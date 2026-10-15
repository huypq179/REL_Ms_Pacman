"""
XRL Ms-Pacman Dashboard - Professional Real-time Comparison
Real-time visualization comparing Baseline vs Explainable RL agents
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import cv2
import os
from pathlib import Path
import torch
from datetime import datetime
import time
import json

st.set_page_config(
    page_title="XRL Ms-Pacman | Agent Comparison",
    page_icon="\U0001F3AE",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================================
# CUSTOM STYLES - Professional Dark Theme
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #111827;
        --bg-tertiary: #1f2937;
        --bg-card: #1a1f2e;
        --accent-green: #10b981;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --accent-orange: #f59e0b;
        --accent-red: #ef4444;
        --accent-cyan: #06b6d4;
        --text-primary: #f9fafb;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --border-color: #374151;
        --gradient-start: #0f172a;
        --gradient-end: #1e3a5f;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--gradient-start) 0%, var(--gradient-end) 100%);
        font-family: 'Inter', sans-serif;
    }
    
    .header-container {
        background: linear-gradient(90deg, var(--bg-card) 0%, var(--bg-tertiary) 100%);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
    }
    
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-green), var(--accent-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .subtitle {
        color: var(--text-secondary);
        font-size: 1rem;
        margin-top: 8px;
    }
    
    .model-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
        height: 100%;
    }
    
    .model-card-baseline {
        border-top: 3px solid var(--accent-blue);
    }
    
    .model-card-explainable {
        border-top: 3px solid var(--accent-purple);
    }
    
    .model-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .model-title-baseline {
        color: var(--accent-blue);
    }
    
    .model-title-explainable {
        color: var(--accent-purple);
    }
    
    .metric-container {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .status-ready {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 1px solid var(--accent-green);
    }
    
    .status-notfound {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
        border: 1px solid var(--accent-red);
    }
    
    .game-frame-container {
        background: var(--bg-primary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 12px;
    }
    
    .heatmap-container {
        background: var(--bg-primary);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        padding: 12px;
    }
    
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 12px 24px;
        transition: all 0.2s ease;
    }
    
    .btn-primary > button {
        background: linear-gradient(135deg, var(--accent-green), var(--accent-cyan));
        color: white;
        border: none;
    }
    
    .btn-primary > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
    }
    
    .explanation-panel {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid var(--accent-purple);
    }
    
    .live-indicator {
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
    
    .live-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: var(--accent-green);
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# MODEL LOADING FUNCTIONS
# ============================================================================

@st.cache_resource
def load_baseline_model():
    """Load baseline DQN model."""
    try:
        from stable_baselines3 import DQN
        model_path = "outputs/models/baseline_dqn.zip"
        if os.path.exists(model_path):
            return DQN.load(model_path, device='cpu')
    except Exception:
        import traceback, sys
        print("[dashboard] Failed to load baseline model:", file=sys.stderr)
        traceback.print_exc()
    return None


@st.cache_resource
def load_explainable_model():
    """Load explainable DQN model."""
    try:
        from stable_baselines3 import DQN
        model_path = "outputs/models/explainable_dqn.zip"
        if os.path.exists(model_path):
            return DQN.load(model_path, device='cpu')
    except Exception:
        import traceback, sys
        print("[dashboard] Failed to load explainable model:", file=sys.stderr)
        traceback.print_exc()
    return None


def check_model_status():
    """Check which models are available."""
    baseline = load_baseline_model()
    explainable = load_explainable_model()
    return {
        'baseline': baseline is not None,
        'explainable': explainable is not None,
        'baseline_model': baseline,
        'explainable_model': explainable
    }


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def compute_saliency_map(model, obs):
    """Compute gradient-based saliency map."""
    try:
        obs_for_q = obs.transpose(0, 3, 1, 2) if obs.ndim == 4 else obs
        obs_tensor = torch.FloatTensor(obs_for_q).unsqueeze(0).to(model.device)
        obs_tensor.requires_grad_(True)
        
        q_values = model.q_net(obs_tensor)
        best_action = q_values.argmax(dim=1)
        q_values[0, best_action].backward()
        
        gradients = obs_tensor.grad[0].cpu().numpy()
        saliency = np.max(np.abs(gradients), axis=0)
        
        if saliency.max() > 0:
            saliency = (saliency / saliency.max() * 255).astype(np.uint8)
        else:
            saliency = np.zeros((84, 84), dtype=np.uint8)
        
        return saliency
    except:
        return np.zeros((84, 84), dtype=np.uint8)


def compute_attention_visualization(model, obs):
    """Compute attention visualization for explainable model."""
    try:
        obs_for_q = obs.transpose(0, 3, 1, 2) if obs.ndim == 4 else obs
        obs_tensor = torch.FloatTensor(obs_for_q).unsqueeze(0).to(model.device)
        obs_tensor.requires_grad_(True)
        
        features_extractor = model.policy.features_extractor
        
        if hasattr(features_extractor, 'attention_extractor'):
            with torch.enable_grad():
                attended_features, attention_data = features_extractor.attention_extractor(obs_tensor)
            
            individual_maps = []
            for attn_map in attention_data.get('individual_maps', []):
                map_np = attn_map[0, 0].detach().cpu().numpy()
                map_resized = cv2.resize(map_np, (84, 84))
                individual_maps.append(map_resized)
            
            combined_map = attention_data.get('combined_map', None)
            if combined_map is not None:
                combined_map = cv2.resize(combined_map[0, 0].detach().cpu().numpy(), (84, 84))
            
            attention_weights = [np.mean(m) for m in individual_maps]
            
            return {
                'individual_maps': individual_maps,
                'combined_map': combined_map,
                'weights': attention_weights,
                'head_names': ['Threat Detection', 'Reward Focus', 'Path Planning'][:len(individual_maps)]
            }
        return None
    except:
        return None


def run_episode(model, max_steps=2000, explainable=False):
    """Run a single episode."""
    import gymnasium as gym
    import ale_py
    from stable_baselines3.common.atari_wrappers import AtariWrapper
    from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
    
    gym.register_envs(ale_py)
    env = gym.make("MsPacman-v4", render_mode=None)
    env = AtariWrapper(env, noop_max=30, frame_skip=4, screen_size=84,
                       terminal_on_life_loss=False, clip_reward=True)
    env = DummyVecEnv([lambda: env])
    env = VecFrameStack(env, n_stack=4)
    
    reset_result = env.reset()
    obs = reset_result[0] if isinstance(reset_result, tuple) else reset_result
    
    episode_data = {
        'frames': [], 'saliency_maps': [], 'attention_data': [],
        'q_values_history': [], 'actions': [], 'rewards': [],
        'scores': [], 'lives': [], 'total_reward': 0,
    }
    
    done = False
    step = 0
    
    while not done and step < max_steps:
        action, _ = model.predict(obs, deterministic=False)
        
        obs_for_q = obs.transpose(0, 3, 1, 2) if obs.ndim == 4 else obs
        obs_tensor = torch.FloatTensor(obs_for_q).to(model.device)
        with torch.no_grad():
            q_vals = model.q_net(obs_tensor)[0].cpu().numpy()
        
        if explainable:
            attn_data = compute_attention_visualization(model, obs)
            if attn_data:
                episode_data['attention_data'].append(attn_data)
        else:
            saliency = compute_saliency_map(model, obs)
            episode_data['saliency_maps'].append(saliency)
        
        frame = obs[0, :, :, -1] if obs.ndim == 4 else obs[-1]
        episode_data['frames'].append(frame)
        episode_data['q_values_history'].append(q_vals)
        episode_data['actions'].append(action)
        
        step_result = env.step(action)
        if len(step_result) == 5:
            obs, reward, terminated, truncated, info = step_result
            done = terminated or truncated
        else:
            obs, reward, done_arr, info = step_result
            # VecEnv returns arrays of shape (n_envs,) and a list of info dicts
            done = bool(np.asarray(done_arr).reshape(-1)[0])
            reward = np.asarray(reward).reshape(-1)[0]
            if isinstance(info, (list, tuple)):
                info = info[0] if info else {}
        
        reward = float(reward)
        episode_data['total_reward'] += reward
        episode_data['rewards'].append(reward)
        
        if step % 10 == 0:
            episode_data['scores'].append(info.get('episode_frame_number', step) if isinstance(info, dict) else step)
            episode_data['lives'].append(info.get('lives', 3) if isinstance(info, dict) else 3)
        
        step += 1
    
    env.close()
    return episode_data


def render_q_values_chart(q_vals, height=200):
    """Render Q-values as professional bar chart."""
    actions = ['NOOP', 'UP', 'RIGHT', 'LEFT', 'DOWN', 'U-R', 'U-L', 'D-R', 'D-L'][:len(q_vals)]
    colors = ['#10b981' if q == max(q_vals) else '#374151' for q in q_vals]
    
    fig = go.Figure(data=[
        go.Bar(x=actions, y=q_vals, marker_color=colors,
               text=[f'{q:.1f}' for q in q_vals], textposition='outside')
    ])
    fig.update_layout(
        height=height, margin=dict(l=20, r=20, t=30, b=40),
        paper_bgcolor='transparent', plot_bgcolor='transparent',
        font=dict(color='#9ca3af', size=11),
        xaxis=dict(gridcolor='#1f2937', tickfont=dict(color='#9ca3af')),
        yaxis=dict(gridcolor='#1f2937', tickfont=dict(color='#9ca3af')),
        showlegend=False
    )
    return fig


def render_attention_heads(attn_data, height=180):
    """Render attention heads as horizontal bar chart."""
    if not attn_data or 'weights' not in attn_data:
        return go.Figure()
    
    colors = ['#ef4444', '#f59e0b', '#3b82f6'][:len(attn_data['weights'])]
    
    fig = go.Figure(data=[
        go.Bar(
            y=attn_data.get('head_names', ['Head']*len(attn_data['weights'])),
            x=attn_data['weights'],
            orientation='h',
            marker_color=colors,
            text=[f'{w*100:.1f}%' for w in attn_data['weights']],
            textposition='outside'
        )
    ])
    fig.update_layout(
        height=height, margin=dict(l=100, r=20, t=20, b=30),
        paper_bgcolor='transparent', plot_bgcolor='transparent',
        font=dict(color='#9ca3af', size=11),
        xaxis=dict(title='Weight', gridcolor='#1f2937', tickfont=dict(color='#9ca3af')),
        yaxis=dict(gridcolor='#1f2937', tickfont=dict(color='#9ca3af')),
        showlegend=False
    )
    return fig


# ============================================================================
# MAIN DASHBOARD
# ============================================================================

@st.cache_resource
def load_model_from_path(path_str):
    """Load any saved DQN checkpoint on CPU (cached per file)."""
    from stable_baselines3 import DQN
    return DQN.load(path_str, device='cpu')


def render_q_bars_html(q_values, action):
    """Q-values as lightweight HTML bars (much faster than a Plotly chart per frame)."""
    from live_game import ACTION_NAMES
    lo, hi = float(np.min(q_values)), float(np.max(q_values))
    span = max(hi - lo, 1e-6)
    rows = []
    for i, q in enumerate(q_values):
        pct = 8 + 92 * (float(q) - lo) / span
        color = '#10b981' if i == action else '#374151'
        rows.append(
            '<div style="display:flex;align-items:center;gap:8px;margin:3px 0;">'
            f'<span style="width:90px;color:#9ca3af;font-size:0.8rem;">{ACTION_NAMES[i]}</span>'
            '<div style="flex:1;background:#111827;border-radius:4px;">'
            f'<div style="width:{pct:.0f}%;height:14px;background:{color};border-radius:4px;"></div></div>'
            '<span style="width:52px;text-align:right;font-family:JetBrains Mono,monospace;'
            f'font-size:0.8rem;color:#f9fafb;">{float(q):.2f}</span></div>'
        )
    return '<div class="model-card">' + ''.join(rows) + '</div>'


def render_live_stats_html(frame):
    """Score / lives / step / action tiles for the live view."""
    from live_game import ACTION_NAMES, ACTION_ARROWS
    hearts = '&#9829; ' * max(frame.lives, 0) or '&ndash;'
    tiles = [
        ('Score', f'{frame.score:.0f}', '#10b981'),
        ('Lives', hearts, '#ef4444'),
        ('Step', f'{frame.step}', '#3b82f6'),
        ('Action', f'{ACTION_ARROWS[frame.action]} {ACTION_NAMES[frame.action]}', '#f59e0b'),
    ]
    cells = ''.join(
        '<div class="metric-container" style="flex:1;">'
        f'<div class="metric-value" style="color:{c};font-size:1.4rem;">{v}</div>'
        f'<div class="metric-label">{k}</div></div>'
        for k, v, c in tiles
    )
    return f'<div style="display:flex;gap:10px;margin-bottom:12px;">{cells}</div>'


def render_live_view():
    """Full-screen live view: the agent plays Ms-Pacman in real time."""
    from live_game import play_live, compose_screen

    model_files = sorted(Path("outputs/models").glob("*.zip"))
    if not model_files:
        st.warning("No trained models found in outputs/models. Train one with `python src/train.py`.")
        return

    names = [p.name for p in model_files]
    default_idx = names.index("best_model.zip") if "best_model.zip" in names else 0

    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        model_name = st.selectbox("Model", names, index=default_idx, key="live_model")
    with c2:
        fps = st.slider("Speed (FPS)", 5, 60, 20, key="live_fps")
    with c3:
        epsilon = st.slider("Random action rate", 0.0, 0.2, 0.02, 0.01, key="live_eps")
    with c4:
        overlay = st.checkbox("Saliency overlay", value=False, key="live_overlay")

    b1, b2, _ = st.columns([1, 1, 4])
    with b1:
        start = st.button("Play live", type="primary", use_container_width=True, key="live_start")
    with b2:
        st.button("Stop", use_container_width=True, key="live_stop")

    screen_col, info_col = st.columns([3, 2])
    with screen_col:
        screen = st.empty()
    with info_col:
        stats = st.empty()
        qbars = st.empty()

    if not start:
        screen.markdown(
            '<div style="text-align:center;padding:80px 20px;background:var(--bg-secondary);'
            'border-radius:16px;border:2px dashed var(--border-color);color:var(--text-secondary);">'
            'Press <strong>Play live</strong> to watch the agent play.</div>',
            unsafe_allow_html=True,
        )
        return

    model = load_model_from_path(str(Path("outputs/models") / model_name))
    delay = 1.0 / fps
    last = None
    for frame in play_live(model, epsilon=epsilon, show_saliency=overlay):
        t0 = time.time()
        img = compose_screen(frame.rgb, frame.saliency if overlay else None, scale=3)
        screen.image(img, channels="RGB", use_column_width=True)
        stats.markdown(render_live_stats_html(frame), unsafe_allow_html=True)
        qbars.markdown(render_q_bars_html(frame.q_values, frame.action), unsafe_allow_html=True)
        last = frame
        time.sleep(max(0.0, delay - (time.time() - t0)))

    if last is not None:
        st.success(f"Game over. Final score: {last.score:.0f} in {last.step} decisions.")


def main():
    """Main dashboard application."""
    
    if 'comparison_data' not in st.session_state:
        st.session_state['comparison_data'] = None
    if 'current_frame' not in st.session_state:
        st.session_state['current_frame'] = 0
    
    model_status = check_model_status()
    
    # Header
    st.markdown("""
    <div class="header-container">
        <h1 class="main-title">XRL Ms-Pacman Agent Comparison</h1>
        <p class="subtitle">Real-time visualization: Baseline DQN vs Explainable Attention Network</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status Bar
    status_cols = st.columns([1, 1, 2])
    with status_cols[0]:
        status_class = 'status-ready' if model_status['baseline'] else 'status-notfound'
        status_text = '&#9679; Ready' if model_status['baseline'] else '&#9675; Not Found'
        st.markdown(f'<div class="status-badge {status_class}">Baseline {status_text}</div>', unsafe_allow_html=True)
    
    with status_cols[1]:
        status_class = 'status-ready' if model_status['explainable'] else 'status-notfound'
        status_text = '&#9679; Ready' if model_status['explainable'] else '&#9675; Not Found'
        st.markdown(f'<div class="status-badge {status_class}">Explainable {status_text}</div>', unsafe_allow_html=True)
    
    with status_cols[2]:
        st.markdown('<div class="live-indicator"><div class="live-dot"></div> <span>Live Comparison Mode</span></div>', unsafe_allow_html=True)
    
    view = st.radio("View", ["Live Game", "Play Game", "Comparison"], horizontal=True,
                    label_visibility="collapsed", key="main_view")
    st.divider()
    if view == "Live Game":
        render_live_view()
        return
    
    if view == "Play Game":
        from pacman_game_streamlit import create_game_tab
        create_game_tab()
        return
    
    # Control Panel
    control_cols = st.columns([1, 1, 1, 2])
    
    with control_cols[0]:
        num_episodes = st.selectbox("Episodes", [1, 3, 5, 10], index=1)
    
    with control_cols[1]:
        playback_speed = st.slider("Playback Speed", 1, 30, 10)
    
    with control_cols[2]:
        show_saliency = st.checkbox("Show Saliency", value=True)
    
    with control_cols[3]:
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            run_clicked = st.button("Run Comparison", type="primary", use_container_width=True)
        with col_btn2:
            reset_clicked = st.button("Reset", use_container_width=True)
    
    if reset_clicked:
        st.session_state['comparison_data'] = None
        st.session_state['current_frame'] = 0
        st.rerun()
    
    # Run Comparison
    if run_clicked and (model_status['baseline'] or model_status['explainable']):
        with st.spinner("Running episodes..."):
            comparison_data = {'baseline': None, 'explainable': None}
            
            if model_status['baseline']:
                st.info("Running Baseline DQN episodes...")
                comparison_data['baseline'] = run_episode(
                    model_status['baseline_model'],
                    max_steps=2000,
                    explainable=False
                )
            
            if model_status['explainable']:
                st.info("Running Explainable DQN episodes...")
                comparison_data['explainable'] = run_episode(
                    model_status['explainable_model'],
                    max_steps=2000,
                    explainable=True
                )
            
            st.session_state['comparison_data'] = comparison_data
            st.success("Episodes complete! View the comparison below.")
            st.rerun()
    
    # Display Comparison
    if st.session_state['comparison_data']:
        comparison_data = st.session_state['comparison_data']
        
        # Episode Summary
        st.markdown("### Episode Summary")
        
        summary_cols = st.columns([1, 1])
        
        # Baseline Summary
        with summary_cols[0]:
            if comparison_data['baseline']:
                ep_data = comparison_data['baseline']
                st.markdown('<div class="model-card model-card-baseline">', unsafe_allow_html=True)
                st.markdown('<div class="model-title model-title-baseline">&#128202; Baseline DQN</div>', unsafe_allow_html=True)
                
                m_cols = st.columns(3)
                with m_cols[0]:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: #3b82f6;">{ep_data['total_reward']:.0f}</div>
                        <div class="metric-label">Final Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_cols[1]:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: #3b82f6;">{len(ep_data['frames'])}</div>
                        <div class="metric-label">Steps</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_cols[2]:
                    avg_reward = ep_data['total_reward'] / max(len(ep_data['rewards']), 1)
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: #3b82f6;">{avg_reward:.2f}</div>
                        <div class="metric-label">Avg Reward</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("Baseline model not available")
        
        # Explainable Summary
        with summary_cols[1]:
            if comparison_data['explainable']:
                ep_data = comparison_data['explainable']
                st.markdown('<div class="model-card model-card-explainable">', unsafe_allow_html=True)
                st.markdown('<div class="model-title model-title-explainable">&#129504; Explainable DQN</div>', unsafe_allow_html=True)
                
                m_cols = st.columns(3)
                with m_cols[0]:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: #8b5cf6;">{ep_data['total_reward']:.0f}</div>
                        <div class="metric-label">Final Score</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_cols[1]:
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: #8b5cf6;">{len(ep_data['frames'])}</div>
                        <div class="metric-label">Steps</div>
                    </div>
                    """, unsafe_allow_html=True)
                with m_cols[2]:
                    avg_reward = ep_data['total_reward'] / max(len(ep_data['rewards']), 1)
                    st.markdown(f"""
                    <div class="metric-container">
                        <div class="metric-value" style="color: #8b5cf6;">{avg_reward:.2f}</div>
                        <div class="metric-label">Avg Reward</div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("Explainable model not available")
        
        # Comparison Delta
        if comparison_data['baseline'] and comparison_data['explainable']:
            delta = comparison_data['explainable']['total_reward'] - comparison_data['baseline']['total_reward']
            delta_pct = (delta / max(comparison_data['baseline']['total_reward'], 1)) * 100
            
            delta_color = '#10b981' if delta >= 0 else '#ef4444'
            delta_sign = '+' if delta >= 0 else ''
            st.markdown(f"""
            <div style="text-align: center; padding: 16px; background: var(--bg-secondary); border-radius: 12px; margin: 20px 0;">
                <span style="font-size: 1.1rem; color: var(--text-secondary);">Performance Delta: </span>
                <span style="font-size: 1.5rem; font-weight: 700; color: {delta_color};">
                    {delta_sign}{delta:.0f} ({delta_sign}{delta_pct:.1f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Side-by-Side Game View
        st.markdown("### Frame-by-Frame Comparison")
        
        active_data = comparison_data['baseline'] or comparison_data['explainable']
        total_frames = len(active_data['frames'])
        
        if total_frames > 0:
            frame_idx = st.slider(
                "Select Frame",
                0, max(0, total_frames - 1),
                st.session_state['current_frame'],
                key="frame_slider_compare"
            )
            st.session_state['current_frame'] = frame_idx
            
            game_cols = st.columns([1, 1, 1, 1])
            
            # Baseline Game
            with game_cols[0]:
                if comparison_data['baseline']:
                    frame = comparison_data['baseline']['frames'][min(frame_idx, len(comparison_data['baseline']['frames'])-1)]
                    frame_display = cv2.resize(frame, (280, 280)) if len(frame.shape) == 2 else cv2.resize(frame, (280, 280))
                    if len(frame_display.shape) == 2:
                        frame_display = cv2.cvtColor(frame_display, cv2.COLOR_GRAY2RGB)
                    
                    st.markdown("""
                    <div class="game-frame-container">
                        <div style="color: #3b82f6; font-weight: 600; margin-bottom: 8px;">&#128202; Baseline DQN</div>
                    """, unsafe_allow_html=True)
                    st.image(frame_display, use_container_width=True)
                    
                    q_vals = comparison_data['baseline']['q_values_history'][min(frame_idx, len(comparison_data['baseline']['q_values_history'])-1)]
                    st.plotly_chart(render_q_values_chart(q_vals, 150), use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Baseline Saliency
            with game_cols[1]:
                if comparison_data['baseline'] and show_saliency:
                    saliency = comparison_data['baseline']['saliency_maps'][min(frame_idx, len(comparison_data['baseline']['saliency_maps'])-1)]
                    saliency_display = cv2.resize(saliency, (280, 280))
                    saliency_colored = cv2.applyColorMap(saliency_display, cv2.COLORMAP_JET)
                    saliency_colored = cv2.cvtColor(saliency_colored, cv2.COLOR_BGR2RGB)
                    
                    st.markdown("""
                    <div class="heatmap-container">
                        <div style="color: #3b82f6; font-weight: 600; margin-bottom: 8px;">&#128269; Gradient Saliency</div>
                    """, unsafe_allow_html=True)
                    st.image(saliency_colored, use_container_width=True)
                    
                    best_action = comparison_data['baseline']['actions'][min(frame_idx, len(comparison_data['baseline']['actions'])-1)]
                    action_names = ['NOOP', 'UP', 'RIGHT', 'LEFT', 'DOWN', 'U-R', 'U-L', 'D-R', 'D-L']
                    st.markdown(f"""
                    <div class="explanation-panel" style="margin-top: 12px;">
                        <strong>Decision:</strong> {action_names[best_action]}<br>
                        <small style="color: var(--text-muted);">Shows which pixels influenced Q-value prediction</small>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Explainable Game
            with game_cols[2]:
                if comparison_data['explainable']:
                    frame = comparison_data['explainable']['frames'][min(frame_idx, len(comparison_data['explainable']['frames'])-1)]
                    frame_display = cv2.resize(frame, (280, 280)) if len(frame.shape) == 2 else cv2.resize(frame, (280, 280))
                    if len(frame_display.shape) == 2:
                        frame_display = cv2.cvtColor(frame_display, cv2.COLOR_GRAY2RGB)
                    
                    st.markdown("""
                    <div class="game-frame-container">
                        <div style="color: #8b5cf6; font-weight: 600; margin-bottom: 8px;">&#129504; Explainable DQN</div>
                    """, unsafe_allow_html=True)
                    st.image(frame_display, use_container_width=True)
                    
                    q_vals = comparison_data['explainable']['q_values_history'][min(frame_idx, len(comparison_data['explainable']['q_values_history'])-1)]
                    st.plotly_chart(render_q_values_chart(q_vals, 150), use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Explainable Attention
            with game_cols[3]:
                if comparison_data['explainable']:
                    attn_data = comparison_data['explainable']['attention_data']
                    if attn_data and frame_idx < len(attn_data):
                        attn = attn_data[frame_idx]
                        
                        st.markdown("""
                        <div class="heatmap-container">
                            <div style="color: #8b5cf6; font-weight: 600; margin-bottom: 8px;">&#128065;&#65039; Attention Heads</div>
                        """, unsafe_allow_html=True)
                        
                        if attn.get('combined_map') is not None:
                            combined = cv2.resize(attn['combined_map'], (280, 280))
                            combined_colored = cv2.applyColorMap((combined * 255).astype(np.uint8), cv2.COLORMAP_JET)
                            combined_colored = cv2.cvtColor(combined_colored, cv2.COLOR_BGR2RGB)
                            st.image(combined_colored, use_container_width=True)
                        
                        st.plotly_chart(render_attention_heads(attn, 120), use_container_width=True)
                        
                        head_descriptions = {
                            'Threat Detection': 'Ghosts & dangers',
                            'Reward Focus': 'Pellets & fruits',
                            'Path Planning': 'Navigation routes'
                        }
                        
                        explanation = "<div class='explanation-panel' style='margin-top: 12px;'><strong>Attention Focus:</strong><br>"
                        for name, weight in zip(attn.get('head_names', []), attn.get('weights', [])):
                            desc = head_descriptions.get(name, '')
                            explanation += f"- {name}: {weight*100:.1f}% <small style='color: var(--text-muted);'>{desc}</small><br>"
                        explanation += "</div>"
                        st.markdown(explanation, unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
        
        # Score Progression
        st.divider()
        st.markdown("### Score Progression Comparison")
        
        fig = go.Figure()
        
        if comparison_data['baseline']:
            baseline_scores = [0]
            cumulative = 0
            for r in comparison_data['baseline']['rewards']:
                cumulative += r
                baseline_scores.append(cumulative)
            fig.add_trace(go.Scatter(
                x=list(range(len(baseline_scores))),
                y=baseline_scores,
                mode='lines',
                name='Baseline DQN',
                line=dict(color='#3b82f6', width=2)
            ))
        
        if comparison_data['explainable']:
            explainable_scores = [0]
            cumulative = 0
            for r in comparison_data['explainable']['rewards']:
                cumulative += r
                explainable_scores.append(cumulative)
            fig.add_trace(go.Scatter(
                x=list(range(len(explainable_scores))),
                y=explainable_scores,
                mode='lines',
                name='Explainable DQN',
                line=dict(color='#8b5cf6', width=2)
            ))
        
        fig.update_layout(
            height=300,
            paper_bgcolor='transparent',
            plot_bgcolor='rgba(17, 24, 39, 0.8)',
            font=dict(color='#9ca3af'),
            xaxis=dict(title='Step', gridcolor='#1f2937'),
            yaxis=dict(title='Cumulative Score', gridcolor='#1f2937'),
            legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#1f2937'),
            margin=dict(l=50, r=20, t=40, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # Placeholder View
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-secondary); border-radius: 16px; border: 2px dashed var(--border-color);">
            <div style="font-size: 4rem; margin-bottom: 20px;">&#127918;</div>
            <h2 style="color: var(--text-primary); margin-bottom: 10px;">Ready to Compare</h2>
            <p style="color: var(--text-secondary); max-width: 500px; margin: 0 auto;">
                Click <strong>Run Comparison</strong> to start a side-by-side evaluation of Baseline DQN and Explainable Attention Network.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature highlights
        feature_cols = st.columns(3)
        
        features = [
            ("&#128202;", "Baseline DQN", "Standard Deep Q-Network with gradient-based saliency visualization"),
            ("&#129504;", "Explainable DQN", "Multi-head attention mechanism with interpretable decision focus"),
            ("&#9889;", "Real-time Comparison", "Side-by-side frame analysis with Q-value breakdown")
        ]
        
        for i, (icon, title, desc) in enumerate(features):
            with feature_cols[i]:
                st.markdown(f"""
                <div class="model-card" style="text-align: center; padding: 30px;">
                    <div style="font-size: 2.5rem; margin-bottom: 16px;">{icon}</div>
                    <h3 style="color: var(--text-primary); margin-bottom: 12px;">{title}</h3>
                    <p style="color: var(--text-secondary);">{desc}</p>
                </div>
                """, unsafe_allow_html=True)
        
        if not model_status['baseline'] and not model_status['explainable']:
            st.warning("No trained models found. Please train models first using `python src/train.py`")


if __name__ == "__main__":
    main()
