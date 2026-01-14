"""Main application window."""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from app.ui.styles import COLORS, configure_dark_theme
from app.ui.dashboard import Dashboard
from app.db.connection import DatabaseConnection
from app.utils.session_timer import SessionTimerManager


class MainWindow:
    """Main application window for Gaming Cafe Manager."""
    
    def __init__(self, root, db: DatabaseConnection, db_path: Path = None):
        """
        Initialize the main window.
        
        Args:
            root: tkinter root window
            db: DatabaseConnection instance
            db_path: Path to the database file (for backup functionality)
        """
        self.root = root
        self.db = db
        self.db_path = db_path or db.db_path
        
        # Initialize session timer manager
        self.timer_manager = SessionTimerManager(
            on_warning=self._on_session_warning,
            on_time_up=self._on_session_time_up
        )
        
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
        self.dashboard = Dashboard(self.root, self.db, self.timer_manager)
        
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
        
        # Reports menu
        reports_menu = tk.Menu(menubar, bg=COLORS["bg_card"], fg=COLORS["text_primary"], tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Session History & Revenue", command=self._open_session_history)
        
        # Data menu (for backup/restore)
        data_menu = tk.Menu(menubar, bg=COLORS["bg_card"], fg=COLORS["text_primary"], tearoff=0)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Backup & Restore Database", command=self._open_backup_manager)
        data_menu.add_separator()
        data_menu.add_command(label="Create Quick Backup", command=self._create_quick_backup)
        
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
    
    def _open_session_history(self):
        """Open the session history and revenue summary dialog."""
        from app.ui.dialogs.session_history_dialog import SessionHistoryDialog
        SessionHistoryDialog(self.root, self.db)
    
    def _open_backup_manager(self):
        """Open the backup manager dialog."""
        from app.ui.dialogs.backup_dialog import BackupManagerDialog
        BackupManagerDialog(self.root, self.db_path)
    
    def _create_quick_backup(self):
        """Create a quick backup without opening the dialog."""
        from tkinter import messagebox
        from app.db.path_manager import DatabaseBackupManager
        
        try:
            backup_manager = DatabaseBackupManager(self.db_path)
            backup_path = backup_manager.create_backup(description="Quick backup via menu")
            messagebox.showinfo(
                "Backup Created",
                f"Backup saved successfully:\n{backup_path.name}"
            )
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Failed to create backup:\n{str(e)}")
    
    def _on_session_warning(self, message: str):
        """Handle session warning notification."""
        # Show warning popup
        messagebox.showwarning("Session Time Warning", message)
        # Also refresh dashboard to show updated times
        self.root.after(100, self.dashboard.refresh)
    
    def _on_session_time_up(self, message: str):
        """Handle session time-up notification."""
        # Show critical notification
        messagebox.showwarning("Session Time Exceeded", message)
        # Refresh dashboard
        self.root.after(100, self.dashboard.refresh)
    
    def cleanup(self):
        """Clean up resources before closing."""
        self.timer_manager.stop_all()
