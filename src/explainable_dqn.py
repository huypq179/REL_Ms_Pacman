"""
Custom DQN subclass that wires the attention regulariser from
``MultiHeadAttentionExtractor.last_reg_loss`` into the Q-learning loss.

Why subclass DQN instead of DQNPolicy:
    SB3's ``DQNPolicy`` does *not* define a ``loss()`` method; the Q-learning
    loss is computed inline in ``DQN.train()``.  Subclassing ``DQN`` and
    overriding ``train()`` is the smallest change that lets us add a second
    loss term without monkey-patching stable_baselines3.

Forward path:
    * ``self.q_net(replay_data.observations)`` populates
      ``self.q_net.features_extractor.attention_extractor.last_reg_loss``
      (a tensor with ``requires_grad=True``).
    * We add ``attention_reg_weight * reg_loss`` to the Huber loss.
    * The target network's forward pass under ``torch.no_grad()`` does not
      contribute gradients, so we only read from the *online* network's
      extractor.

Logging:
    * ``train/loss`` keeps the standard Q-learning loss (TensorBoard).
    * ``train/reg_loss`` records the raw attention regulariser for inspection.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type, Union

import numpy as np
import torch
import torch.nn.functional as F
from gymnasium import spaces

from stable_baselines3 import DQN
from stable_baselines3.common.type_aliases import GymEnv, Schedule


class ExplainableDQN(DQN):
    """DQN with attention-entropy regulariser added to the Q-learning loss.

    Args:
        attention_reg_weight: Coefficient on the attention regulariser.
            0.005-0.05 is a good range; smaller means the regulariser nudges
            the entropy distribution without overwhelming the Q objective.
    """

    def __init__(
        self,
        policy: Union[str, Type],
        env: Union[GymEnv, str],
        attention_reg_weight: float = 0.01,
        *args: Any,
        **kwargs: Any,
    ):
        self.attention_reg_weight = float(attention_reg_weight)
        super().__init__(policy, env, *args, **kwargs)

    def train(self, gradient_steps: int, batch_size: int = 100) -> None:
        """Identical to ``DQN.train`` but adds the attention regulariser.

        We re-implement (rather than calling super and then patching) so
        that the reg-loss gradient flows through the SAME
        ``loss.backward()`` call as the Q-loss, ensuring a single optimiser
        step updates both objectives.
        """
        self.policy.set_training_mode(True)
        self._update_learning_rate(self.policy.optimizer)

        q_losses = []
        reg_losses = []

        for _ in range(gradient_steps):
            replay_data = self.replay_buffer.sample(
                batch_size, env=self._vec_normalize_env  # type: ignore[arg-type]
            )

            with torch.no_grad():
                next_q_values = self.q_net_target(replay_data.next_observations)
                next_q_values, _ = next_q_values.max(dim=1)
                next_q_values = next_q_values.reshape(-1, 1)
                target_q_values = (
                    replay_data.rewards
                    + (1 - replay_data.dones) * self.gamma * next_q_values
                )

            # Forward pass on the online network.  This populates
            # ``last_reg_loss`` on the attention extractor.
            current_q_values = self.q_net(replay_data.observations)
            current_q_values = torch.gather(
                current_q_values, dim=1, index=replay_data.actions.long()
            )

            q_loss = F.smooth_l1_loss(current_q_values, target_q_values)

            reg_loss = self.q_net.features_extractor.attention_extractor.last_reg_loss
            if reg_loss is None or not reg_loss.requires_grad:
                reg_loss = torch.zeros((), device=q_loss.device)

            loss = q_loss + self.attention_reg_weight * reg_loss

            q_losses.append(q_loss.item())
            reg_losses.append(float(reg_loss.detach().cpu()))

            self.policy.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
            self.policy.optimizer.step()

        self._n_updates += gradient_steps
        self.logger.record("train/n_updates", self._n_updates, exclude="tensorboard")
        self.logger.record("train/loss", float(np.mean(q_losses)))
        self.logger.record("train/reg_loss", float(np.mean(reg_losses)))


__all__ = ["ExplainableDQN"]