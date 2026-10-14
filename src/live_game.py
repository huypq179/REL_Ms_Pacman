"""
Live gameplay support for the dashboard.

Runs a trained DQN agent in Ms-Pacman and yields one `LiveFrame` per agent
decision, containing the full-colour game screen, the real score, lives,
the chosen action, the Q-values and (optionally) a gradient saliency map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

import cv2
import numpy as np
import torch
import gymnasium as gym
import ale_py
from stable_baselines3.common.atari_wrappers import AtariWrapper
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack

gym.register_envs(ale_py)

# Same base environment that train.py / evaluate_baseline.py use via make_atari_env.
LIVE_ENV_ID = "MsPacmanNoFrameskip-v4"

ACTION_NAMES = ["NOOP", "UP", "RIGHT", "LEFT", "DOWN", "UP-RIGHT", "UP-LEFT", "DOWN-RIGHT", "DOWN-LEFT"]
ACTION_ARROWS = ["\u00b7", "\u2191", "\u2192", "\u2190", "\u2193", "\u2197", "\u2196", "\u2198", "\u2199"]


@dataclass
class LiveFrame:
    rgb: np.ndarray                 # full-colour screen, (210, 160, 3) uint8
    step: int                       # agent decisions taken so far
    score: float                    # real (unclipped) game score
    lives: int
    action: int                     # action about to be played
    q_values: np.ndarray            # Q-values for every action
    saliency: Optional[np.ndarray]  # (84, 84) in [0, 1], or None
    done: bool                      # True on the last frame of the game


def make_live_env(seed: int = 0):
    """Build the agent-facing env (84x84 gray, 4 stacked frames) plus a handle for colour rendering."""
    base = gym.make(LIVE_ENV_ID, render_mode="rgb_array")
    wrapped = AtariWrapper(
        base,
        noop_max=30,
        frame_skip=4,
        screen_size=84,
        terminal_on_life_loss=False,  # play the whole game, not one life
        clip_reward=False,            # keep the real score
    )
    venv = DummyVecEnv([lambda: wrapped])
    venv.seed(seed)
    return VecFrameStack(venv, n_stack=4), wrapped


def analyse(model, obs: np.ndarray, want_saliency: bool):
    """Return (q_values, saliency or None) for the current stacked observation."""
    obs_t, _ = model.policy.obs_to_tensor(obs)
    if want_saliency:
        obs_t = obs_t.float().requires_grad_(True)
        q = model.q_net(obs_t)
        q[0, q.argmax(dim=1)[0]].backward()
        sal = obs_t.grad[0].abs().max(dim=0).values.cpu().numpy()
        model.q_net.zero_grad(set_to_none=True)
        peak = float(sal.max())
        sal = sal / peak if peak > 0 else np.zeros_like(sal)
        return q.detach()[0].cpu().numpy(), sal
    with torch.no_grad():
        q = model.q_net(obs_t)
    return q[0].cpu().numpy(), None


def play_live(
    model,
    epsilon: float = 0.02,
    show_saliency: bool = False,
    max_steps: int = 20_000,
    seed: int = 0,
) -> Iterator[LiveFrame]:
    """Play one full game and yield a LiveFrame per decision."""
    venv, wrapped = make_live_env(seed)
    rng = np.random.default_rng(seed)
    try:
        obs = venv.reset()
        score, lives, step = 0.0, 3, 0
        while step < max_steps:
            q, sal = analyse(model, obs, show_saliency)
            if rng.random() < epsilon:
                action = int(rng.integers(len(q)))
            else:
                action = int(np.argmax(q))
            rgb = wrapped.render()

            yield LiveFrame(rgb, step, score, lives, action, q, sal, False)

            obs, reward, done, info = venv.step(np.array([action]))
            score += float(reward[0])
            step += 1
            lives = int(info[0].get("lives", lives))
            if bool(done[0]):
                # The VecEnv has already reset, so reuse the last real screen.
                yield LiveFrame(rgb, step, score, lives, action, q, sal, True)
                return
    finally:
        venv.close()


def compose_screen(rgb: np.ndarray, saliency: Optional[np.ndarray] = None,
                   scale: int = 3, alpha: float = 0.55) -> np.ndarray:
    """Upscale the game screen with crisp pixels and optionally blend a saliency heatmap on top."""
    h, w = rgb.shape[:2]
    img = cv2.resize(rgb, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)
    if saliency is not None:
        heat = cv2.resize(saliency, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
        heat = cv2.GaussianBlur(heat, (0, 0), sigmaX=6)
        heat = np.clip(heat / (heat.max() + 1e-8), 0.0, 1.0) ** 0.7
        color = cv2.cvtColor(cv2.applyColorMap((heat * 255).astype(np.uint8), cv2.COLORMAP_JET),
                             cv2.COLOR_BGR2RGB)
        weight = (heat * alpha)[..., None]
        img = (img * (1.0 - weight) + color * weight).astype(np.uint8)
    return img
