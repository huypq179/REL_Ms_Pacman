"""
Visual ASCII Preview of the Pacman Game
This shows how the game looks in the dashboard
"""

GAME_PREVIEW = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                  XRL Ms-Pacman Agent Comparison                           ║
║          Real-time visualization: Baseline DQN vs Explainable             ║
║                                                                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║   ┌─────────┬─────────┬─────────┐                                        ║
║   │ Baseline│Explainabl│  Live   │                                       ║
║   │  Ready  │  Ready   │ Mode    │                                       ║
║   └─────────┴─────────┴─────────┘                                        ║
║                                                                           ║
║   ⚪ Live Game    ⚫ Play Game    ⚪ Comparison                           ║
║   ═══════════════════════════════════════════════════════                ║
║                                                                           ║
║   ┌────────────────────────────────────────────────────────────────────┐ ║
║   │                  🎮 Interactive Pacman Game                        │ ║
║   │        Play the classic Pacman game directly in the dashboard      │ ║
║   └────────────────────────────────────────────────────────────────────┘ ║
║                                                                           ║
║   ┌──────────────────┬──────────────────┬──────────────────┐            ║
║   │  🎮 PLAY CLASSIC │  🤖 WATCH AI    │  📊 STATISTICS   │            ║
║   └──────────────────┴──────────────────┴──────────────────┘            ║
║                                                                           ║
║   Classic Pacman Gameplay                                                ║
║   🎯 Use arrow keys to control Pacman. Eat all pellets while avoiding   ║
║      ghosts!                                                             ║
║                                                                           ║
║   ┌────────────────────────────────────────────────────────────────────┐ ║
║   │                                                                    │ ║
║   │                                                                    │ ║
║   │         ┌──────────────────────────────────────────┐              │ ║
║   │         │                                          │              │ ║
║   │         │  · · · · · · · · · · · · · · · · · ·   │              │ ║
║   │         │  · ┌──┐ · ┌──────────────┐ · ┌──┐ ·   │              │ ║
║   │         │  · │  │ · │              │ · │  │ ·   │              │ ║
║   │         │  · └──┘ · └──┐      ┌────┘ · └──┘ ·   │              │ ║
║   │         │  · · · · · · · · · · · · · · · · · ·   │              │ ║
║   │         │  · ┌──────┐ · · · · · ┌──────┐ · ·   │              │ ║
║   │         │  · │      │ · ┌────┐ · │      │ · ·   │              │ ║
║   │         │  · │      │ · │ 👻 │ · │      │ · ·   │              │ ║
║   │         │  · └──────┘ · │👻👻│ · └──────┘ · ·   │              │ ║
║   │         │  · · · · · · · └────┘ · · · · · · ·   │              │ ║
║   │         │  · ┌────┐ · · · · · · · ┌────┐ · ·   │              │ ║
║   │         │  · │    │ · ┌────────┐ · │    │ · ·   │              │ ║
║   │         │  · │    │ · │        │ · │    │ · ·   │              │ ║
║   │         │  · └────┘ · └────────┘ · └────┘ · ·   │              │ ║
║   │         │  · · · · · · · 🟡 · · · · · · · · ·   │              │ ║
║   │         │  · · · · · · · · · · · · · · · · · ·   │              │ ║
║   │         │                                          │              │ ║
║   │         └──────────────────────────────────────────┘              │ ║
║   │                                                                    │ ║
║   └────────────────────────────────────────────────────────────────────┘ ║
║                                                                           ║
║   ┌────────┬────────┬────────┬────────┐                                 ║
║   │ Score  │ Lives  │ Level  │ Time   │                                 ║
║   │   0    │   3    │   1    │ 00:00  │                                 ║
║   └────────┴────────┴────────┴────────┘                                 ║
║                                                                           ║
║   [ ▶️ Start Game ]  [ ⏸️ Pause ]  [ 🔄 Reset ]                         ║
║                                                                           ║
║   ┌────────────────────────────────────────┐                            ║
║   │ 🎯 Controls                            │                            ║
║   │ ⬆️ Arrow Up    - Move Up              │                            ║
║   │ ⬇️ Arrow Down  - Move Down            │                            ║
║   │ ⬅️ Arrow Left  - Move Left            │                            ║
║   │ ➡️ Arrow Right - Move Right           │                            ║
║   │ ⏸️ Spacebar    - Pause Game           │                            ║
║   └────────────────────────────────────────┘                            ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

ELEMENTS:
  🟡 = Pacman (you!)
  👻 = Ghosts (Red: Blinky, Pink: Pinky, Cyan: Inky, Orange: Clyde)
  · = Pellets (collect for points)
  
SCORING:
  Regular Pellet: +10 points
  Ghost Collision: -1 life
  All Pellets: Next level
  
CONTROLS:
  Arrow Keys: Movement
  Spacebar: Pause
  
FEATURES:
  ✓ 60 FPS smooth gameplay
  ✓ Real-time collision detection
  ✓ Professional dark theme UI
  ✓ Live score tracking
  ✓ Statistics and charts
"""

def print_preview():
    print(GAME_PREVIEW)

if __name__ == "__main__":
    print_preview()
