"""
Wrapper to integrate Pacman2.0-main Pygame game into Streamlit
Captures pygame output and displays in Streamlit
"""

import streamlit as st
import pygame
import numpy as np
from PIL import Image
import threading
import time
import sys
import os
from pathlib import Path
from io import BytesIO
import queue

# Path to Pacman2.0-main
PACMAN_DIR = Path(__file__).parent.parent / "Pacman2.0-main"
sys.path.insert(0, str(PACMAN_DIR))

class PacmanGameRunner:
    """Run Pacman game from Pacman2.0-main in a separate thread"""
    
    def __init__(self, game_dir):
        self.game_dir = game_dir
        self.running = False
        self.paused = False
        self.frame_queue = queue.Queue(maxsize=1)
        self.game_thread = None
        self.game_process = None
        
    def start(self):
        """Start the game"""
        if not self.running:
            self.running = True
            self.game_thread = threading.Thread(target=self._run_pygame, daemon=True)
            self.game_thread.start()
    
    def stop(self):
        """Stop the game"""
        self.running = False
        if self.game_thread:
            self.game_thread.join(timeout=2)
    
    def _run_pygame(self):
        """Run the Pygame game and capture frames"""
        try:
            # Change to game directory
            os.chdir(str(self.game_dir))
            
            # Import game classes
            from pacman import Game_Setup, Pacman, Ghost, Food, Game
            
            # Initialize game
            game_setup = Game_Setup()
            
            # Create game instance
            game = Game(game_setup)
            
            # Game loop
            clock = pygame.time.Clock()
            while self.running:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    
                    # Pass events to game if needed
                    game.handle_event(event)
                
                # Update game
                game.update()
                
                # Draw game
                game.draw()
                
                # Capture frame
                frame_array = pygame.surfarray.array3d(game_setup.SCREEN)
                frame_array = np.transpose(frame_array, (1, 0, 2))  # Convert from (W,H,C) to (H,W,C)
                
                try:
                    self.frame_queue.put_nowait(frame_array)
                except queue.Full:
                    pass  # Skip frame if queue is full
                
                clock.tick(30)  # 30 FPS
            
            pygame.quit()
            
        except Exception as e:
            st.error(f"❌ Error running game: {e}")
            self.running = False
    
    def get_frame(self):
        """Get the latest frame"""
        try:
            frame = self.frame_queue.get_nowait()
            return frame
        except queue.Empty:
            return None


def render_pacman_game():
    """Render the Pacman2.0-main game in Streamlit"""
    
    # Initialize session state
    if 'game_runner' not in st.session_state:
        st.session_state.game_runner = None
    if 'game_running' not in st.session_state:
        st.session_state.game_running = False
    
    st.markdown("""
    <style>
    .game-header {
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
        margin-bottom: 8px;
    }
    .game-subtitle {
        color: #9ca3af;
        font-size: 0.95em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="game-header">
        <div class="game-title">🎮 Pacman 2.0 - Original Game</div>
        <div class="game-subtitle">Tích hợp từ Pacman2.0-main | Original Pygame Game</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    game_tabs = st.tabs(["🎮 Chơi Game", "📖 Hướng Dẫn", "⚙️ Cài Đặt"])
    
    with game_tabs[0]:
        st.markdown("### 🕹️ Chơi Pacman")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Bắt Đầu Game", key="start_btn", use_container_width=True):
                st.session_state.game_running = True
                if st.session_state.game_runner is None:
                    st.session_state.game_runner = PacmanGameRunner(PACMAN_DIR)
                st.session_state.game_runner.start()
        
        with col2:
            if st.button("⏸️ Tạm Dừng", key="pause_btn", use_container_width=True):
                st.session_state.game_running = False
                if st.session_state.game_runner:
                    st.session_state.game_runner.stop()
        
        with col3:
            if st.button("🔄 Reset", key="reset_btn", use_container_width=True):
                if st.session_state.game_runner:
                    st.session_state.game_runner.stop()
                st.session_state.game_runner = None
                st.session_state.game_running = False
                st.rerun()
        
        # Game display area
        game_placeholder = st.empty()
        
        # Display frames
        if st.session_state.game_running and st.session_state.game_runner:
            st.info("🎮 Game đang chạy... (Nhấn nút để dừng)")
            
            frame_placeholder = st.empty()
            
            # Update loop
            while st.session_state.game_running and st.session_state.game_runner.running:
                frame = st.session_state.game_runner.get_frame()
                if frame is not None:
                    # Convert to PIL Image
                    img = Image.fromarray(frame.astype('uint8'))
                    frame_placeholder.image(img, caption="Pacman 2.0 Gameplay", use_column_width=True)
                time.sleep(0.033)  # ~30 FPS
        
        else:
            st.info("ℹ️ Nhấn '▶️ Bắt Đầu Game' để chơi!")
            # Show placeholder
            st.image("https://via.placeholder.com/672x840?text=Pacman+Game", use_column_width=True)
    
    with game_tabs[1]:
        st.markdown("""
        ### 📖 Hướng Dẫn Chơi
        
        **Điều Khiển:**
        - **W** - Đi Lên ⬆️
        - **A** - Sang Trái ⬅️
        - **S** - Đi Xuống ⬇️
        - **D** - Sang Phải ➡️
        
        **Mục Tiêu:**
        - 🟡 Ăn tất cả các viên mồi (.)
        - 👻 Tránh gặp ma quái
        - ⭐ Ăn power-up để gọc ma quái
        - 🏆 Đạt điểm cao nhất!
        
        **Nhân Vật:**
        - **Pacman** 🟡: Nhân vật chính (bạn)
        - **Blinky** 🔴: Ma quái đỏ (đuổi theo)
        - **Pinky** 🩷: Ma quái hồng (chặn đường)
        - **Inky** 🩵: Ma quái xanh (chiến lược)
        - **Clyde** 🟠: Ma quái cam (ngẫu nhiên)
        """)
    
    with game_tabs[2]:
        st.markdown("""
        ### ⚙️ Cài Đặt & Thông Tin
        
        **Về Game:**
        - Phiên bản: Pacman 2.0 (Original)
        - Framework: Pygame
        - Độ phân giải: 672×840 px
        - FPS: 30
        
        **Cơ Sở:**
        - 📁 Vị trí: `/Pacman2.0-main/`
        - 📝 Game Logic: `pacman.py`
        - 🎨 Assets: Sprites & Fonts
        - 🔊 Audio: Pygame mixer
        
        **Tính Năng:**
        - ✅ Chơi Manual (Keyboard control)
        - ✅ AI Ghosts (Minimax algorithm)
        - ✅ Genetic Algorithm training
        - ✅ Sound effects
        """)


if __name__ == "__main__":
    render_pacman_game()
