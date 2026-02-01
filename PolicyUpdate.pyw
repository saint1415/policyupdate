#!/usr/bin/env python
"""
PolicyUpdate - Windows GUI Launcher
Double-click this file to launch the application
(.pyw extension runs without console window on Windows)
"""

import sys
import os
from pathlib import Path

# Set up paths
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

def main():
    try:
        from gui.main_window import PolicyUpdateGUI, TKINTER_AVAILABLE

        if not TKINTER_AVAILABLE:
            import tkinter.messagebox as mb
            mb.showerror("Error", "tkinter is not available.\nPlease install Python with tkinter support.")
            return

        app = PolicyUpdateGUI()
        app.run()

    except Exception as e:
        # Show error in GUI if possible
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("PolicyUpdate Error", f"Failed to start application:\n\n{e}")
            root.destroy()
        except:
            print(f"Error: {e}")
            input("Press Enter to exit...")

if __name__ == '__main__':
    main()
