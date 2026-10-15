# 🎮 Pacman 2.0 Integration Guide

## Overview

Integrating the original **Pacman2.0-main** Pygame game into the XRL Streamlit dashboard. This allows users to play the classic game directly from the dashboard interface.

## Quick Start

### Method 1: Play Game Tab in Dashboard
```bash
streamlit run src/dashboard.py
```
Then select **"Play Game"** tab and click **"▶️ Bắt Đầu Game"**

### Method 2: Standalone Game Launcher
```bash
streamlit run launch_pacman_game.py
```

### Method 3: Direct Pygame Game
```bash
python Pacman2.0-main/main.py
```

## Features

### ✅ Game Features
- **Original Pygame Implementation**: Full features from Pacman2.0-main
- **AI Ghosts**: 4 intelligent ghosts with different behaviors
  - 🔴 **Blinky**: Aggressive pursuer
  - 🩷 **Pinky**: Ambush specialist
  - 🩵 **Inky**: Unpredictable
  - 🟠 **Clyde**: Random

- **Sound Effects**: Complete audio system
  - Background music
  - Waka-waka pellet sounds
  - Power-up eating sound
  - Ghost eaten sound
  - Death sound
  - Level complete sound

- **Multiple Levels**: Progressive difficulty
- **Power-Ups**: Make ghosts vulnerable
- **Score System**: Track high scores

### ✅ Integration Features
- **One-Click Launch**: Start game from dashboard
- **Process Management**: Automatically manages game window
- **Status Tracking**: See if game is running
- **Full Documentation**: Built-in guides and controls

## Controls

| Key | Action |
|-----|--------|
| **W** | Move Up ⬆️ |
| **A** | Move Left ⬅️ |
| **S** | Move Down ⬇️ |
| **D** | Move Right ➡️ |
| **START** | Begin game (in start screen) |
| **ESC** | Quit game |

## Architecture

### File Structure
```
project-xrl-mspacman/
├── src/
│   └── pacman_game_integration.py    # Streamlit wrapper (397 lines)
│
├── Pacman2.0-main/                   # Original Pygame game
│   ├── main.py                       # Start screen
│   ├── pacman.py                     # Game logic & classes
│   ├── genetic_algorithim.py         # AI training
│   ├── assets/
│   │   ├── sprites/                  # Game sprites
│   │   ├── sounds/                   # Audio files (.wav)
│   │   └── fonts/                    # Game fonts
│   └── ...
│
└── launch_pacman_game.py             # Direct launcher script
```

### How It Works

```
┌─────────────────────────────────────────────────────┐
│ Streamlit Dashboard (dashboard.py)                  │
│ - UI Components                                     │
│ - Tab Navigation                                    │
│ - Session Management                                │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ Pacman Game Integration (pacman_game_integration.py)│
│ - Game Launcher                                     │
│ - Process Management                                │
│ - Control Interface                                 │
└────────────────┬────────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────────┐
│ Subprocess (Pygame Window)                          │
│ - main.py (Start Screen)                            │
│ - pacman.py (Game Engine)                           │
│ - Graphics & Sound                                  │
└─────────────────────────────────────────────────────┘
```

### Integration Code

**In dashboard.py:**
```python
if view == "Play Game":
    from pacman_game_integration import create_game_tab
    create_game_tab()
    return
```

**Starting the game:**
```python
st.session_state.game_process = subprocess.Popen(
    [sys.executable, str(PACMAN_MAIN)],
    cwd=str(PACMAN_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
```

## Gameplay Guide

### Objective
- 🟡 Collect all pellets (white dots)
- 👻 Avoid ghosts (or eat them with power-ups)
- ⭐ Reach next level by clearing the board
- 🏆 Achieve high score

### Strategy Tips

**Basic:**
1. Learn the maze layout
2. Find safe zones (corners)
3. Plan escape routes
4. Avoid traps

**Advanced:**
1. Use power-ups strategically
2. Bait ghosts into patterns
3. Control ghost spawning locations
4. Memorize optimal pellet routes

### Difficulty Levels
- **Level 1**: Easy - Slow ghosts, easy patterns
- **Level 2-3**: Medium - Faster movement, smarter AI
- **Level 4+**: Hard - Very fast, complex ghost coordination

## Technical Details

### System Requirements
- **Python**: 3.8+
- **Pygame**: 2.5.0+
- **Display**: Support for 672×930 px window
- **Audio**: Working speakers/headphones (optional)

### Game Specifications
- **Resolution**: 672×930 pixels (28×31 cells @ 3x scale)
- **FPS**: 60 frames per second
- **Cell Size**: 8×8 pixels base (24×24 scaled)
- **Sprite Sheet**: `Arcade - Pac-Man - General Sprites.png`
- **Font**: `PressStart2P-vaV7.ttf` (Arcade font)

### Dependencies
```
pygame>=2.5.0
psutil>=5.8.0  # For process management
streamlit>=1.24.0
```

### Memory Usage
- Game window: ~100-150 MB
- Per frame: <50 MB
- Total: ~200 MB when running

## Troubleshooting

### Game Won't Start

**Problem**: Button click does nothing
- **Solution**: Check if pygame is installed: `pip install pygame`
- **Solution**: Ensure `Pacman2.0-main/main.py` exists
- **Solution**: Check game folder path in code

**Problem**: "File not found" error
- **Solution**: Verify folder structure is correct
- **Solution**: Check all required files exist:
  - `main.py`, `pacman.py`
  - Sprite sheet PNG file
  - Font TTF file

### No Sound

**Problem**: Game runs but no audio
- **Solution**: Check volume settings in OS
- **Solution**: Verify `.wav` files exist in game directory
- **Solution**: Try restarting Streamlit app

### Game Crashes

**Problem**: Game freezes or crashes
- **Solution**: Close other applications
- **Solution**: Check system resources (Task Manager)
- **Solution**: Update GPU drivers
- **Solution**: Try standalone: `python Pacman2.0-main/main.py`

### Controls Not Working

**Problem**: Game doesn't respond to keyboard
- **Solution**: Click inside game window first
- **Solution**: Ensure NumLock is off
- **Solution**: Try different keyboard layout

### High CPU Usage

**Problem**: Game uses too much CPU
- **Solution**: Reduce resolution in settings
- **Solution**: Lower FPS if game supports it
- **Solution**: Close background applications

## Customization

### Modify Colors
Edit in `pacman.py`:
```python
PACMAN_COLOR = (255, 255, 0)  # Yellow
GHOST_COLORS = [(255, 0, 0), ...]  # Red, Pink, Cyan, Orange
```

### Change Difficulty
Modify ghost speeds and AI patterns in `pacman.py`

### Add New Levels
Create new maze layouts in game data

### Customize Controls
Edit key mappings in game event handler

## Performance Optimization

### For Better Performance
1. **Reduce graphic quality**: Simpler sprites
2. **Lower FPS**: 30 instead of 60
3. **Disable effects**: Remove visual effects
4. **Optimize ghost AI**: Simpler algorithms

### For Better Experience
1. **Increase FPS**: 120 if system supports
2. **Higher resolution**: If display allows
3. **Better audio**: High-quality sound files
4. **Full-screen**: Better immersion

## Known Limitations

- ⚠️ Game runs in separate window (not embedded in dashboard)
- ⚠️ No direct save/load within Streamlit UI
- ⚠️ Game state not synchronized with dashboard
- ⚠️ Limited interaction with other dashboard features during gameplay

## Future Enhancements

### Planned Features
- [ ] Embed game using Pygame Surface capture
- [ ] Save replay functionality
- [ ] Leaderboard integration
- [ ] Network multiplayer
- [ ] Custom skin/theme support

### Experimental
- [ ] AI agent control (DQN)
- [ ] Training visualization
- [ ] Real-time attention overlay
- [ ] Live replay analysis

## Credits

- **Original Game**: Pacman2.0-main repository
- **Pygame**: Official Pygame library
- **Integration**: XRL Team
- **Framework**: Streamlit

## License

This integration maintains the original Pacman2.0-main license.
Streamlit wrapper is part of the XRL project.

---

**Version**: 1.0
**Last Updated**: October 15, 2026
**Status**: ✅ Production Ready
