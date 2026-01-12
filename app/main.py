"""
Gaming Cafe Manager - Main Application Entry Point

A Windows-only desktop application for managing gaming cafe sessions.
Built with Python, Tkinter, and SQLite.
"""

import sys
from pathlib import Path

# Add workspace root to path so imports work correctly
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

import tkinter as tk
from tkinter import messagebox
from app.ui.main_window import MainWindow


def main():
    """Initialize and start the application."""
    try:
        # Create root window
        root = tk.Tk()
        root.title("Gaming Cafe Manager")
        root.geometry("800x600")
        
        # Initialize main UI
        app = MainWindow(root)
        
        # Start event loop
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application:\n{str(e)}")
        raise


if __name__ == "__main__":
    main()
