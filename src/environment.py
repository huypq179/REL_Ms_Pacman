"""
Ms-Pacman Environment Setup and Utilities
"""

import gymnasium as gym
import ale_py
import numpy as np
from typing import Tuple, Dict, Any
from stable_baselines3.common.atari_wrappers import AtariWrapper, MaxAndSkipEnv
from config import ENV_NAME, SEED, FRAME_SKIP

# Register ALE environments (ALE/MsPacman-v5, etc.) into gymnasium's registry.
# Required for gymnasium >= 0.27 — the [atari] extra would normally do this,
# but we install ale-py directly to avoid the shimmy pin.
gym.register_envs(ale_py)


class MsPacmanGameState:
    """Extract high-level game state from Ms-Pacman."""
    
    def __init__(self, env):
        self.env = env
        self.ale = env.unwrapped.ale if hasattr(env.unwrapped, 'ale') else None
    
    def get_game_state(self) -> Dict[str, Any]:
        """Extract game state from RAM."""
        if not self.ale:
            return {}
        
        try:
            ram = self.ale.getRAM()
            
            pacman_x = ram[0x08]
            pacman_y = ram[0x09]
            
            ghost_red = (ram[0x0E], ram[0x0F])
            ghost_pink = (ram[0x10], ram[0x11])
            ghost_cyan = (ram[0x12], ram[0x13])
            ghost_orange = (ram[0x14], ram[0x15])
            
            score = ram[0x0A] * 256 + ram[0x0B]
            lives = ram[0x0C]
            power_timer = ram[0x1D]
            
            return {
                'pacman_pos': (pacman_x, pacman_y),
                'ghost_positions': [
                    {'color': 'red', 'pos': ghost_red},
                    {'color': 'pink', 'pos': ghost_pink},
                    {'color': 'cyan', 'pos': ghost_cyan},
                    {'color': 'orange', 'pos': ghost_orange},
                ],
                'score': score,
                'lives': lives,
                'powered_up': power_timer > 0,
                'power_timer': power_timer,
            }
        except Exception as e:
            print(f"Error extracting game state: {e}")
            return {}
    
    def calculate_threat_levels(self, game_state: Dict) -> list:
        """Calculate threat level for each ghost."""
        if not game_state:
            return []
        
        pacman_pos = game_state['pacman_pos']
        powered_up = game_state['powered_up']
        
        threats = []
        for ghost_info in game_state['ghost_positions']:
            ghost_pos = ghost_info['pos']
            color = ghost_info['color']
            
            # Euclidean distance
            distance = np.sqrt(
                (ghost_pos[0] - pacman_pos[0])**2 + 
                (ghost_pos[1] - pacman_pos[1])**2
            )
            
            if powered_up:
                threat_level = 'REWARD' if distance < 50 else 'IGNORE'
            else:
                if distance < 15:
                    threat_level = 'CRITICAL'
                elif distance < 30:
                    threat_level = 'HIGH'
                elif distance < 50:
                    threat_level = 'MEDIUM'
                else:
                    threat_level = 'LOW'
            
            threats.append({
                'color': color,
                'position': ghost_pos,
                'distance': distance,
                'threat_level': threat_level,
            })
        
        return threats


def create_ms_pacman_env(render_mode: str = None) -> gym.Env:
    """Create Ms-Pacman environment with proper wrappers."""
    
    # Create base environment
    env = gym.make(ENV_NAME, render_mode=render_mode)
    
    # Apply wrappers
    env = MaxAndSkipEnv(env, skip=FRAME_SKIP)
    
    # Note: AtariWrapper might not be compatible with all gymnasium versions
    # so we apply wrappers manually if needed
    
    return env


def create_eval_env() -> gym.Env:
    """Create evaluation environment (with rendering)."""
    return create_ms_pacman_env(render_mode='rgb_array')


def verify_environment():
    """Verify Ms-Pacman environment is working."""
    print("Creating Ms-Pacman environment...")
    env = create_ms_pacman_env()
    
    print(f"Observation space: {env.observation_space}")
    print(f"Action space: {env.action_space}")
    
    obs, info = env.reset(seed=SEED)
    print(f"Initial observation shape: {obs.shape}")
    
    # Test a few steps
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        print(f"Step {i+1}: reward={reward}, done={terminated or truncated}")
        
        if terminated or truncated:
            break
    
    env.close()
    print("? Environment verification complete!")


if __name__ == "__main__":
    verify_environment()
