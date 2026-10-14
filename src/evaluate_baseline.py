"""
Evaluate a saved baseline DQN model without re-training.
Usage (from project root, venv active):
    python src\\evaluate_baseline.py
    python src\\evaluate_baseline.py --episodes 50
"""
import argparse
from pathlib import Path
import sys
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import numpy as np
import torch
# Importing ale_py triggers the side-effect that registers Atari envs
# (MsPacmanNoFrameskip-v4, ALE/MsPacman-v5, ...) into gymnasium.envs.registry.
# Without this, make_atari_env() below fails with "Environment not found".
import ale_py
from stable_baselines3 import DQN
from stable_baselines3.common.env_util import make_atari_env
from stable_baselines3.common.vec_env import VecFrameStack

# Same constants as train.py
from config import SEED, PATHS


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--model", type=str, default=str(PATHS["baseline_model"]))
    args = p.parse_args()

    # SB3 auto-resolves "baseline_dqn" or "baseline_dqn.zip"
    model_path = Path(args.model)
    if not model_path.exists():
        candidates = [Path(str(model_path) + ".zip"), model_path.with_suffix(".zip")]
        for c in candidates:
            if c.exists():
                model_path = c
                break
    if not model_path.exists():
        sys.exit(f"Model not found: {args.model}")
    print(f"Loading model from: {model_path}")
    model = DQN.load(str(model_path), device="cuda" if torch.cuda.is_available() else "cpu")

    print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print("=" * 80)
    print(f"EVALUATING BASELINE DQN over {args.episodes} episodes")
    print("=" * 80)

    env = make_atari_env("MsPacmanNoFrameskip-v4", n_envs=1, seed=SEED)
    env = VecFrameStack(env, n_stack=4)

    scores = []
    for ep in range(args.episodes):
        obs = env.reset()                   # VecEnv.reset() -> obs only
        episode_reward = 0.0
        done = np.array([False])
        while not bool(done[0]):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)  # VecEnv: 4-tuple
            episode_reward += float(reward[0])
        scores.append(episode_reward)
        print(f"  Episode {ep + 1:>2d}/{args.episodes}: Score = {episode_reward:>7.0f}")

    env.close()

    scores = np.array(scores)
    print("=" * 80)
    print("FINAL BASELINE PERFORMANCE")
    print("=" * 80)
    print(f"  Average: {scores.mean():.1f} +/- {scores.std():.1f}")
    print(f"  Min:     {scores.min():.1f}")
    print(f"  Max:     {scores.max():.1f}")
    print(f"  Median:  {np.median(scores):.1f}")
    return scores


if __name__ == "__main__":
    main()
