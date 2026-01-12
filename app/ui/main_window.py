"""Main application window."""

import tkinter as tk
from tkinter import ttk


class MainWindow:
    """Main application window for Gaming Cafe Manager."""
    
    def __init__(self, root):
        """
        Initialize the main window.
        
        Args:
            root: tkinter root window
        """
        self.root = root
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the initial UI components."""
        # Create a simple label as placeholder
        label = ttk.Label(
            self.root,
            text="Gaming Cafe Manager\n\nApplication initialized successfully",
            font=("Arial", 14),
            justify=tk.CENTER
        )
        label.pack(expand=True)
        
        # Create a frame for future menu or buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)
        
        quit_btn = ttk.Button(
            button_frame,
            text="Exit",
            command=self.root.quit
        )
        quit_btn.pack(side=tk.LEFT, padx=5)
