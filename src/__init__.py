"""
Explainable RL for Ms-Pacman Package
"""

from .config import get_config, PATHS
from .environment import create_ms_pacman_env, MsPacmanGameState
from .attention_network import create_explainable_network, ExplainableDQNNetwork
from .explainer import ExplainabilityEngine
from .train import train_baseline_agent

__version__ = "1.0.0"
__author__ = "AI Research Team"

__all__ = [
    'get_config',
    'PATHS',
    'create_ms_pacman_env',
    'MsPacmanGameState',
    'create_explainable_network',
    'ExplainableDQNNetwork',
    'ExplainabilityEngine',
    'train_baseline_agent',
]
