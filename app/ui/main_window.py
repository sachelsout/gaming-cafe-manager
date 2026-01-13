"""Main application window."""

import tkinter as tk
from tkinter import ttk
from app.ui.styles import COLORS, configure_dark_theme
from app.ui.dashboard import Dashboard
from app.db.connection import DatabaseConnection


class MainWindow:
    """Main application window for Gaming Cafe Manager."""
    
    def __init__(self, root, db: DatabaseConnection):
        """
        Initialize the main window.
        
        Args:
            root: tkinter root window
            db: DatabaseConnection instance
        """
        self.root = root
        self.db = db
        self._setup_theme()
        self._setup_ui()
    
    def _setup_theme(self):
        """Configure dark theme for the application."""
        # Set window background
        self.root.configure(bg=COLORS["bg_dark"])
        
        # Configure ttk styles
        configure_dark_theme()
    
    def _setup_ui(self):
        """Set up the main UI components."""
        # Create main dashboard first
        self.dashboard = Dashboard(self.root, self.db)
        
        # Create menu bar (needs dashboard reference)
        self._create_menu()
    
    def _create_menu(self):
        """Create menu bar with basic options."""
        menubar = tk.Menu(self.root, bg=COLORS["bg_card"], fg=COLORS["text_primary"])
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, bg=COLORS["bg_card"], fg=COLORS["text_primary"], tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, bg=COLORS["bg_card"], fg=COLORS["text_primary"], tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh Dashboard", command=self.dashboard.refresh)
        
        # Help menu
        help_menu = tk.Menu(menubar, bg=COLORS["bg_card"], fg=COLORS["text_primary"], tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _show_about(self):
        """Show about dialog."""
        from tkinter import messagebox
        messagebox.showinfo(
            "About Gaming Cafe Manager",
            "Gaming Cafe Manager v1.0\n\n"
            "A Windows desktop application for managing gaming cafe sessions.\n"
            "Built with Python, Tkinter, and SQLite."
        )
