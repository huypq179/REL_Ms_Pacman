"""
Quick launcher for Pacman 2.0 game with Streamlit integration
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from pacman_game_integration import render_pacman_game_launcher

# Page config
st.set_page_config(
    page_title="🎮 Pacman 2.0 - Original Game",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom theme
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
    }
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
</style>
""", unsafe_allow_html=True)

# Render game
render_pacman_game_launcher()
