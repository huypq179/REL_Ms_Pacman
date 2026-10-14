"""
Training Script for Baseline and Explainable DQN
Optimized for RTX 3050 4GB
"""

import os
import warnings
import numpy as np
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
import gymnasium as gym
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback
from stable_baselines3.common.env_util import make_atari_env
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

from config import (
    ENV_NAME, TRAINING_CONFIG, PATHS, DEVICE_CONFIG, ATTENTION_CONFIG,
    SEED, FRAME_SKIP
)
from environment import create_ms_pacman_env
from attention_network import MultiHeadAttentionExtractor
from explainable_dqn import ExplainableDQN

warnings.filterwarnings('ignore')


class TrainingLogger:
    """Simple training logger."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, 'a') as f:
            f.write(log_message + '\n')


class AttentionFeaturesExtractor(BaseFeaturesExtractor):
    """
    Custom features extractor for SB3 DQN using multi-head attention.
    Wraps MultiHeadAttentionExtractor to work with SB3's feature extractor API.

    v2: real multiplicative gating + additive residual + entropy regulariser.
    """

    def __init__(
        self,
        observation_space,
        num_attention_heads: int = 3,
        features_dim: int = 512,
        entropy_low: float = 1.0,
        entropy_high: float = 3.0,
        entropy_margin: float = 0.3,
    ):
        super().__init__(observation_space, features_dim)

        self.attention_extractor = MultiHeadAttentionExtractor(
            in_channels=observation_space.shape[0],
            num_heads=num_attention_heads,
            entropy_low=entropy_low,
            entropy_high=entropy_high,
            entropy_margin=entropy_margin,
        )

        # Calculate flattened size after CNN + attention
        # Input: (batch, 4, 84, 84)
        # After CNN: (batch, 64, 7, 7) = 3136
        self.flat_size = 64 * 7 * 7

        # Linear layer to project to features_dim
        self.linear = nn.Linear(self.flat_size, features_dim)
        self.relu = nn.ReLU()

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        """
        Extract features from observations using attention mechanism.

        Args:
            observations: (batch, 4, 84, 84)

        Returns:
            features: (batch, features_dim)

        Side effect:
            ``attention_extractor.last_reg_loss`` is populated with a tensor
            that has ``requires_grad=True``.  ``ExplainableDQN.train`` reads
            it and adds ``attention_reg_weight * reg_loss`` to the Q-loss.
        """
        # Apply attention extractor (backbone + per-head gating + residual).
        attended_features, _ = self.attention_extractor(observations)

        # Flatten
        flat_features = attended_features.reshape(attended_features.shape[0], -1)

        # Project to features_dim
        features = self.linear(flat_features)
        features = self.relu(features)

        return features


def train_baseline_agent(logger: TrainingLogger):
    """Train baseline DQN agent."""
    
    logger.log("=" * 80)
    logger.log("TRAINING BASELINE DQN AGENT")
    logger.log("=" * 80)
    
    logger.log(f"Environment: {ENV_NAME}")
    logger.log(f"Total timesteps: {TRAINING_CONFIG['total_timesteps']:,}")
    logger.log(f"Buffer size: {TRAINING_CONFIG['buffer_size']:,}")
    logger.log(f"Batch size: {TRAINING_CONFIG['batch_size']}")
    logger.log(f"Learning rate: {TRAINING_CONFIG['learning_rate']}")
    
    try:
        # Create environment
        logger.log("Creating environment...")
        env = make_atari_env(
            "MsPacmanNoFrameskip-v4",
            n_envs=1,
            seed=SEED,
        )
        env = VecFrameStack(env, n_stack=4)
        logger.log(f"? Environment created")
        logger.log(f"  Observation space: {env.observation_space}")
        logger.log(f"  Action space: {env.action_space}")
        
        # Create agent
        logger.log("Creating DQN agent...")
        model = DQN(
            "CnnPolicy",
            env,
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
        logger.log(f"? Agent created")
        
        # Callbacks
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
            name_prefix="baseline_checkpoint",
        )
        
        # Train
        logger.log("Starting training...")
        start_time = datetime.now()
        
        model.learn(
            total_timesteps=TRAINING_CONFIG['total_timesteps'],
            callback=[eval_callback, checkpoint_callback],
            log_interval=10,
            progress_bar=True,
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.log(f"? Training complete! Elapsed: {elapsed/3600:.2f} hours")
        
        # Save
        model_path = PATHS['models'] / "baseline_dqn"
        model.save(model_path)
        logger.log(f"? Model saved to {model_path}")
        
        env.close()
        
        return model
    
    except Exception as e:
        logger.log(f"? Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def train_explainable_agent(logger: TrainingLogger):
    """Train explainable DQN agent with v2 multi-head attention.

    Architecture (see ``attention_network.py``):
      * Real multiplicative gating per head: combined = base + alpha * (base * attn)
      * Global additive residual block: combined += beta * proj(base)
      * Entropy regulariser pushing each head's spatial entropy into the
        focused band (H <= 1.0) or the dispersed band (H >= 3.0).
    The regulariser is added to the Q-learning loss via ExplainableDQN.
    """

    logger.log("=" * 80)
    logger.log("TRAINING EXPLAINABLE DQN AGENT (v2: real gating + residual + entropy reg)")
    logger.log("=" * 80)

    logger.log(f"Environment: {ENV_NAME}")
    logger.log(f"Total timesteps: {TRAINING_CONFIG['total_timesteps']:,}")
    logger.log(f"Attention heads: {ATTENTION_CONFIG['num_heads']}")
    logger.log(f"Head names: {ATTENTION_CONFIG['head_names']}")
    logger.log(f"Buffer size: {TRAINING_CONFIG['buffer_size']:,}")
    logger.log(f"Batch size: {TRAINING_CONFIG['batch_size']}")
    logger.log(f"Learning rate: {TRAINING_CONFIG['learning_rate']}")
    logger.log(f"Entropy reg weight: {TRAINING_CONFIG['attention_reg_weight']}")
    logger.log(f"Entropy low/high/margin: "
               f"{TRAINING_CONFIG['entropy_low']} / {TRAINING_CONFIG['entropy_high']} / "
               f"{TRAINING_CONFIG['entropy_margin']}")

    try:
        # Create environment
        logger.log("Creating environment...")
        env = make_atari_env(
            "MsPacmanNoFrameskip-v4",
            n_envs=1,
            seed=SEED,
        )
        env = VecFrameStack(env, n_stack=4)
        logger.log(f"? Environment created")
        logger.log(f"  Observation space: {env.observation_space}")
        logger.log(f"  Action space: {env.action_space}")

        # Create agent with attention feature extractor
        logger.log("Creating Explainable DQN agent (v2)...")

        policy_kwargs = {
            "features_extractor_class": AttentionFeaturesExtractor,
            "features_extractor_kwargs": {
                "num_attention_heads": ATTENTION_CONFIG['num_heads'],
                "features_dim": 512,
                "entropy_low": TRAINING_CONFIG['entropy_low'],
                "entropy_high": TRAINING_CONFIG['entropy_high'],
                "entropy_margin": TRAINING_CONFIG['entropy_margin'],
            },
        }

        # Use ExplainableDQN so train() adds attention regulariser to Q-loss.
        model = ExplainableDQN(
            "CnnPolicy",
            env,
            attention_reg_weight=TRAINING_CONFIG['attention_reg_weight'],
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
        logger.log(f"? Explainable Agent created with {ATTENTION_CONFIG['num_heads']} attention heads (v2)")

        # Callbacks
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
            name_prefix="explainable_v2_checkpoint",
        )

        # Train
        logger.log("Starting training...")
        start_time = datetime.now()

        model.learn(
            total_timesteps=TRAINING_CONFIG['total_timesteps'],
            callback=[eval_callback, checkpoint_callback],
            log_interval=10,
            progress_bar=True,
        )

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.log(f"? Training complete! Elapsed: {elapsed/3600:.2f} hours")

        # Save
        model_path = PATHS['models'] / "explainable_dqn"
        model.save(model_path)
        logger.log(f"? Model saved to {model_path}")

        env.close()

        return model

    except Exception as e:
        logger.log(f"? Training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def evaluate_agent(model, num_episodes: int = 10, logger: TrainingLogger = None):
    """Evaluate agent performance."""
    
    if logger:
        logger.log(f"\nEvaluating agent over {num_episodes} episodes...")
    
    env = make_atari_env(
        "MsPacmanNoFrameskip-v4",
        n_envs=1,
        seed=SEED,
    )
    env = VecFrameStack(env, n_stack=4)
    
    scores = []
    
    for ep in range(num_episodes):
        obs = env.reset()
        episode_reward = 0
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_reward += reward[0]
        
        scores.append(episode_reward)
        if logger:
            logger.log(f"  Episode {ep+1}: Score={episode_reward:.0f}")
    
    avg_score = np.mean(scores)
    std_score = np.std(scores)
    
    if logger:
        logger.log(f"Average score: {avg_score:.1f} +/- {std_score:.1f}")
    
    env.close()
    
    return scores


def main():
    """Main training pipeline."""
    
    # Setup
    logger = TrainingLogger(PATHS['logs'])
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    
    logger.log("Ms-Pacman Explainable RL - Training Script")
    logger.log(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    
    # Train baseline
    baseline_model = train_baseline_agent(logger)
    
    baseline_scores = None
    if baseline_model:
        # Evaluate baseline
        logger.log("\n" + "=" * 80)
        logger.log("BASELINE EVALUATION")
        logger.log("=" * 80)
        
        baseline_scores = evaluate_agent(baseline_model, num_episodes=20, logger=logger)
        
        logger.log(f"\nFinal Baseline Performance:")
        logger.log(f"  Average: {np.mean(baseline_scores):.1f}")
        logger.log(f"  Std Dev: {np.std(baseline_scores):.1f}")
        logger.log(f"  Min: {np.min(baseline_scores):.1f}")
        logger.log(f"  Max: {np.max(baseline_scores):.1f}")
    
    # Train explainable
    explainable_model = train_explainable_agent(logger)
    
    explainable_scores = None
    if explainable_model:
        # Evaluate explainable
        logger.log("\n" + "=" * 80)
        logger.log("EXPLAINABLE DQN EVALUATION")
        logger.log("=" * 80)
        
        explainable_scores = evaluate_agent(explainable_model, num_episodes=20, logger=logger)
        
        logger.log(f"\nFinal Explainable Performance:")
        logger.log(f"  Average: {np.mean(explainable_scores):.1f}")
        logger.log(f"  Std Dev: {np.std(explainable_scores):.1f}")
        logger.log(f"  Min: {np.min(explainable_scores):.1f}")
        logger.log(f"  Max: {np.max(explainable_scores):.1f}")
    
    # Compare results
    if baseline_scores is not None and explainable_scores is not None:
        logger.log("\n" + "=" * 80)
        logger.log("PERFORMANCE COMPARISON")
        logger.log("=" * 80)
        
        baseline_avg = np.mean(baseline_scores)
        explainable_avg = np.mean(explainable_scores)
        ratio = (explainable_avg / baseline_avg * 100) if baseline_avg > 0 else 0
        
        logger.log(f"\nBaseline Average:     {baseline_avg:.1f}")
        logger.log(f"Explainable Average:  {explainable_avg:.1f}")
        logger.log(f"Ratio (Explainable/Baseline): {ratio:.1f}%")
        
        if ratio >= 90:
            logger.log(f"? EXCELLENT: Explainable achieved >=90% of baseline")
        elif ratio >= 80:
            logger.log(f"? TARGET MET: Explainable achieved >=80% of baseline")
        elif ratio >= 60:
            logger.log(f"?? PARTIAL: Explainable is {ratio:.1f}% of baseline (target: >=80%)")
        else:
            logger.log(f"! Note: Explainable is {ratio:.1f}% of baseline (target: >=80%)")

    logger.log("\n? Training pipeline complete!")


def main_explainable_only():
    """Re-train only the explainable agent.

    The baseline was trained once and gives 34.6 avg on this seed; we
    re-use that as the reference.  This avoids spending 3+ hours retraining
    the baseline when only the explainable architecture changed.
    """
    logger = TrainingLogger(PATHS['logs'])
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'

    logger.log("=" * 80)
    logger.log("RE-TRAIN EXPLAINABLE ONLY (v2 architecture)")
    logger.log("=" * 80)
    logger.log(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

    # Re-use cached baseline if available
    baseline_path = PATHS['models'] / "baseline_dqn"
    baseline_avg = None
    if baseline_path.with_suffix(".zip").exists():
        logger.log(f"Loading cached baseline from {baseline_path}.zip for reference score")
        from stable_baselines3 import DQN as _DQN
        baseline_model = _DQN.load(str(baseline_path), device=DEVICE_CONFIG['device'])
        logger.log("\n" + "=" * 80)
        logger.log("BASELINE EVALUATION (cached model)")
        logger.log("=" * 80)
        baseline_scores = evaluate_agent(baseline_model, num_episodes=20, logger=logger)
        baseline_avg = float(np.mean(baseline_scores))
        logger.log(f"\nFinal Baseline Performance: avg={baseline_avg:.1f}, "
                   f"std={np.std(baseline_scores):.1f}")
    else:
        logger.log("? No cached baseline found.  Run main() first to produce one.")

    # Train explainable
    explainable_model = train_explainable_agent(logger)
    if not explainable_model:
        logger.log("Explainable training returned no model; aborting comparison.")
        return

    # Eval
    logger.log("\n" + "=" * 80)
    logger.log("EXPLAINABLE DQN EVALUATION (v2)")
    logger.log("=" * 80)
    explainable_scores = evaluate_agent(explainable_model, num_episodes=20, logger=logger)
    explainable_avg = float(np.mean(explainable_scores))
    logger.log(f"\nFinal Explainable Performance:")
    logger.log(f"  Average: {explainable_avg:.1f}")
    logger.log(f"  Std Dev: {np.std(explainable_scores):.1f}")
    logger.log(f"  Min: {np.min(explainable_scores):.1f}")
    logger.log(f"  Max: {np.max(explainable_scores):.1f}")

    if baseline_avg is not None and baseline_avg > 0:
        ratio = explainable_avg / baseline_avg * 100
        logger.log("\n" + "=" * 80)
        logger.log("PERFORMANCE COMPARISON")
        logger.log("=" * 80)
        logger.log(f"Baseline Average:     {baseline_avg:.1f}")
        logger.log(f"Explainable Average:  {explainable_avg:.1f}")
        logger.log(f"Ratio (Explainable/Baseline): {ratio:.1f}%")

        if ratio >= 90:
            logger.log(f"? EXCELLENT: Explainable achieved >=90% of baseline")
        elif ratio >= 80:
            logger.log(f"? TARGET MET: Explainable achieved >=80% of baseline")
        elif ratio >= 60:
            logger.log(f"?? PARTIAL: Explainable is {ratio:.1f}% of baseline (target: >=80%)")
        else:
            logger.log(f"! Note: Explainable is {ratio:.1f}% of baseline (target: >=80%)")

    logger.log("\n? Re-train pipeline complete!")


if __name__ == "__main__":
    import sys
    if "--explainable-only" in sys.argv:
        main_explainable_only()
    else:
        main()
