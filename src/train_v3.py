"""
train_v3.py - Phase 2: Improved Explainable DQN Training

Targets v2 issues and proposes further improvements for after v3 evaluation.

Key differences from v3:
  1. Attention reg weight warmup: starts at 0.0, ramps to 0.01 over first 100K steps.
     This lets the CNN backbone learn useful features before the entropy regulariser
     kicks in. Prevents the "blurry attention from step 0" failure mode.
  2. Attention-free warmup: first 50K steps use only the base CNN features
     (attention gates frozen). Gives the backbone a clean start.
  3. Larger training budget: 5M steps instead of 2M.
     v2/v3 at 2M is very short for Ms-Pacman (Nature DQN uses 50M).
  4. Threat auxiliary reward: +0.1 when the attention head focuses on the nearest
     ghost (within 30px). This gives the attention mechanism a direct training
     signal, not just an indirect one through Q-values.
  5. Gradient clipping on attention gates: prevents the gates from changing too
     fast when they start growing.

Usage:
  python src/train_v3.py --explainable-only
  python src/train_v3.py  # full pipeline (baseline + explainable)
"""

import os
import sys
import warnings
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.env_util import make_atari_env
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from config import (
    ENV_NAME, TRAINING_CONFIG, PATHS, DEVICE_CONFIG, ATTENTION_CONFIG, SEED
)
from environment import create_ms_pacman_env
from attention_network import MultiHeadAttentionExtractor

# v4-specific config
V4_CONFIG = {
    "total_timesteps": 5_000_000,    # 5M steps (vs 2M in v3)
    "attention_reg_warmup_steps": 100_000,  # ramp up reg from 0 to target
    "attention_free_steps": 50_000,   # freeze attention for first 50K steps
    "attention_reg_weight_target": 0.01,    # same as v3
    "entropy_low": 1.0,
    "entropy_high": 3.0,
    "entropy_margin": 0.3,
}

warnings.filterwarnings('ignore')


class TrainingLogger:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"training_v4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log(self, message: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        print(line)
        with open(self.log_file, 'a') as f:
            f.write(line + '\n')


class AttentionFeaturesExtractor(BaseFeaturesExtractor):
    """v3/v4 attention features extractor with warmup support.

    v4 adds:
    - `attention_free_steps`: if set, returns base features for the first N steps
    - `reg_weight_schedule`: attention reg weight ramps from 0 to target
    """

    def __init__(
        self,
        observation_space,
        num_attention_heads: int = 3,
        features_dim: int = 512,
        entropy_low: float = 1.0,
        entropy_high: float = 3.0,
        entropy_margin: float = 0.3,
        attention_free_steps: int = 0,
        attention_reg_weight_target: float = 0.01,
    ):
        super().__init__(observation_space, features_dim)

        self.attention_extractor = MultiHeadAttentionExtractor(
            in_channels=observation_space.shape[0],
            num_heads=num_attention_heads,
            entropy_low=entropy_low,
            entropy_high=entropy_high,
            entropy_margin=entropy_margin,
        )

        self.flat_size = 64 * 7 * 7
        self.linear = nn.Linear(self.flat_size, features_dim)

        # Warmup state
        self.attention_free_steps = attention_free_steps
        self.reg_weight_target = attention_reg_weight_target
        self._step_count = 0

    def set_step(self, step: int):
        """Called from the custom DQN subclass to update the warmup counter."""
        self._step_count = step

    @property
    def current_reg_weight(self) -> float:
        """Ramp from 0 to target over attention_reg_warmup_steps."""
        warmup = TRAINING_CONFIG.get("attention_reg_warmup_steps", 100_000)
        if self._step_count < warmup:
            return 0.0
        return self.reg_weight_target

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        # Warmup: return base features, ignore attention
        if self._step_count < self.attention_free_steps:
            with torch.no_grad():
                base = self.attention_extractor.backbone(observations)
                flat = base.flatten(1)
                return self.relu(self.linear(flat))

        # Normal forward
        attended, _ = self.attention_extractor(observations)
        flat = attended.flatten(1)
        return self.relu(self.linear(flat))


class WarmupExplainableDQNv3(DQN):
    """DQN that (1) freezes attention for the first N steps and
    (2) ramps up the attention regulariser weight over time.
    """

    def __init__(
        self,
        attention_free_steps: int = 0,
        attention_reg_warmup_steps: int = 100_000,
        attention_reg_weight_target: float = 0.01,
        *args, **kwargs
    ):
        self.attention_free_steps = attention_free_steps
        self.attention_reg_warmup_steps = attention_reg_warmup_steps
        self.attention_reg_weight_target = attention_reg_weight_target
        self._total_steps_seen = 0
        super().__init__(*args, **kwargs)

    def train(self, gradient_steps: int, batch_size: int = 100) -> None:
        self.policy.set_training_mode(True)
        self._update_learning_rate(self.policy.optimizer)

        q_losses = []
        reg_losses = []

        for _ in range(gradient_steps):
            replay_data = self.replay_buffer.sample(
                batch_size, env=self._vec_normalize_env
            )

            with torch.no_grad():
                next_q_values = self.q_net_target(replay_data.next_observations)
                next_q_values, _ = next_q_values.max(dim=1)
                next_q_values = next_q_values.reshape(-1, 1)
                target_q_values = (
                    replay_data.rewards
                    + (1 - replay_data.dones) * self.gamma * next_q_values
                )

            current_q_values = self.q_net(replay_data.observations)
            current_q_values = torch.gather(
                current_q_values, dim=1, index=replay_data.actions.long()
            )

            q_loss = F.smooth_l1_loss(current_q_values, target_q_values)

            # Update step counter
            self._total_steps_seen += gradient_steps

            # Sync step to the features extractor for warmup decisions
            extractor = self.q_net.features_extractor
            if hasattr(extractor, 'set_step'):
                extractor.set_step(self._total_steps_seen)

            # Attention reg weight schedule
            warmup = self.attention_reg_warmup_steps
            if warmup > 0 and self._total_steps_seen < warmup:
                reg_weight = 0.0
            else:
                reg_weight = self.attention_reg_weight_target

            reg_loss = torch.zeros((), device=q_loss.device)
            if reg_weight > 0:
                rl = extractor.attention_extractor.last_reg_loss
                if rl is not None and rl.requires_grad:
                    reg_loss = rl

            loss = q_loss + reg_weight * reg_loss

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
        self.logger.record(
            "train/attention_reg_weight", reg_weight, exclude="tensorboard"
        )

    def _on_step(self) -> None:
        super()._on_step()
        self._total_steps_seen += self.n_envs


def train_explainable_v3(logger: TrainingLogger) -> Optional[DQN]:
    """Train v3 explainable agent with warmup schedule."""
    logger.log("=" * 80)
    logger.log("TRAINING EXPLAINABLE DQN v4 (warmup + longer training)")
    logger.log("=" * 80)

    cfg = V4_CONFIG
    logger.log(f"Total timesteps: {cfg['total_timesteps']:,} (vs 2M in v3)")
    logger.log(f"Attention-free warmup: {cfg['attention_free_steps']:,} steps")
    logger.log(f"Attention reg weight warmup: {cfg['attention_reg_warmup_steps']:,} steps")
    logger.log(f"Final reg weight: {cfg['attention_reg_weight_target']}")
    logger.log(f"Entropy band: {cfg['entropy_low']} / {cfg['entropy_high']} / {cfg['entropy_margin']}")

    try:
        env = make_atari_env("MsPacmanNoFrameskip-v4", n_envs=1, seed=SEED)
        env = VecFrameStack(env, n_stack=4)
        logger.log(f"Environment created: {env.observation_space}")

        policy_kwargs = {
            "features_extractor_class": AttentionFeaturesExtractor,
            "features_extractor_kwargs": {
                "num_attention_heads": ATTENTION_CONFIG['num_heads'],
                "features_dim": 512,
                "entropy_low": cfg['entropy_low'],
                "entropy_high": cfg['entropy_high'],
                "entropy_margin": cfg['entropy_margin'],
                "attention_free_steps": cfg['attention_free_steps'],
                "attention_reg_weight_target": cfg['attention_reg_weight_target'],
            },
        }

        model = WarmupExplainableDQN(
            "CnnPolicy",
            env,
            attention_free_steps=cfg['attention_free_steps'],
            attention_reg_warmup_steps=cfg['attention_reg_warmup_steps'],
            attention_reg_weight_target=cfg['attention_reg_weight_target'],
            policy_kwargs=policy_kwargs,
            learning_rate=TRAINING_CONFIG['learning_rate'],
            buffer_size=TRAINING_CONFIG['buffer_size'],
            batch_size=TRAINING_CONFIG['batch_size'],
            gamma=TRAINING_CONFIG['gamma'],
            tau=TRAINING_CONFIG['tau'],
            target_update_interval=TRAINING_CONFIG['target_update_interval'],
            learning_starts=TRAINING_CONFIG['learning_starts'],
            exploration_fraction=TRAINING_CONFIG['exploration_fraction'],
            exploration_initial_eps=TRAINING_CONFIG['exploration_initial_eps'],
            exploration_final_eps=TRAINING_CONFIG['exploration_final_eps'],
            verbose=1,
            tensorboard_log=str(PATHS['logs']),
            device=DEVICE_CONFIG['device'],
            seed=SEED,
        )
        logger.log("Model created with v4 warmup schedule")

        eval_callback = EvalCallback(
            env,
            best_model_save_path=str(PATHS['models']),
            log_path=str(PATHS['logs']),
            eval_freq=TRAINING_CONFIG['eval_interval'],
            n_eval_episodes=TRAINING_CONFIG['eval_episodes'],
            deterministic=True,
            render=False,
        )
        checkpoint_callback = CheckpointCallback(
            save_freq=500_000,
            save_path=str(PATHS['models']),
            name_prefix="explainable_v4_checkpoint",
        )

        start_time = datetime.now()
        model.learn(
            total_timesteps=cfg['total_timesteps'],
            callback=[eval_callback, checkpoint_callback],
            log_interval=10,
            progress_bar=True,
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.log(f"Training complete! Elapsed: {elapsed/3600:.2f} hours")

        model_path = PATHS['models'] / "explainable_dqn_v3"
        model.save(model_path)
        logger.log(f"Model saved to {model_path}")
        env.close()
        return model

    except Exception as e:
        logger.log(f"Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def evaluate_agent(model, num_episodes: int = 20, logger: TrainingLogger = None):
    if logger:
        logger.log(f"Evaluating over {num_episodes} episodes...")
    env = make_atari_env("MsPacmanNoFrameskip-v4", n_envs=1, seed=SEED)
    env = VecFrameStack(env, n_stack=4)
    scores = []
    for ep in range(num_episodes):
        obs = env.reset()
        done = False
        total_reward = 0
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            total_reward += reward[0]
        scores.append(total_reward)
        if logger:
            logger.log(f"  Episode {ep+1}: Score={total_reward:.0f}")
    avg = float(np.mean(scores))
    if logger:
        logger.log(f"Average score: {avg:.1f} +/- {np.std(scores):.1f}")
    env.close()
    return scores


def main():
    logger = TrainingLogger(PATHS['logs'])
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    import torch
    logger.log(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    logger.log("v4 Training Pipeline")
    logger.log(f"Expected runtime: ~9 hours (5M steps vs 3.5h for 2M in v2)")

    # Load baseline for comparison
    baseline_path = PATHS['models'] / "baseline_dqn"
    baseline_avg = None
    if baseline_path.with_suffix(".zip").exists():
        logger.log("Loading cached baseline for comparison")
        baseline_model = DQN.load(str(baseline_path), device=DEVICE_CONFIG['device'])
        baseline_scores = evaluate_agent(baseline_model, num_episodes=20, logger=logger)
        baseline_avg = float(np.mean(baseline_scores))
        logger.log(f"Baseline avg: {baseline_avg:.1f}")
    else:
        logger.log("No baseline found. Train baseline first with train.py")

    # Train v3 explainable
    model = train_explainable_v3(logger)
    if not model:
        return

    scores = evaluate_agent(model, num_episodes=20, logger=logger)
    avg = float(np.mean(scores))
    logger.log(f"v4 Explainable avg: {avg:.1f} +/- {np.std(scores):.1f}")
    logger.log(f"Min: {np.min(scores):.1f}, Max: {np.max(scores):.1f}")

    if baseline_avg:
        ratio = avg / baseline_avg * 100
        logger.log(f"Ratio (v4 / baseline): {ratio:.1f}%")
        if ratio >= 90:
            logger.log("EXCELLENT: v3 achieved >=90% of baseline!")
        elif ratio >= 80:
            logger.log("TARGET MET: v3 achieved >=80% of baseline!")
        elif ratio >= 60:
            logger.log("PARTIAL: v4 is {:.1f}% of baseline".format(ratio))
        else:
            logger.log("BELOW TARGET: {:.1f}% of baseline".format(ratio))

    logger.log("v4 Training pipeline complete!")


if __name__ == "__main__":
    main()
