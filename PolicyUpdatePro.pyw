#!/usr/bin/env python
"""
PolicyUpdate Pro - Modern GUI Launcher
Double-click to launch the professional interface
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

def main():
    try:
        from gui.modern_app import PolicyUpdatePro, CUSTOMTKINTER_AVAILABLE

        if not CUSTOMTKINTER_AVAILABLE:
            # Fall back to installing
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "customtkinter", "pillow"], check=True)

            # Try again
            from gui.modern_app import PolicyUpdatePro

        app = PolicyUpdatePro()
        app.mainloop()

    except Exception as e:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("PolicyUpdate Pro Error", f"Failed to start:\n\n{e}\n\nTry running: pip install customtkinter pillow")
            root.destroy()
        except:
            print(f"Error: {e}")
            input("Press Enter to exit...")

if __name__ == '__main__':
    main()
