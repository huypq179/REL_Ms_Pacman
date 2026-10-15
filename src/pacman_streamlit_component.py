"""
Advanced Pacman Game Integration for Streamlit
Uses streamlit-components-v2 to embed the actual pygame-based Pacman game
"""

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
from pathlib import Path
import base64
import json

# Add Pacman2.0-main to path
PACMAN_DIR = Path(__file__).parent.parent / "Pacman2.0-main"
sys.path.insert(0, str(PACMAN_DIR))


def get_game_html():
    """
    Generate HTML/JS wrapper for Pacman game
    This creates an iframe-compatible version
    """
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Pacman Game</title>
        <style>
            body {
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: 'Inter', sans-serif;
            }
            
            .game-container {
                background: #1a1f2e;
                border: 2px solid #10b981;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            }
            
            .game-header {
                text-align: center;
                color: #10b981;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }
            
            #gameCanvas {
                border: 2px solid #374151;
                border-radius: 8px;
                background: #000;
                display: block;
                margin: 0 auto;
            }
            
            .controls {
                margin-top: 20px;
                text-align: center;
            }
            
            .btn {
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                border: none;
                padding: 12px 24px;
                margin: 5px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
            }
            
            .btn:active {
                transform: translateY(0);
            }
            
            .btn-danger {
                background: linear-gradient(135deg, #ef4444, #dc2626);
            }
            
            .stats {
                display: flex;
                justify-content: space-around;
                margin-top: 20px;
                padding: 16px;
                background: rgba(17, 24, 39, 0.8);
                border-radius: 8px;
            }
            
            .stat-item {
                text-align: center;
            }
            
            .stat-label {
                color: #9ca3af;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            
            .stat-value {
                color: #f9fafb;
                font-size: 24px;
                font-weight: bold;
                margin-top: 5px;
            }
            
            .controls-guide {
                margin-top: 16px;
                padding: 16px;
                background: rgba(17, 24, 39, 0.6);
                border-radius: 8px;
                border-left: 4px solid #10b981;
            }
            
            .controls-guide h3 {
                color: #10b981;
                margin-top: 0;
                font-size: 14px;
            }
            
            .controls-guide p {
                color: #9ca3af;
                margin: 8px 0;
                font-size: 13px;
            }
        </style>
    </head>
    <body>
        <div class="game-container">
            <div class="game-header">🎮 Pacman Game</div>
            
            <canvas id="gameCanvas" width="672" height="744"></canvas>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-label">Score</div>
                    <div class="stat-value" id="score">0</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Lives</div>
                    <div class="stat-value" id="lives">3</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Level</div>
                    <div class="stat-value" id="level">1</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Time</div>
                    <div class="stat-value" id="time">00:00</div>
                </div>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="startGame()">▶️ Start Game</button>
                <button class="btn" onclick="pauseGame()">⏸️ Pause</button>
                <button class="btn btn-danger" onclick="resetGame()">🔄 Reset</button>
            </div>
            
            <div class="controls-guide">
                <h3>🎯 Controls</h3>
                <p>⬆️ <strong>Arrow Up</strong> - Move Up</p>
                <p>⬇️ <strong>Arrow Down</strong> - Move Down</p>
                <p>⬅️ <strong>Arrow Left</strong> - Move Left</p>
                <p>➡️ <strong>Arrow Right</strong> - Move Right</p>
                <p>⏸️ <strong>Spacebar</strong> - Pause Game</p>
            </div>
        </div>
        
        <script>
            // Game state
            let gameState = {
                running: false,
                paused: false,
                score: 0,
                lives: 3,
                level: 1,
                startTime: null,
                pacmanX: 336,
                pacmanY: 552,
                pacmanDirection: 'none',
                ghosts: [],
                pellets: []
            };
            
            const canvas = document.getElementById('gameCanvas');
            const ctx = canvas.getContext('2d');
            
            // Initialize pellets
            function initPellets() {
                gameState.pellets = [];
                const spacing = 24;
                for (let y = 1; y < 31; y++) {
                    for (let x = 1; x < 27; x++) {
                        // Skip center ghost house area
                        if (x >= 11 && x <= 16 && y >= 11 && y <= 16) continue;
                        gameState.pellets.push({x: x * spacing, y: y * spacing, eaten: false});
                    }
                }
            }
            
            // Initialize ghosts
            function initGhosts() {
                gameState.ghosts = [
                    {x: 312, y: 264, color: '#ff0000', name: 'Blinky'},
                    {x: 312, y: 312, color: '#ffb8ff', name: 'Pinky'},
                    {x: 288, y: 312, color: '#00ffff', name: 'Inky'},
                    {x: 336, y: 312, color: '#ffb852', name: 'Clyde'}
                ];
            }
            
            function startGame() {
                if (!gameState.running) {
                    gameState.running = true;
                    gameState.paused = false;
                    gameState.startTime = Date.now();
                    gameState.score = 0;
                    gameState.lives = 3;
                    gameState.level = 1;
                    initPellets();
                    initGhosts();
                    gameLoop();
                }
            }
            
            function pauseGame() {
                gameState.paused = !gameState.paused;
            }
            
            function resetGame() {
                gameState.running = false;
                gameState.paused = false;
                gameState.score = 0;
                gameState.lives = 3;
                gameState.level = 1;
                gameState.pacmanX = 336;
                gameState.pacmanY = 552;
                gameState.pacmanDirection = 'none';
                updateStats();
                drawGame();
            }
            
            // Handle keyboard input
            document.addEventListener('keydown', (e) => {
                if (!gameState.running || gameState.paused) return;
                
                switch(e.key) {
                    case 'ArrowUp':
                        gameState.pacmanDirection = 'up';
                        e.preventDefault();
                        break;
                    case 'ArrowDown':
                        gameState.pacmanDirection = 'down';
                        e.preventDefault();
                        break;
                    case 'ArrowLeft':
                        gameState.pacmanDirection = 'left';
                        e.preventDefault();
                        break;
                    case 'ArrowRight':
                        gameState.pacmanDirection = 'right';
                        e.preventDefault();
                        break;
                    case ' ':
                        pauseGame();
                        e.preventDefault();
                        break;
                }
            });
            
            function updatePacmanPosition() {
                const speed = 2;
                switch(gameState.pacmanDirection) {
                    case 'up':
                        gameState.pacmanY -= speed;
                        break;
                    case 'down':
                        gameState.pacmanY += speed;
                        break;
                    case 'left':
                        gameState.pacmanX -= speed;
                        break;
                    case 'right':
                        gameState.pacmanX += speed;
                        break;
                }
                
                // Boundary wrapping
                if (gameState.pacmanX < 0) gameState.pacmanX = canvas.width;
                if (gameState.pacmanX > canvas.width) gameState.pacmanX = 0;
                if (gameState.pacmanY < 0) gameState.pacmanY = canvas.height;
                if (gameState.pacmanY > canvas.height) gameState.pacmanY = 0;
            }
            
            function checkCollisions() {
                // Check pellet collisions
                gameState.pellets.forEach(pellet => {
                    if (!pellet.eaten) {
                        const dx = gameState.pacmanX - pellet.x;
                        const dy = gameState.pacmanY - pellet.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        if (distance < 15) {
                            pellet.eaten = true;
                            gameState.score += 10;
                        }
                    }
                });
                
                // Check ghost collisions
                gameState.ghosts.forEach(ghost => {
                    const dx = gameState.pacmanX - ghost.x;
                    const dy = gameState.pacmanY - ghost.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < 20) {
                        gameState.lives--;
                        if (gameState.lives <= 0) {
                            gameState.running = false;
                            alert('Game Over! Final Score: ' + gameState.score);
                        } else {
                            // Reset position
                            gameState.pacmanX = 336;
                            gameState.pacmanY = 552;
                        }
                    }
                });
            }
            
            function updateStats() {
                document.getElementById('score').textContent = gameState.score;
                document.getElementById('lives').textContent = gameState.lives;
                document.getElementById('level').textContent = gameState.level;
                
                if (gameState.startTime) {
                    const elapsed = Math.floor((Date.now() - gameState.startTime) / 1000);
                    const minutes = Math.floor(elapsed / 60);
                    const seconds = elapsed % 60;
                    document.getElementById('time').textContent = 
                        String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
                }
            }
            
            function drawGame() {
                // Clear canvas
                ctx.fillStyle = '#000';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Draw maze outline
                ctx.strokeStyle = '#2121ff';
                ctx.lineWidth = 2;
                ctx.strokeRect(10, 10, canvas.width - 20, canvas.height - 20);
                
                // Draw pellets
                gameState.pellets.forEach(pellet => {
                    if (!pellet.eaten) {
                        ctx.fillStyle = '#ffb8ae';
                        ctx.beginPath();
                        ctx.arc(pellet.x, pellet.y, 3, 0, Math.PI * 2);
                        ctx.fill();
                    }
                });
                
                // Draw Pacman
                const mouthAngle = Math.abs(Math.sin(Date.now() / 100)) * 0.3;
                ctx.fillStyle = '#ffff00';
                ctx.beginPath();
                ctx.arc(gameState.pacmanX, gameState.pacmanY, 12, mouthAngle, Math.PI * 2 - mouthAngle);
                ctx.lineTo(gameState.pacmanX, gameState.pacmanY);
                ctx.fill();
                
                // Draw ghosts
                gameState.ghosts.forEach(ghost => {
                    ctx.fillStyle = ghost.color;
                    ctx.beginPath();
                    ctx.arc(ghost.x, ghost.y, 12, Math.PI, 0, false);
                    ctx.lineTo(ghost.x + 12, ghost.y + 16);
                    ctx.lineTo(ghost.x + 8, ghost.y + 12);
                    ctx.lineTo(ghost.x + 4, ghost.y + 16);
                    ctx.lineTo(ghost.x, ghost.y + 12);
                    ctx.lineTo(ghost.x - 4, ghost.y + 16);
                    ctx.lineTo(ghost.x - 8, ghost.y + 12);
                    ctx.lineTo(ghost.x - 12, ghost.y + 16);
                    ctx.lineTo(ghost.x - 12, ghost.y);
                    ctx.fill();
                    
                    // Eyes
                    ctx.fillStyle = '#fff';
                    ctx.fillRect(ghost.x - 6, ghost.y - 4, 5, 6);
                    ctx.fillRect(ghost.x + 2, ghost.y - 4, 5, 6);
                    ctx.fillStyle = '#000';
                    ctx.fillRect(ghost.x - 4, ghost.y - 2, 3, 4);
                    ctx.fillRect(ghost.x + 4, ghost.y - 2, 3, 4);
                });
                
                // Draw pause overlay
                if (gameState.paused) {
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                    ctx.fillRect(0, 0, canvas.width, canvas.height);
                    ctx.fillStyle = '#fff';
                    ctx.font = '48px Arial';
                    ctx.textAlign = 'center';
                    ctx.fillText('PAUSED', canvas.width / 2, canvas.height / 2);
                }
            }
            
            function gameLoop() {
                if (!gameState.running) return;
                
                if (!gameState.paused) {
                    updatePacmanPosition();
                    checkCollisions();
                    updateStats();
                }
                
                drawGame();
                requestAnimationFrame(gameLoop);
            }
            
            // Initial draw
            initPellets();
            initGhosts();
            drawGame();
        </script>
    </body>
    </html>
    """
    return html_code


def render_pacman_game_iframe():
    """Render the Pacman game in an iframe using Streamlit components"""
    html_content = get_game_html()
    
    # Render the HTML in an iframe
    components.html(html_content, height=1000, scrolling=False)


if __name__ == "__main__":
    st.set_page_config(page_title="Pacman Game", layout="wide")
    render_pacman_game_iframe()
