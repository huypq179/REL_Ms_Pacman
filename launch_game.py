"""
Quick demo launcher for the Pacman game integration
Run this to see the game without launching the full dashboard
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("🎮 XRL Ms-Pacman - Game Demo Launcher")
    print("=" * 50)
    print()
    print("Choose a demo mode:")
    print()
    print("1. 🕹️  Play Classic Pacman (standalone)")
    print("2. 📊 Full Dashboard with all features")
    print("3. 🎯 Game Tab Only")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    project_root = Path(__file__).parent
    
    if choice == "1":
        print("\n🚀 Launching standalone Pacman game...")
        script = project_root / "src" / "pacman_streamlit_component.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(script)])
        
    elif choice == "2":
        print("\n🚀 Launching full dashboard...")
        print("   📌 After launch, select 'Play Game' tab")
        script = project_root / "src" / "dashboard.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(script)])
        
    elif choice == "3":
        print("\n🚀 Launching game tab module...")
        script = project_root / "src" / "pacman_game_streamlit.py"
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(script)])
        
    else:
        print("❌ Invalid choice. Please run again and select 1, 2, or 3.")
        sys.exit(1)

if __name__ == "__main__":
    main()
