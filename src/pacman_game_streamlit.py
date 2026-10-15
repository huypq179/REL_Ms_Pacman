"""
Pacman Game Integration for Streamlit Dashboard
Embeds the Pacman2.0 game directly into the XRL dashboard
"""

import streamlit as st
import numpy as np
from pathlib import Path
import sys

# Import the game component
from pacman_streamlit_component import render_pacman_game_iframe


def create_game_tab():
    """Create a tab for playing the game in the main dashboard"""
    
    st.markdown("""
    <style>
    .game-tab-header {
        background: linear-gradient(135deg, #1a1f2e 0%, #111827 100%);
        border: 2px solid #10b981;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        text-align: center;
    }
    .game-title {
        color: #10b981;
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .game-subtitle {
        color: #9ca3af;
        font-size: 1em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('''
    <div class="game-tab-header">
        <div class="game-title">🎮 Interactive Pacman Game</div>
        <div class="game-subtitle">Play the classic Pacman game directly in the dashboard</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Create tabs for different game modes
    game_tabs = st.tabs(["🎮 Play Classic", "🤖 Watch AI Agent", "📊 Statistics"])
    
    with game_tabs[0]:
        st.markdown("### Classic Pacman Gameplay")
        st.info("🎯 Use arrow keys to control Pacman. Eat all pellets while avoiding ghosts!")
        
        # Render the actual game
        render_pacman_game_iframe()
    
    with game_tabs[1]:
        st.markdown("### AI Agent vs Pacman")
        st.info("Watch the trained RL agent play Pacman with real-time explanations")
        
        col1, col2 = st.columns(2)
        with col1:
            agent_mode = st.selectbox("Select Agent", ["Baseline DQN", "Explainable DQN (v1)", "Explainable DQN (v2)"])
        with col2:
            speed = st.slider("Playback Speed", 0.5, 2.0, 1.0, step=0.1)
        
        if st.button("▶️ Play Agent Demo", key="play_agent"):
            st.success(f"Now playing {agent_mode} at {speed}x speed")
            
            # Placeholder for agent gameplay
            agent_display = st.empty()
            with agent_display.container():
                st.image("https://via.placeholder.com/672x744?text=Agent+Playing", 
                        caption="Agent gameplay with explanations", use_column_width=True)
    
    with game_tabs[2]:
        st.markdown("### Game Statistics")
        
        stat_cols = st.columns(3)
        with stat_cols[0]:
            st.metric("High Score", "1,500", delta="+100")
        with stat_cols[1]:
            st.metric("Games Played", "42")
        with stat_cols[2]:
            st.metric("Win Rate", "64.3%", delta="+5.2%")
        
        st.markdown("### Score History")
        import plotly.graph_objects as go
        
        # Sample data
        scores = [200, 350, 280, 520, 480, 650, 700, 580, 900, 1100]
        
        fig = go.Figure(data=go.Scatter(y=scores, mode='lines+markers',
                                       line=dict(color='#10b981', width=3),
                                       marker=dict(size=8, color='#10b981')))
        fig.update_layout(
            title="Score Progression Over Games",
            xaxis_title="Game Number",
            yaxis_title="Score",
            hovermode='x unified',
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(17, 24, 39, 0.8)',
            font=dict(color='#9ca3af'),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    create_game_tab()
