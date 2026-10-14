"""
Configuration for Explainable RL Ms-Pacman Project
Optimized for RTX 3050 4GB VRAM
"""

import os
from pathlib import Path
from typing import Dict, Any

# ============================================================================
# PROJECT PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
MODELS_DIR = OUTPUTS_DIR / "models"
VIDEOS_DIR = OUTPUTS_DIR / "videos"
LOGS_DIR = OUTPUTS_DIR / "logs"

# Create directories
for directory in [DATA_DIR, OUTPUTS_DIR, MODELS_DIR, VIDEOS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# ENVIRONMENT SETTINGS
# ============================================================================

ENV_NAME = "ALE/MsPacman-v5"
FRAME_SKIP = 4
NUM_ENVS = 1  # CPU-friendly
SEED = 42

# ============================================================================
# TRAINING SETTINGS (Optimized for RTX 3050 4GB)
# ============================================================================

TRAINING_CONFIG = {
    "total_timesteps": 2_000_000,  # ~3-4 hours on RTX 3050
    "learning_rate": 1e-4,
    "buffer_size": 100_000,  # Reduced to fit in 4GB VRAM
    "batch_size": 32,  # Reduced batch size
    "gamma": 0.99,
    "tau": 1.0,
    "target_update_interval": 10_000,
    "learning_starts": 50_000,
    "exploration_fraction": 0.1,
    "exploration_initial_eps": 1.0,
    "exploration_final_eps": 0.05,
    "log_interval": 10_000,
    "eval_interval": 100_000,
    "eval_episodes": 10,

    # ---- v3 attention regulariser ----
    # Weight on the entropy regulariser added to the Q-learning loss.
    # 0.01 keeps the regulariser nudging without overwhelming Q-learning.
    "attention_reg_weight": 0.01,
    # Per-head spatial entropy band.  Each head's entropy H is pushed to
    # either H <= entropy_low (focused) or H >= entropy_high (dispersed).
    # 7x7 spatial map has max entropy log(49) ~= 3.89.
    "entropy_low": 1.0,
    "entropy_high": 3.0,
    "entropy_margin": 0.3,
}

# ============================================================================
# NEURAL NETWORK ARCHITECTURE
# ============================================================================

NETWORK_ARCHITECTURE = {
    "nature_dqn": {
        "layers": [
            {"type": "Conv2d", "out_channels": 32, "kernel_size": 8, "stride": 4},
            {"type": "ReLU"},
            {"type": "Conv2d", "out_channels": 64, "kernel_size": 4, "stride": 2},
            {"type": "ReLU"},
            {"type": "Conv2d", "out_channels": 64, "kernel_size": 3, "stride": 1},
            {"type": "ReLU"},
        ],
        "features_dim": 512,  # Reduced from 1024 for VRAM
    }
}

# ============================================================================
# ATTENTION MECHANISM SETTINGS
# ============================================================================

ATTENTION_CONFIG = {
    "num_heads": 3,
    "head_names": ["threat", "reward", "path"],
    "head_colors": ["#FF0000", "#FFD700", "#00FF00"],  # Red, Gold, Green
    "attention_dim": 64,
    "use_softmax": True,
    "head_weights": {
        "threat": 0.5,
        "reward": 0.3,
        "path": 0.2,
    }
}

# ============================================================================
# EXPLAINABILITY SETTINGS
# ============================================================================

EXPLAINABILITY_CONFIG = {
    "enable_gradcam": True,
    "enable_saliency": True,
    "enable_qvalue_analysis": True,
    "enable_attention_tracking": True,
    
    # Gradient computation
    "gradcam_layers": ["conv_layer_3"],  # Last conv layer
    "saliency_computation": "gradient",  # or "integrated_gradient"
    
    # Attention tracking
    "attention_history_length": 10,  # frames
    "attention_smoothing": True,
    "smoothing_window": 3,
}

# ============================================================================
# GAME STATE DETECTION
# ============================================================================

GAME_STATE_CONFIG = {
    # Ms-Pacman RAM addresses (ALE emulator)
    "ram_addresses": {
        "pacman_x": 0x08,
        "pacman_y": 0x09,
        "ghost_red_x": 0x0E,
        "ghost_red_y": 0x0F,
        "ghost_pink_x": 0x10,
        "ghost_pink_y": 0x11,
        "ghost_cyan_x": 0x12,
        "ghost_cyan_y": 0x13,
        "ghost_orange_x": 0x14,
        "ghost_orange_y": 0x15,
        "score_high": 0x0A,
        "score_low": 0x0B,
        "lives": 0x0C,
        "power_timer": 0x1D,
    },
    "threat_distance_thresholds": {
        "critical": 15,
        "high": 30,
        "medium": 50,
        "low": 100,
    },
    "ghost_colors": {
        "red": "#FF0000",
        "pink": "#FFB6C1",
        "cyan": "#00FFFF",
        "orange": "#FFA500",
    }
}

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

VISUALIZATION_CONFIG = {
    "dashboard_width": 1600,
    "dashboard_height": 900,
    "game_panel_width": 350,
    "game_panel_height": 350,
    "heatmap_colormap": "hot",  # "jet", "viridis", "hot", "cool"
    "attention_alpha": 0.6,  # Transparency
    "fps_target": 30,
    "video_fps": 24,
    "video_quality": "high",  # "low", "medium", "high"
}

# ============================================================================
# DEVICE SETTINGS
# ============================================================================

DEVICE_CONFIG = {
    "device": "cuda",  # Auto-select GPU if available
    "cuda_index": 0,
    "dtype": "float32",  # float32 for better compatibility
    "pin_memory": True,  # Optimize data loading
}

# ============================================================================
# EVALUATION METRICS
# ============================================================================

METRICS_CONFIG = {
    "window_size": 100,  # Episodes for averaging
    "target_score": 2000,  # Target average score
    "performance_threshold": 0.94,  # 94% of baseline
    "entropy_threshold_low": 1.5,  # Strategic state
    "entropy_threshold_high": 3.0,  # Exploration state
}

# ============================================================================
# PATHS (for easy reference)
# ============================================================================

PATHS = {
    "project_root": PROJECT_ROOT,
    "data": DATA_DIR,
    "outputs": OUTPUTS_DIR,
    "models": MODELS_DIR,
    "videos": VIDEOS_DIR,
    "logs": LOGS_DIR,
    "config": PROJECT_ROOT / "src" / "config.py",
    "baseline_model": MODELS_DIR / "baseline_dqn.zip",
    "explainable_model": MODELS_DIR / "explainable_dqn.zip",
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config(section: str = None) -> Dict[str, Any]:
    """Get configuration dictionary."""
    config = {
        "environment": ENV_NAME,
        "training": TRAINING_CONFIG,
        "network": NETWORK_ARCHITECTURE,
        "attention": ATTENTION_CONFIG,
        "explainability": EXPLAINABILITY_CONFIG,
        "game_state": GAME_STATE_CONFIG,
        "visualization": VISUALIZATION_CONFIG,
        "device": DEVICE_CONFIG,
        "metrics": METRICS_CONFIG,
        "paths": PATHS,
    }
    
    if section:
        return config.get(section, {})
    return config

def print_config():
    """Print configuration summary."""
    import json
    print("=" * 80)
    print("CONFIGURATION SUMMARY")
    print("=" * 80)
    config = get_config()
    for key, value in config.items():
        print(f"\n{key.upper()}:")
        if isinstance(value, dict):
            print(json.dumps(value, indent=2, default=str))
        else:
            print(f"  {value}")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    print_config()
