"""Dialog for starting a planned session (transitioning from PLANNED to ACTIVE)."""

import tkinter as tk
from tkinter import ttk, messagebox
from app.ui.styles import COLORS, FONTS
from app.services.session_service import SessionService
from app.db.connection import DatabaseConnection
from app.utils.time_utils import get_current_time_12hr, parse_time_12hr
from app.utils.validators import validate_time_format
from app.ui.dialogs.error_dialog import show_validation_error, show_error, show_success


class StartPlannedSessionDialog:
    """Dialog for activating a planned gaming session."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, session_id: int, on_success=None):
        """
        Initialize start planned session dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            session_id: ID of the planned session to start
            on_success: Optional callback when session is started successfully
        """
        self.parent = parent
        self.db = db
        self.session_id = session_id
        self.session_service = SessionService(db)
        self.on_success = on_success
        
        # Fetch session
        self.session = self.session_service.get_session_by_id(session_id)
        if not self.session:
            messagebox.showerror("Error", f"Session {session_id} not found.")
            return
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Start Session - {self.session.customer_name}")
        self.dialog.geometry("400x250")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (250 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Session info section
        info_label = ttk.Label(container, text="Session Information", style="Heading.TLabel")
        info_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Customer name (read-only)
        customer_label = ttk.Label(container, text="Customer:", style="TLabel")
        customer_label.grid(row=1, column=0, sticky=tk.W)
        customer_value = ttk.Label(container, text=self.session.customer_name, style="TLabel")
        customer_value.grid(row=1, column=1, sticky=tk.W)
        
        # System (read-only)
        system_label = ttk.Label(container, text="System:", style="TLabel")
        system_label.grid(row=2, column=0, sticky=tk.W)
        system_value = ttk.Label(container, text=self.session.system_name, style="TLabel")
        system_value.grid(row=2, column=1, sticky=tk.W)
        
        # Planned duration (read-only)
        duration_label = ttk.Label(container, text="Planned Duration:", style="TLabel")
        duration_label.grid(row=3, column=0, sticky=tk.W)
        duration_hours = self.session.planned_duration_min / 60 if self.session.planned_duration_min else 0
        duration_value = ttk.Label(container, text=f"{duration_hours:.1f} hours", style="TLabel")
        duration_value.grid(row=3, column=1, sticky=tk.W)
        
        # Login time
        login_label = ttk.Label(container, text="Login Time *", style="Heading.TLabel")
        login_label.grid(row=4, column=0, sticky=tk.W, pady=(15, 5))
        
        self.login_time_var = tk.StringVar(value=get_current_time_12hr())
        login_entry = ttk.Entry(container, textvariable=self.login_time_var, width=30)
        login_entry.grid(row=4, column=1, sticky=tk.EW, pady=(15, 5))
        
        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=(20, 0))
        
        start_btn = ttk.Button(button_frame, text="Start Session", command=self._start)
        start_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _start(self):
        """Start the session and close dialog."""
        # Validate time format
        time_input = self.login_time_var.get()
        is_valid, error_msg = validate_time_format(time_input)
        if not is_valid:
            show_validation_error(self.dialog, error_msg)
            return
        
        try:
            # Parse time from 12-hour to 24-hour format
            login_time_24hr = parse_time_12hr(time_input)
        except ValueError as e:
            show_validation_error(self.dialog, f"Invalid time: {str(e)}")
            return
        
        try:
            # Start the session (transition from PLANNED to ACTIVE)
            success = self.session_service.start_session(self.session_id, login_time_24hr)
            
            if not success:
                show_error(self.dialog, "Failed to Start Session", 
                          "The session could not be started. Please try again.")
                return
            
            show_success(self.dialog, "Session Started", 
                        f"Session started for {self.session.customer_name}")
            
            # Call success callback if provided
            if self.on_success:
                self.on_success()
            
            self.dialog.destroy()
            
        except Exception as e:
            show_error(self.dialog, "Failed to Start Session", 
                      f"An error occurred while starting the session: {str(e)}")
