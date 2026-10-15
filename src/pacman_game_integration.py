"""
Streamlit integration for Pacman2.0-main Pygame game
Launches the original Pygame game in a separate window from dashboard
"""

import streamlit as st
import subprocess
import sys
import os
from pathlib import Path
import time
import psutil

# Path to Pacman2.0-main
PACMAN_DIR = Path(__file__).parent.parent / "Pacman2.0-main"
PACMAN_MAIN = PACMAN_DIR / "main.py"


def render_pacman_game_launcher():
    """Render launcher for Pacman2.0 game"""
    
    # Initialize session state
    if 'game_process' not in st.session_state:
        st.session_state.game_process = None
    if 'game_running' not in st.session_state:
        st.session_state.game_running = False
    
    # Custom CSS
    st.markdown("""
    <style>
    .game-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border: 2px solid #10b981;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.1);
    }
    .game-title {
        color: #10b981;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 12px;
        text-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
    }
    .game-subtitle {
        color: #9ca3af;
        font-size: 1em;
        margin-bottom: 8px;
    }
    .info-box {
        background: #1a1f2e;
        border: 1px solid #374151;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
    }
    .control-key {
        background: #10b981;
        color: #0f172a;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
        margin: 4px;
    }
    .status-running {
        color: #10b981;
        font-weight: bold;
    }
    .status-stopped {
        color: #ef4444;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="game-header">
        <div class="game-title">🎮 Pacman 2.0 - Original Game</div>
        <div class="game-subtitle">Pygame Game Integration | Full Features</div>
        <div class="game-subtitle">🎯 AI Ghosts | 🔊 Sound Effects | 🏆 Classic Gameplay</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎮 Chơi Game", "📖 Hướng Dẫn", "📊 Thông Tin", "⚙️ Cài Đặt"])
    
    with tab1:
        st.markdown("### 🕹️ Điều Khiển Game")
        
        # Check if game exists
        if not PACMAN_MAIN.exists():
            st.error(f"❌ Không tìm thấy game tại: `{PACMAN_MAIN}`")
            st.info("ℹ️ Đảm bảo folder `Pacman2.0-main` tồn tại với file `main.py`")
            return
        
        # Game status
        if st.session_state.game_running and st.session_state.game_process:
            try:
                process = psutil.Process(st.session_state.game_process.pid)
                if process.is_running():
                    status_html = '<p class="status-running">🟢 Game đang chạy...</p>'
                else:
                    status_html = '<p class="status-stopped">🔴 Game đã dừng</p>'
                    st.session_state.game_running = False
            except (psutil.NoSuchProcess, AttributeError):
                status_html = '<p class="status-stopped">🔴 Game đã dừng</p>'
                st.session_state.game_running = False
        else:
            status_html = '<p class="status-stopped">⚪ Game chưa chạy</p>'
        
        st.markdown(f'<div class="info-box">{status_html}</div>', unsafe_allow_html=True)
        
        # Control buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Bắt Đầu Game", key="start_game", use_container_width=True, 
                        disabled=st.session_state.game_running):
                try:
                    # Launch game in separate window
                    st.session_state.game_process = subprocess.Popen(
                        [sys.executable, str(PACMAN_MAIN)],
                        cwd=str(PACMAN_DIR),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    st.session_state.game_running = True
                    st.success("✅ Game đã khởi động! Kiểm tra cửa sổ game.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi khi khởi động game: {e}")
        
        with col2:
            if st.button("🔄 Khởi Động Lại", key="restart_game", use_container_width=True):
                # Stop current game
                if st.session_state.game_process:
                    try:
                        st.session_state.game_process.terminate()
                        st.session_state.game_process.wait(timeout=3)
                    except:
                        st.session_state.game_process.kill()
                
                st.session_state.game_running = False
                time.sleep(0.5)
                
                # Start new game
                try:
                    st.session_state.game_process = subprocess.Popen(
                        [sys.executable, str(PACMAN_MAIN)],
                        cwd=str(PACMAN_DIR),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    st.session_state.game_running = True
                    st.success("✅ Game đã khởi động lại!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
        
        with col3:
            if st.button("⏹️ Dừng Game", key="stop_game", use_container_width=True,
                        disabled=not st.session_state.game_running):
                if st.session_state.game_process:
                    try:
                        st.session_state.game_process.terminate()
                        st.session_state.game_process.wait(timeout=3)
                        st.success("✅ Game đã dừng")
                    except:
                        st.session_state.game_process.kill()
                        st.warning("⚠️ Force killed game process")
                    finally:
                        st.session_state.game_running = False
                        st.rerun()
        
        # Instructions
        st.markdown("""
        <div class="info-box">
            <h4 style="color: #10b981; margin-top: 0;">🎯 Cách Chơi:</h4>
            <ol style="color: #d1d5db;">
                <li>Nhấn nút <strong>"▶️ Bắt Đầu Game"</strong></li>
                <li>Một cửa sổ Pygame mới sẽ mở ra</li>
                <li>Trong cửa sổ game, nhấn <strong>"START"</strong></li>
                <li>Sử dụng phím <strong>W/A/S/D</strong> để điều khiển</li>
                <li>Ăn tất cả các viên mồi và tránh ma quái!</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Preview image
        st.markdown("### 📸 Preview")
        st.image("https://via.placeholder.com/672x840/0f172a/10b981?text=Pacman+Game+Window", 
                caption="Game sẽ mở trong cửa sổ riêng", use_column_width=True)
    
    with tab2:
        st.markdown("### 📖 Hướng Dẫn Chi Tiết")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-box">
                <h4 style="color: #10b981;">⌨️ Phím Điều Khiển</h4>
                <div style="text-align: center; margin-top: 16px;">
                    <span class="control-key">W</span> Lên ⬆️<br>
                    <span class="control-key">A</span> Trái ⬅️
                    <span class="control-key">D</span> Phải ➡️<br>
                    <span class="control-key">S</span> Xuống ⬇️
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-box">
                <h4 style="color: #10b981;">🎮 Gameplay</h4>
                <ul>
                    <li>🟡 <strong>Pacman</strong>: Nhân vật chính</li>
                    <li>⚪ <strong>Viên mồi</strong>: Ăn để ghi điểm</li>
                    <li>⭐ <strong>Power-up</strong>: Gọc ma quái</li>
                    <li>👻 <strong>Ma quái</strong>: Tránh hoặc gọc</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🎯 Chiến Thuật Chơi Game
        
        **Cơ Bản:**
        1. **Thu thập viên mồi** - Ưu tiên ăn hết tất cả các viên nhỏ
        2. **Tránh ma quái** - Giữ khoảng cách an toàn với các con ma
        3. **Sử dụng Power-up** - Ăn viên to để truy đuổi ma quái ngược lại
        4. **Lên level** - Hoàn thành màn để tăng độ khó
        
        **Nâng Cao:**
        - **Góc bản đồ** - Sử dụng các góc để tránh ma quái
        - **Pattern** - Học các đường đi tối ưu
        - **Timing** - Đợi thời điểm đúng để đi qua ma quái
        - **Power-up strategy** - Không vội ăn power-up, để dành khi cần
        
        ### 👻 Về Các Ma Quái
        
        **4 loại ma quái với AI khác nhau:**
        
        1. **🔴 Blinky (Red Ghost)**
           - Tính cách: Hung hãn, đuổi theo trực tiếp
           - Chiến thuật: Luôn đuổi theo vị trí hiện tại của Pacman
           
        2. **🩷 Pinky (Pink Ghost)**
           - Tính cách: Chiến lược, chặn đường
           - Chiến thuật: Dự đoán vị trí Pacman sắp đến
           
        3. **🩵 Inky (Cyan Ghost)**
           - Tính cách: Phối hợp với Blinky
           - Chiến thuật: Tấn công từ góc không ngờ
           
        4. **🟠 Clyde (Orange Ghost)**
           - Tính cách: Ngẫu nhiên, khó đoán
           - Chiến thuật: Thỉnh thoảng đuổi, thỉnh thoảng chạy
        """)
    
    with tab3:
        st.markdown("### 📊 Thông Tin Game")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.markdown("""
            <div class="info-box">
                <h4 style="color: #10b981;">🎮 Thông Số Kỹ Thuật</h4>
                <ul>
                    <li><strong>Phiên bản:</strong> Pacman 2.0</li>
                    <li><strong>Framework:</strong> Pygame</li>
                    <li><strong>Độ phân giải:</strong> 672×930 px</li>
                    <li><strong>FPS:</strong> 60</li>
                    <li><strong>Cells:</strong> 28×31</li>
                    <li><strong>Scale:</strong> 3x</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with info_col2:
            st.markdown("""
            <div class="info-box">
                <h4 style="color: #10b981;">📁 Cấu Trúc File</h4>
                <ul>
                    <li><code>main.py</code> - Start screen</li>
                    <li><code>pacman.py</code> - Game logic</li>
                    <li><code>genetic_algorithim.py</code> - AI</li>
                    <li><code>assets/</code> - Sprites & Audio</li>
                    <li><code>PressStart2P.ttf</code> - Font</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""
        ### 🔊 Âm Thanh
        
        Game có đầy đủ hiệu ứng âm thanh:
        - 🎵 **Background music** - Nhạc nền kinh điển
        - 🎶 **Waka waka** - Tiếng ăn viên mồi
        - 💀 **Death sound** - Tiếng chết
        - 👻 **Eat ghost** - Tiếng ăn ma quái
        - 🍒 **Eat fruit** - Tiếng ăn trái cây
        - 😱 **Frightened mode** - Nhạc khi ma quái sợ hãi
        - 🏁 **Startup** - Tiếng bắt đầu game
        - 🎉 **Win** - Tiếng thắng cuộc
        """)
        
        # File path info
        st.markdown("### 📂 Đường Dẫn")
        st.code(f"""
Game Directory: {PACMAN_DIR}
Main File: {PACMAN_MAIN}
Exists: {PACMAN_MAIN.exists()}
        """)
    
    with tab4:
        st.markdown("### ⚙️ Cài Đặt & Requirements")
        
        st.markdown("""
        <div class="info-box">
            <h4 style="color: #10b981;">📦 Dependencies</h4>
            <p>Game cần các thư viện sau:</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.code("""
# Core
pygame>=2.5.0

# Optional (for AI features)
numpy
heapq (built-in)
        """, language="text")
        
        st.markdown("### 🔧 Cài Đặt Pygame")
        
        if st.button("📥 Cài Đặt Pygame", use_container_width=True):
            with st.spinner("Đang cài đặt pygame..."):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "pygame"],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        st.success("✅ Pygame đã được cài đặt thành công!")
                        st.code(result.stdout)
                    else:
                        st.error(f"❌ Lỗi cài đặt:\n{result.stderr}")
                except Exception as e:
                    st.error(f"❌ Lỗi: {e}")
        
        # Check pygame
        try:
            import pygame as pyg
            st.success(f"✅ Pygame đã được cài đặt: version {pyg.version.ver}")
        except ImportError:
            st.warning("⚠️ Pygame chưa được cài đặt. Nhấn nút bên trên để cài đặt.")
        
        st.markdown("""
        ### 🐛 Troubleshooting
        
        **Game không khởi động:**
        1. Kiểm tra pygame đã cài đặt chưa
        2. Đảm bảo folder `Pacman2.0-main` tồn tại
        3. Kiểm tra file `main.py` có trong folder
        4. Thử chạy trực tiếp: `python Pacman2.0-main/main.py`
        
        **Không có âm thanh:**
        - Kiểm tra các file `.wav` trong folder game
        - Đảm bảo pygame.mixer được khởi tạo
        
        **Game lag:**
        - Đóng các ứng dụng khác
        - Kiểm tra CPU usage
        - Restart computer
        """)


def create_game_tab():
    """Main function to create the game tab - Compatible with dashboard"""
    render_pacman_game_launcher()


if __name__ == "__main__":
    st.set_page_config(
        page_title="Pacman 2.0 Game",
        page_icon="🎮",
        layout="wide"
    )
    render_pacman_game_launcher()
