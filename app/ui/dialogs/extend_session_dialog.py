"""Extend Session dialog for adding extra hours to active sessions."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from typing import Optional, Callable

from app.ui.styles import COLORS, FONTS
from app.services.session_service import SessionService
from app.db.connection import DatabaseConnection
from app.utils.time_utils import format_duration
from app.ui.dialogs.error_dialog import show_validation_error, show_error, show_success
from app.services.session_service import SessionError


class ExtendSessionDialog:
    """Dialog for extending active gaming sessions with additional hours."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, session_id: int, timer_manager=None, on_success: Optional[Callable] = None):
        """
        Initialize extend session dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            session_id: ID of the session to extend
            timer_manager: Optional SessionTimerManager for updating timers
            on_success: Optional callback when session is extended successfully
        """
        self.parent = parent
        self.db = db
        self.session_id = session_id
        self.timer_manager = timer_manager
        self.on_success = on_success
        self.session_service = SessionService(db)
        
        # Fetch session
        self.session = self.session_service.get_session_by_id(session_id)
        if not self.session:
            messagebox.showerror("Error", f"Session {session_id} not found.")
            return
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Extend Session - {self.session.customer_name}")
        self.dialog.geometry("450x350")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Session info section
        info_label = ttk.Label(container, text="Current Session Information", style="Heading.TLabel")
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
        
        # Current planned duration (read-only)
        current_label = ttk.Label(container, text="Current Duration:", style="TLabel")
        current_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 10))
        current_str = format_duration(self.session.planned_duration_min) if self.session.planned_duration_min else "N/A"
        current_value = ttk.Label(container, text=current_str, style="TLabel")
        current_value.grid(row=3, column=1, sticky=tk.W, pady=(0, 10))
        
        # Extra hours section
        extra_label = ttk.Label(container, text="Add Extra Hours", style="Heading.TLabel")
        extra_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 10))
        
        # Extra hours input
        hours_label = ttk.Label(container, text="Extra Hours *", style="Heading.TLabel")
        hours_label.grid(row=5, column=0, sticky=tk.W, pady=(0, 5))
        
        self.hours_var = tk.StringVar(value="1")
        hours_entry = ttk.Entry(container, textvariable=self.hours_var, width=30)
        hours_entry.grid(row=5, column=1, sticky=tk.EW, pady=(0, 10))
        
        # Hourly rate (read-only)
        rate_label = ttk.Label(container, text="Hourly Rate:", style="TLabel")
        rate_label.grid(row=6, column=0, sticky=tk.W)
        rate_value = ttk.Label(container, text=f"₹{self.session.hourly_rate:.2f}/hour", style="TLabel")
        rate_value.grid(row=6, column=1, sticky=tk.W, pady=(0, 10))
        
        # Additional cost label
        cost_label = ttk.Label(container, text="Additional Cost:", style="TLabel")
        cost_label.grid(row=7, column=0, sticky=tk.W)
        self.cost_value = ttk.Label(container, text="₹0.00", style="TLabel")
        self.cost_value.grid(row=7, column=1, sticky=tk.W)
        
        # Bind hours input to update cost display
        self.hours_var.trace("w", self._update_cost_display)
        
        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.grid(row=8, column=0, columnspan=2, sticky=tk.EW, pady=(20, 0))
        
        extend_btn = ttk.Button(button_frame, text="Extend Session", command=self._extend_session)
        extend_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _update_cost_display(self, *args):
        """Update the additional cost display based on extra hours input."""
        try:
            extra_hours = float(self.hours_var.get())
            if extra_hours < 0:
                extra_hours = 0
            additional_cost = extra_hours * self.session.hourly_rate
            self.cost_value.config(text=f"₹{additional_cost:.2f}")
        except ValueError:
            self.cost_value.config(text="₹0.00")
    
    def _extend_session(self):
        """Extend the session with additional hours."""
        # Validate extra hours input
        hours_str = self.hours_var.get()
        try:
            extra_hours = float(hours_str)
            if extra_hours <= 0:
                raise ValueError("must be greater than 0")
            if extra_hours > 24:
                raise ValueError("cannot exceed 24 hours")
            extra_min = int(extra_hours * 60)
        except ValueError as e:
            show_validation_error(self.dialog, f"Invalid extra hours: {str(e)}")
            return
        
        try:
            # Update session with new planned duration
            new_duration_min = self.session.planned_duration_min + extra_min
            new_total_due = self.session.paid_amount + (extra_hours * self.session.hourly_rate)
            
            # Update database
            rows_affected = self.db.update(
                """UPDATE sessions 
                   SET planned_duration_min = ?, total_due = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (new_duration_min, new_total_due, self.session_id)
            )
            
            if not rows_affected:
                show_error(self.dialog, "Failed to Extend Session", 
                          "The session could not be updated. Please try again.")
                return
            
            # Update timer if available
            if self.timer_manager:
                # Remove old timer
                self.timer_manager.remove_session(self.session_id)
                # Re-add with new duration
                self.timer_manager.add_session(
                    session_id=self.session_id,
                    customer_name=self.session.customer_name,
                    system_name=self.session.system_name,
                    planned_duration_min=new_duration_min,
                    login_time_24hr=self.session.login_time
                )
            
            # Show success message
            new_duration_str = format_duration(new_duration_min)
            show_success(self.dialog, "Session Extended",
                        f"Session extended for {self.session.customer_name}\n\n"
                        f"New Duration: {new_duration_str}\n"
                        f"Additional Cost: ₹{extra_hours * self.session.hourly_rate:.2f}\n"
                        f"New Total: ₹{new_total_due:.2f}")
            
            # Call success callback
            if self.on_success:
                self.on_success()
            
            self.dialog.destroy()
        
        except SessionError as e:
            show_validation_error(self.dialog, str(e))
        except Exception as e:
            show_error(self.dialog, "Failed to Extend Session",
                      f"An unexpected error occurred: {str(e)}")
