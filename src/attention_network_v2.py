"""
Multi-Head Attention-Augmented DQN Network for Explainable RL in Ms-Pacman.

Design notes (vs. the v1 architecture):
  * Per-head learnable gate, initialised near 0 (sigmoid(-3) ~= 0.05). A head that
    is uninformative at the start of training is effectively a no-op, so the
    network can fall back to the plain CNN feature. This avoids the "blind
    attention at step 0" failure mode that the old sigmoid-in-[0,1] design had.
  * Residual modulation: out = base * (1 + g * tanh(conv(base))) instead of
    out = base * sigmoid(conv(base)). With the old form, an attention value
    of 0.1 still suppressed the base feature to 10% of its strength, so early
    in training the explainable network was effectively blind.
  * A second global gate on the combined attention map, also init near 0, so
    the combined block is also a near-identity at the start.
  * Auxiliary regularization loss (`last_reg_loss`):
        - per-head activity penalty (encourage non-trivial |modulation|)
        - diversity penalty across heads (penalise pairwise cosine sim > 0.5)
    This loss is read by `ExplainableDQN` in train.py and added to the DQN
    loss with a small weight so the attention heads have to *do* something
    different from each other.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np


# Initial logit for a gate whose sigmoid should be near 0.05 at the start.
# Anything <= -2 is fine; we pick -3 so the gate is a clear no-op.
_GATE_INIT_LOGIT = -3.0


class AttentionHead(nn.Module):
    """One attention head with a learnable per-head gate and residual modulation."""

    def __init__(self, in_channels: int, hidden_channels: int = 32):
        super().__init__()
        self.attention_conv = nn.Sequential(
            nn.Conv2d(in_channels, hidden_channels, kernel_size=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden_channels, 1, kernel_size=1),
        )
        # gate_logit is a single parameter; sigmoid(gate_logit) is the gate.
        self.gate_logit = nn.Parameter(torch.tensor(_GATE_INIT_LOGIT))

    @property
    def gate(self) -> torch.Tensor:
        return torch.sigmoid(self.gate_logit)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # raw modulation in [-1, 1]
        raw = torch.tanh(self.attention_conv(x))
        mod = self.gate * raw  # in [-gate, gate]
        # residual: keep base, modulate around it
        attended = x * (1.0 + mod)
        return mod, attended


class MultiHeadAttentionExtractor(nn.Module):
    """Multi-head attention extractor with residual gating and a reg loss."""

    def __init__(self, in_channels: int = 4, num_heads: int = 3, hidden_channels: int = 32):
        super().__init__()
        self.num_heads = num_heads
        self.in_channels = in_channels

        # Nature-DQN backbone. Same as the rest of the project, so the
        # baseline and explainable agents share an identical feature
        # extractor up to the attention block.
        self.backbone = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=8, stride=4),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, stride=1),
            nn.ReLU(inplace=True),
        )

        self.attention_heads = nn.ModuleList([
            AttentionHead(64, hidden_channels) for _ in range(num_heads)
        ])

        # 1x1 conv to combine the per-head modulations into one map in [-1, 1].
        # We initialise it to a uniform average so it behaves like a mean at
        # the start, and the network can later learn to weight heads
        # differently if that helps.
        self.aggregator = nn.Conv2d(num_heads, 1, kernel_size=1, bias=False)
        nn.init.constant_(self.aggregator.weight, 1.0 / num_heads)

        # Global gate on the combined block, also init near 0.
        self.global_gate_logit = nn.Parameter(torch.tensor(_GATE_INIT_LOGIT))

        # Caches populated on every forward() for the regularizer and the
        # visualisers. We keep them on the module so a subclass of DQN can
        # read `last_reg_loss` without touching the policy internals.
        self.last_modulations: Optional[List[torch.Tensor]] = None
        self.last_combined_modulation: Optional[torch.Tensor] = None
        self.last_gates: Optional[List[torch.Tensor]] = None
        self.last_global_gate: Optional[torch.Tensor] = None
        self.last_reg_loss: Optional[torch.Tensor] = None

    @property
    def global_gate(self) -> torch.Tensor:
        return torch.sigmoid(self.global_gate_logit)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        base_features = self.backbone(x)

        per_head_mods: List[torch.Tensor] = []
        gates: List[torch.Tensor] = []
        for head in self.attention_heads:
            mod, _ = head(base_features)
            per_head_mods.append(mod)
            gates.append(head.gate)

        # Stack per-head modulations and combine. Tanh keeps the output in
        # [-1, 1] regardless of how the aggregator weights shift during
        # training, which keeps the residual multiplication well-behaved.
        stacked = torch.cat(per_head_mods, dim=1)            # (B, H, 7, 7)
        combined = torch.tanh(self.aggregator(stacked))      # (B, 1, 7, 7)
        g_global = self.global_gate()
        combined_features = base_features * (1.0 + g_global * combined)

        reg_loss = self._compute_regularization(per_head_mods)

        # Detach the cached visualisations so they don't bloat the graph.
        self.last_modulations = [m.detach() for m in per_head_mods]
        self.last_combined_modulation = combined.detach()
        self.last_gates = [g.detach() for g in gates]
        self.last_global_gate = g_global.detach()
        self.last_reg_loss = reg_loss

        attention_data = {
            "individual_maps": self.last_modulations,
            "combined_map": self.last_combined_modulation,
            "gates": self.last_gates,
            "global_gate": self.last_global_gate,
            "attention_entropy": self._compute_entropy(per_head_mods),
        }
        return combined_features, attention_data

    # ------------------------------------------------------------------ loss

    def _compute_regularization(self, per_head_mods: List[torch.Tensor]) -> torch.Tensor:
        """
        Auxiliary loss. Two terms:
          1. Activity: each head's |modulation| should have a non-trivial mean.
             We pull it towards 0.3 with MSE so a head cannot be all-zero.
          2. Diversity: penalise pairwise cosine similarity > 0.5 between
             flattened per-head modulations, so heads must disagree.
        """
        target = torch.tensor(0.3, device=per_head_mods[0].device)
        activity = sum(F.mse_loss(m.abs().mean(), target) for m in per_head_mods)

        diversity = per_head_mods[0].new_zeros(())
        if len(per_head_mods) > 1:
            flat = [m.flatten(start_dim=1) for m in per_head_mods]
            for i in range(len(flat)):
                for j in range(i + 1, len(flat)):
                    cos = F.cosine_similarity(flat[i], flat[j], dim=1).mean()
                    diversity = diversity + F.relu(cos - 0.5)

        return activity + diversity

    def _compute_entropy(self, per_head_mods: List[torch.Tensor]) -> torch.Tensor:
        """Spatial entropy (in nats) of the per-head |modulation| maps."""
        stacked = torch.cat([m.abs() for m in per_head_mods], dim=1)  # (B, H, 7, 7)
        norm = stacked / (stacked.sum(dim=(2, 3), keepdim=True) + 1e-8)
        return -(norm * torch.log(norm + 1e-8)).sum(dim=(2, 3)).mean(dim=1)

    # ---------------------------------------------------------- visualisation

    def get_attention_maps(self, head_idx: Optional[int] = None) -> Optional[torch.Tensor]:
        if self.last_modulations is None:
            return None
        if head_idx is not None:
            return self.last_modulations[head_idx]
        return torch.cat(self.last_modulations, dim=1)


class ExplainableDQNNetwork(nn.Module):
    """Full Q-network with dueling heads, used for stand-alone tests."""

    def __init__(
        self,
        observation_space_shape: Tuple[int, int, int] = (4, 84, 84),
        num_actions: int = 9,
        num_attention_heads: int = 3,
        features_dim: int = 512,
    ):
        super().__init__()
        self.observation_space_shape = observation_space_shape
        self.num_actions = num_actions
        self.num_attention_heads = num_attention_heads
        self.features_dim = features_dim

        self.attention_extractor = MultiHeadAttentionExtractor(
            in_channels=observation_space_shape[0],
            num_heads=num_attention_heads,
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


def create_explainable_network(num_actions: int = 9, num_attention_heads: int = 3) -> ExplainableDQNNetwork:
    return ExplainableDQNNetwork(
        observation_space_shape=(4, 84, 84),
        num_actions=num_actions,
        num_attention_heads=num_attention_heads,
        features_dim=512,
    )


if __name__ == "__main__":
    print("Testing ExplainableDQNNetwork (v2)...")
    net = create_explainable_network()
    print(f"Network: {net}")
    x = torch.randn(4, 4, 84, 84)
    q = net(x)
    print(f"Q-values shape: {q.shape}")
    print(f"Combined attention shape: {net.attention_extractor.last_combined_modulation.shape}")
    print(f"Per-head gates: {[g.item() for g in net.attention_extractor.last_gates]}")
    print(f"Global gate: {net.attention_extractor.last_global_gate.item():.4f}")
    print(f"Reg loss: {net.attention_extractor.last_reg_loss.item():.4f}")
    print("? Network test complete!")
