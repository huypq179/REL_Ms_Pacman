# 🎮 Pacman Game Integration

## Overview

The XRL Ms-Pacman dashboard now includes an **interactive Pacman game** that can be played directly within the Streamlit interface!

## Features

### 1. **Play Classic Pacman** 🎯
- Fully playable Pacman game with canvas rendering
- Real-time score tracking, lives counter, and timer
- Smooth controls using arrow keys
- Pause/Resume functionality

### 2. **Watch AI Agent Play** 🤖
- Compare Baseline DQN vs Explainable DQN performance
- Real-time attention visualizations
- Adjustable playback speed
- Decision explanations overlay

### 3. **Game Statistics** 📊
- High score tracking
- Win rate analytics
- Score progression charts
- Performance metrics

## How to Access

### Method 1: Dashboard Tab
```bash
streamlit run src/dashboard.py
```

Then select **"Play Game"** from the view selector at the top.

### Method 2: Standalone Component
```bash
streamlit run src/pacman_streamlit_component.py
```

### Method 3: Game Tab Module
```bash
streamlit run src/pacman_game_streamlit.py
```

## Controls

| Key | Action |
|-----|--------|
| ⬆️ Arrow Up | Move Up |
| ⬇️ Arrow Down | Move Down |
| ⬅️ Arrow Left | Move Left |
| ➡️ Arrow Right | Move Right |
| ⏸️ Spacebar | Pause/Resume |

## Game Elements

- **Yellow Circle**: Pacman (you!)
- **Colored Ghosts**: 
  - 🔴 Blinky (Red) - Aggressive chaser
  - 🩷 Pinky (Pink) - Ambusher
  - 🩵 Inky (Cyan) - Unpredictable
  - 🧡 Clyde (Orange) - Random movement
- **Small Dots**: Regular pellets (+10 points each)

## Architecture

### File Structure
```
src/
├── dashboard.py                    # Main dashboard with game tab
├── pacman_game_streamlit.py        # Game tab wrapper
├── pacman_streamlit_component.py   # HTML5 Canvas game implementation
└── ...

Pacman2.0-main/                     # Original Pygame-based game
├── pacman.py                       # Game logic
├── main.py                         # Start screen
└── assets/                         # Game assets
```

### Technology Stack

- **Frontend**: Streamlit + HTML5 Canvas
- **Game Engine**: Custom JavaScript game loop
- **Rendering**: 2D Canvas API
- **State Management**: Streamlit session state

## Integration Details

### How It Works

1. **HTML5 Canvas Renderer**: The game is rendered using HTML5 Canvas embedded via `streamlit.components.v1.html()`
2. **JavaScript Game Loop**: Runs at 60 FPS using `requestAnimationFrame()`
3. **Collision Detection**: Real-time detection between Pacman, ghosts, and pellets
4. **State Synchronization**: Game state updates reflected in Streamlit metrics

### Code Example

```python
from src.pacman_game_streamlit import create_game_tab

# In your dashboard
create_game_tab()
```

## Customization

### Adjust Game Speed
Edit `pacman_streamlit_component.py`:
```javascript
const speed = 2;  // Change movement speed
```

### Modify Colors
Edit CSS variables in `get_game_html()`:
```css
--accent-green: #10b981;
--bg-card: #1a1f2e;
```

### Add Power Pellets
Add to the game state:
```javascript
gameState.powerPellets = [
    {x: 50, y: 50, active: true},
    // ...
];
```

## Performance

- **Frame Rate**: 60 FPS
- **Latency**: <16ms per frame
- **Memory**: ~50MB
- **Browser Compatibility**: Chrome, Firefox, Safari, Edge

## Future Enhancements

- [ ] Power pellets (make ghosts vulnerable)
- [ ] Multiple levels with increasing difficulty
- [ ] Sound effects integration
- [ ] Leaderboard system
- [ ] Multiplayer mode
- [ ] AI agent training visualization
- [ ] Save/load game state

## Troubleshooting

### Game Not Loading
1. Check browser console for errors (F12)
2. Ensure Streamlit version ≥1.24.0
3. Clear browser cache

### Controls Not Working
1. Click inside the game canvas first
2. Check if another element has focus
3. Try refreshing the page

### Performance Issues
1. Close other browser tabs
2. Reduce playback speed
3. Check system resources

## Credits

- Original Pacman2.0 implementation from `Pacman2.0-main/`
- Streamlit integration by XRL Team
- Canvas game engine custom-built for this project

## License

This integration is part of the XRL Ms-Pacman project.

---

**Enjoy playing!** 🎮✨
