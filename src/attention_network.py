"""
Multi-Head Attention-Augmented DQN Network for Explainable RL in Ms-Pacman.

v2 architecture (vs. v1 multiplicative residual + activity/diversity reg):

  1. Real multiplicative gating per head:
         combined = base + alpha_h * (base * attention_h)
     where alpha_h = sigmoid(alpha_h_logit) is a *single scalar parameter per
     head*, initialised near 0 (sigmoid(-3) ~= 0.05).  When alpha_h -> 0
     the head is exactly identity; as alpha_h grows during training, the
     attention map starts modulating the base.  The old "(combined + 1) / 2"
     averaging trick is gone.

  2. Global additive residual block:
         combined = combined + beta * proj(base)
     where proj is a 1x1 conv initialised to zero and beta is another
     sigmoid-gated scalar (init near 0).  Even if *every* alpha_h stays at
     0, this gives the network a separate additive path that can still
     learn useful features without being constrained to "look like base".

  3. Entropy regularisation per head:
     For each head we measure the spatial entropy H of |attention| over the
     7x7 feature map.  H ranges in [0, log(49) ~ 3.89].  We push every
     head's H toward one of two regimes:
         - focused: H <= entropy_low (concentrated on a few cells)
         - dispersed: H >= entropy_high (spread over the field)
     Anything in the middle band (entropy_low + margin, entropy_high - margin)
     is penalised.  This makes attention *clearly* focused or *clearly*
     dispersed -- never a vague blur in the middle.

  4. The combined regularisation loss lives on
     `MultiHeadAttentionExtractor.last_reg_loss`.  It is a *real* tensor with
     `requires_grad=True` so the SB3 DQN policy in
     `explainable_dqn_policy.py` can add it to the Q-learning loss.
"""

from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np


# sigmoid(-3) ~= 0.047.  This is small enough that, at step 0, every gated
# path is effectively a no-op.  Training is free to grow them as needed.
_GATE_INIT_LOGIT = -3.0


class AttentionHead(nn.Module):
    """One attention head with a learnable multiplicative gate (alpha).

    The output is `base + alpha * (base * attention)` where `attention` is a
    spatial sigmoid map in [0, 1] computed from `base`.  When alpha is small,
    the output is approximately base; when alpha grows, attention modulates
    the base multiplicatively.
    """

    def __init__(self, in_channels: int, hidden_channels: int = 32):
        super().__init__()
        self.attention_conv = nn.Sequential(
            nn.Conv2d(in_channels, hidden_channels, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_channels, 1, kernel_size=1),
        )
        # alpha is sigmoid(alpha_logit); init near 0.
        self.alpha_logit = nn.Parameter(torch.tensor(_GATE_INIT_LOGIT))

    @property
    def alpha(self) -> torch.Tensor:
        return torch.sigmoid(self.alpha_logit)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        attn_logits = self.attention_conv(x)
        attn = torch.sigmoid(attn_logits)  # (B, 1, H, W) in [0, 1]
        # Real gating: combined = base + alpha * (base * attention)
        gated = x + self.alpha * x * attn
        return attn, gated


class MultiHeadAttentionExtractor(nn.Module):
    """Multi-head attention extractor with real gating, residual path, and entropy reg.

    Forward path:
        base = backbone(obs)
        combined = base
        for head in heads:
            attn, _ = head(base)              # attention computed from base
            combined = combined + head.alpha * combined * attn
        combined = combined + residual_gate * residual_proj(base)

    The combined result is `combined_features`, returned alongside an
    `attention_data` dict for visualisation and logging.
    """

    def __init__(
        self,
        in_channels: int = 4,
        num_heads: int = 3,
        hidden_channels: int = 32,
        entropy_low: float = 1.0,
        entropy_high: float = 3.0,
        entropy_margin: float = 0.3,
    ):
        super().__init__()
        self.num_heads = num_heads
        self.in_channels = in_channels

        # Nature-DQN backbone.  Identical to baseline so apples-to-apples.
        self.backbone = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=8, stride=4),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(inplace=True),
        )

        # Per-head attention with learnable alpha (multiplicative gating).
        self.attention_heads = nn.ModuleList([
            AttentionHead(64, hidden_channels) for _ in range(num_heads)
        ])

        # Global additive residual block: 1x1 conv, init zero so it starts
        # as identity.  Gated by `residual_gate` (init near 0).
        self.residual_proj = nn.Conv2d(64, 64, kernel_size=1, bias=False)
        nn.init.zeros_(self.residual_proj.weight)
        self.residual_gate_logit = nn.Parameter(torch.tensor(_GATE_INIT_LOGIT))

        # Entropy reg targets (registered as buffers so they move with .to(device)).
        self.register_buffer("entropy_low_buf", torch.tensor(entropy_low))
        self.register_buffer("entropy_high_buf", torch.tensor(entropy_high))
        self.entropy_margin = float(entropy_margin)

        # Caches populated on every forward().
        self.last_attns: Optional[List[torch.Tensor]] = None
        self.last_alphas: Optional[List[torch.Tensor]] = None
        self.last_residual_gate: Optional[torch.Tensor] = None
        self.last_combined_features: Optional[torch.Tensor] = None
        self.last_entropy: Optional[torch.Tensor] = None
        self.last_reg_loss: Optional[torch.Tensor] = None

    # --------------------------------------------------------------- helpers

    @property
    def residual_gate(self) -> torch.Tensor:
        return torch.sigmoid(self.residual_gate_logit)

    def _compute_entropy(self, per_head_attns: List[torch.Tensor]) -> torch.Tensor:
        """Spatial Shannon entropy per head, in nats.

        Args:
            per_head_attns: list of (B, 1, H, W) attention maps in [0, 1].
        Returns:
            (num_heads,) tensor of per-head mean entropy.
        """
        entropies = []
        for attn in per_head_attns:
            # Normalise to a probability distribution per sample.
            p = attn / (attn.sum(dim=(2, 3), keepdim=True) + 1e-8)
            ent = -(p * torch.log(p + 1e-8)).sum(dim=(2, 3))  # (B, 1)
            # .mean() over every dim gives a 0-d scalar tensor, which
            # torch.stack turns into a clean (num_heads,) vector.
            entropies.append(ent.mean())
        return torch.stack(entropies)                         # (num_heads,)

    def _compute_entropy_reg(self, entropies: torch.Tensor) -> torch.Tensor:
        """Push every head's entropy into either the focused or dispersed band.

        For each head, the "middle band" is
            (entropy_low + margin, entropy_high - margin).
        If a head's entropy sits in that band, the gap to the nearer edge is
        penalised.  Heads already in one of the two extreme bands pay nothing.
        """
        margin = self.entropy_margin
        low = self.entropy_low_buf
        high = self.entropy_high_buf
        # H <= low + margin  -> focused, OK
        # H >= high - margin -> dispersed, OK
        # Else penalise the smaller of the two gaps.
        low_violation = F.relu(entropies - (low + margin))
        high_violation = F.relu((high - margin) - entropies)
        gap = torch.minimum(low_violation, high_violation)
        return gap.sum()

    # --------------------------------------------------------------- forward

    def forward(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        base_features = self.backbone(x)

        # Step 1: per-head multiplicative gating.
        # combined = base + alpha_h * (base * attn_h)  for each head.
        combined = base_features
        per_head_attns: List[torch.Tensor] = []
        alphas: List[torch.Tensor] = []
        for head in self.attention_heads:
            # Compute attention on base (not on running combined) so each head
            # sees the same input and stays interpretable.
            attn, _ = head(base_features)
            combined = combined + head.alpha * combined * attn
            per_head_attns.append(attn)
            alphas.append(head.alpha)

        # Step 2: additive residual safety net.
        # combined = combined + residual_gate * residual_proj(base)
        # At init residual_gate ~= 0 and residual_proj is zero, so this is
        # effectively a no-op.  It can grow independently of the per-head
        # alphas if the network wants an unconstrained additive path.
        residual = self.residual_proj(base_features)
        combined = combined + self.residual_gate * residual

        # Step 3: entropy regularisation.
        entropies = self._compute_entropy(per_head_attns)
        reg_loss = self._compute_entropy_reg(entropies)

        # Detach everything we expose to visualisation; reg_loss keeps grad.
        self.last_attns = [m.detach() for m in per_head_attns]
        self.last_alphas = [a.detach() for a in alphas]
        self.last_residual_gate = self.residual_gate.detach()
        self.last_combined_features = combined.detach()
        self.last_entropy = entropies.detach()
        self.last_reg_loss = reg_loss

        attention_data = {
            "individual_maps": self.last_attns,
            "alphas": self.last_alphas,
            "residual_gate": self.last_residual_gate,
            "attention_entropy": self.last_entropy,
        }
        return combined, attention_data

    # ---------------------------------------------------------- visualisation

    def get_attention_maps(self, head_idx: Optional[int] = None) -> Optional[torch.Tensor]:
        if self.last_attns is None:
            return None
        if head_idx is not None:
            return self.last_attns[head_idx]
        return torch.cat(self.last_attns, dim=1)


class ExplainableDQNNetwork(nn.Module):
    """Full Q-network with dueling heads, used for stand-alone tests."""

    def __init__(
        self,
        observation_space_shape: Tuple[int, int, int] = (4, 84, 84),
        num_actions: int = 9,
        num_attention_heads: int = 3,
        features_dim: int = 512,
        entropy_low: float = 1.0,
        entropy_high: float = 3.0,
        entropy_margin: float = 0.3,
    ):
        super().__init__()
        self.observation_space_shape = observation_space_shape
        self.num_actions = num_actions
        self.num_attention_heads = num_attention_heads
        self.features_dim = features_dim

        self.attention_extractor = MultiHeadAttentionExtractor(
            in_channels=observation_space_shape[0],
            num_heads=num_attention_heads,
            entropy_low=entropy_low,
            entropy_high=entropy_high,
            entropy_margin=entropy_margin,
        )
        self.flat_size = 64 * 7 * 7
        self.fc = nn.Sequential(nn.Linear(self.flat_size, features_dim), nn.ReLU())
        self.value_head = nn.Sequential(nn.Linear(features_dim, 256), nn.ReLU(), nn.Linear(256, 1))
        self.advantage_head = nn.Sequential(
            nn.Linear(features_dim, 256), nn.ReLU(), nn.Linear(256, num_actions)
        )

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        features, attention_data = self.attention_extractor(obs)
        flat = features.flatten(start_dim=1)
        f = self.fc(flat)
        values = self.value_head(f)
        advantages = self.advantage_head(f)
        q_values = values + advantages - advantages.mean(dim=1, keepdim=True)
        self.last_attention_data = attention_data
        return q_values

    def get_explanations(self) -> Dict[str, torch.Tensor]:
        return getattr(self, "last_attention_data", {})

    def get_attention_numpy(self, head_idx: Optional[int] = None) -> Optional[np.ndarray]:
        maps = self.attention_extractor.get_attention_maps(head_idx)
        if maps is not None:
            return maps.detach().cpu().numpy()
        return None


def create_explainable_network(
    num_actions: int = 9,
    num_attention_heads: int = 3,
    entropy_low: float = 1.0,
    entropy_high: float = 3.0,
    entropy_margin: float = 0.3,
) -> ExplainableDQNNetwork:
    return ExplainableDQNNetwork(
        observation_space_shape=(4, 84, 84),
        num_actions=num_actions,
        num_attention_heads=num_attention_heads,
        features_dim=512,
        entropy_low=entropy_low,
        entropy_high=entropy_high,
        entropy_margin=entropy_margin,
    )


if __name__ == "__main__":
    print("Testing ExplainableDQNNetwork (v2)...")
    net = create_explainable_network()
    print(f"Network: {net}")
    x = torch.randn(4, 4, 84, 84)
    q = net(x)
    print(f"Q-values shape: {q.shape}")
    print(f"Per-head alphas: {[a.item() for a in net.attention_extractor.last_alphas]}")
    print(f"Residual gate: {net.attention_extractor.last_residual_gate.item():.4f}")
    print(f"Per-head entropy: {net.attention_extractor.last_entropy.tolist()}")
    print(f"Reg loss (raw): {net.attention_extractor.last_reg_loss.item():.4f}")
    print("? Network test complete!")