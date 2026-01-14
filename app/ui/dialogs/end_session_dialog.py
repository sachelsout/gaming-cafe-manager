"""End Session dialog for completing gaming sessions and calculating billing."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable
from app.ui.styles import COLORS, FONTS
from app.services.session_service import SessionService
from app.services.system_service import SystemService
from app.utils.time_utils import calculate_duration_minutes, format_duration, calculate_bill, get_current_time_12hr, format_time_12hr, parse_time_12hr
from app.db.connection import DatabaseConnection
from app.utils.validators import validate_time_format, validate_hourly_rate, validate_extra_charges, validate_notes
from app.ui.dialogs.error_dialog import show_validation_error, show_error, show_success
from app.services.session_service import SessionError


class EndSessionDialog:
    """Dialog for ending a gaming session and calculating billing."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, session_id: int, on_success: Optional[Callable] = None):
        """
        Initialize end session dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            session_id: ID of the session to end
            on_success: Optional callback when session is ended successfully
        """
        self.parent = parent
        self.db = db
        self.session_id = session_id
        self.session_service = SessionService(db)
        self.system_service = SystemService(db)
        self.on_success = on_success
        
        # Fetch session
        self.session = self.session_service.get_session_by_id(session_id)
        if not self.session:
            messagebox.showerror("Error", f"Session {session_id} not found.")
            return
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"End Session - {self.session.customer_name}")
        self.dialog.geometry("500x650")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (650 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # State variables
        self.notes_var = tk.StringVar()
        
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
        
        # Login time (read-only, display in 12-hour format)
        login_label = ttk.Label(container, text="Login Time:", style="TLabel")
        login_label.grid(row=3, column=0, sticky=tk.W)
        login_time_12hr = format_time_12hr(self.session.login_time) if self.session.login_time else "--"
        login_value = ttk.Label(container, text=login_time_12hr, style="TLabel")
        login_value.grid(row=3, column=1, sticky=tk.W)
        
        # Planned duration (read-only)
        planned_label = ttk.Label(container, text="Planned Duration:", style="TLabel")
        planned_label.grid(row=4, column=0, sticky=tk.W)
        from app.utils.time_utils import format_duration
        planned_str = format_duration(self.session.planned_duration_min) if self.session.planned_duration_min else "N/A"
        planned_value = ttk.Label(container, text=planned_str, style="TLabel")
        planned_value.grid(row=4, column=1, sticky=tk.W)
        
        # Logout time (calculated automatically)
        logout_label = ttk.Label(container, text="Logout Time (Auto):", style="TLabel")
        logout_label.grid(row=5, column=0, sticky=tk.W, pady=(10, 0))
        calculated_logout_time = self._calculate_logout_time()
        logout_value = ttk.Label(container, text=calculated_logout_time, style="TLabel")
        logout_value.grid(row=5, column=1, sticky=tk.W, pady=(10, 0))
        
        # Amount paid (read-only)
        paid_label = ttk.Label(container, text="Amount Paid (Upfront):", style="TLabel")
        paid_label.grid(row=6, column=0, sticky=tk.W, pady=(10, 0))
        paid_value = ttk.Label(container, text=f"₹{self.session.paid_amount:.2f}" if self.session.paid_amount else "N/A", style="TLabel")
        paid_value.grid(row=6, column=1, sticky=tk.W, pady=(10, 0))
        
        # Notes section
        notes_label = ttk.Label(container, text="Notes (Optional)", style="Heading.TLabel")
        notes_label.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(20, 5))
        
        notes_text = tk.Text(
            container,
            height=4,
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief=tk.FLAT,
            bd=1
        )
        notes_text.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Bind text widget to variable
        def update_notes(event=None):
            self.notes_var.set(notes_text.get("1.0", tk.END).strip())
        
        notes_text.bind("<KeyRelease>", update_notes)
        self.notes_text = notes_text  # Store reference for later
        
        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.grid(row=10, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        end_btn = ttk.Button(button_frame, text="End Session & Save", command=self._end_session)
        end_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _calculate_logout_time(self) -> str:
        """Calculate logout time based on login_time + planned_duration_min.
        
        Returns:
            Logout time in 12-hour format (HH:MM AM/PM) or "--" if login_time is missing
        """
        if not self.session.login_time or not self.session.planned_duration_min:
            return "--"
        
        try:
            from app.utils.time_utils import parse_time_24hr_to_datetime
            from datetime import timedelta
            # Parse login time to datetime
            login_dt = parse_time_24hr_to_datetime(self.session.login_time)
            # Add planned duration
            logout_dt = login_dt + timedelta(minutes=self.session.planned_duration_min)
            # Return formatted as 12-hour time
            return logout_dt.strftime("%I:%M %p")
        except Exception:
            return "--"
    
    def _get_logout_time_24hr(self) -> str:
        """Get logout time in 24-hour format based on login_time + planned_duration_min.
        
        Returns:
            Logout time in HH:MM:SS format
        """
        from app.utils.time_utils import parse_time_24hr_to_datetime
        from datetime import timedelta
        
        login_dt = parse_time_24hr_to_datetime(self.session.login_time)
        logout_dt = login_dt + timedelta(minutes=self.session.planned_duration_min)
        return logout_dt.strftime("%H:%M:%S")
    
    def _end_session(self):
        """End the session and save to database."""
        # Calculate logout time automatically from login_time + planned_duration
        try:
            logout_time_24hr = self._get_logout_time_24hr()
        except Exception as e:
            show_validation_error(self.dialog, f"Failed to calculate logout time: {str(e)}")
            return
        
        # Validate notes if provided
        notes = self.notes_text.get("1.0", tk.END).strip() if hasattr(self, 'notes_text') else ""
        if notes:
            is_valid, error_msg = validate_notes(notes)
            if not is_valid:
                show_validation_error(self.dialog, error_msg)
                return
        
        try:
            # Calculate actual duration for records
            duration_minutes = calculate_duration_minutes(self.session.login_time, logout_time_24hr)
            
            # Ensure duration is positive
            if duration_minutes <= 0:
                show_validation_error(self.dialog, 
                                     "Logout time must be after login time.")
                return
            
            # End the session (records actual duration but does NOT recalculate charges)
            # Payment was already recorded when session was created/started
            success = self.session_service.end_session(
                self.session_id,
                logout_time_24hr,
                extra_charges=0.0,  # No extra charges - use paid amount as-is
                notes=notes
            )
            
            if not success:
                show_error(self.dialog, "Failed to End Session", 
                          "The session could not be saved. Please try again.")
                return
            
            # Mark system as available
            try:
                self.system_service.set_system_availability(self.session.system_id, "Available")
            except Exception as e:
                show_error(self.dialog, "System Update Error", 
                          f"Session ended but system status could not be updated: {str(e)}")
                return
            
            # Show confirmation with session details
            planned_duration = self.session.planned_duration_min if hasattr(self.session, 'planned_duration_min') else 0
            
            show_success(self.dialog, "Session Ended",
                        f"Session ended for {self.session.customer_name}\n\n"
                        f"Planned Duration: {format_duration(planned_duration)}\n"
                        f"Actual Duration: {format_duration(duration_minutes)}\n"
                        f"Amount Paid (No Refunds): ₹{self.session.paid_amount:.2f}")
            
            # Call success callback
            if self.on_success:
                self.on_success()
            
            self.dialog.destroy()
        
        except SessionError as e:
            show_validation_error(self.dialog, str(e))
        except Exception as e:
            show_error(self.dialog, "Failed to End Session",
                      f"An unexpected error occurred: {str(e)}")
