"""Start Session dialog for creating new gaming sessions."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from typing import Optional, Callable
from app.ui.styles import COLORS, FONTS
from app.services.system_service import SystemService
from app.services.session_service import SessionService
from app.db.connection import DatabaseConnection
from app.utils.validators import validate_customer_name, validate_hourly_rate, validate_notes
from app.ui.dialogs.error_dialog import show_validation_error, show_error, show_success
from app.services.session_service import SessionError


class StartSessionDialog:
    """Dialog for starting a new gaming session."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, on_success: Optional[Callable] = None):
        """
        Initialize start session dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            on_success: Optional callback when session is created successfully
        """
        self.parent = parent
        self.db = db
        self.system_service = SystemService(db)
        self.session_service = SessionService(db)
        self.on_success = on_success
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Start New Session")
        self.dialog.geometry("400x500")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Result
        self.result = None
        
        # Build UI
        self._create_ui()
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # System selection
        system_label = ttk.Label(container, text="Select System *", style="Heading.TLabel")
        system_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.system_var = tk.StringVar()
        available_systems = self.system_service.get_available_systems()
        
        if not available_systems:
            messagebox.showwarning("No Systems Available", "All systems are currently in use.")
            self.dialog.destroy()
            return
        
        system_choices = [f"{s.system_name} ({s.system_type})" for s in available_systems]
        system_combo = ttk.Combobox(
            container,
            textvariable=self.system_var,
            values=system_choices,
            state="readonly",
            width=35
        )
        system_combo.grid(row=0, column=1, sticky=tk.EW, pady=(0, 10))
        system_combo.current(0)  # Select first available system
        
        self.available_systems = available_systems
        
        # Customer name
        customer_label = ttk.Label(container, text="Customer Name *", style="Heading.TLabel")
        customer_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.customer_var = tk.StringVar()
        customer_entry = ttk.Entry(container, textvariable=self.customer_var, width=38)
        customer_entry.grid(row=1, column=1, sticky=tk.EW, pady=(0, 10))
        customer_entry.focus()
        
        # Hourly rate
        rate_label = ttk.Label(container, text="Hourly Rate *", style="Heading.TLabel")
        rate_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.rate_var = tk.StringVar(
            value=str(available_systems[0].default_hourly_rate) if available_systems else "0"
        )
        rate_entry = ttk.Entry(container, textvariable=self.rate_var, width=38)
        rate_entry.grid(row=2, column=1, sticky=tk.EW, pady=(0, 10))
        
        # Update rate when system changes
        system_combo.bind("<<ComboboxSelected>>", self._on_system_changed)
        
        # Planned duration (hours)
        duration_label = ttk.Label(container, text="Planned Duration (Hours) *", style="Heading.TLabel")
        duration_label.grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        self.duration_var = tk.StringVar(value="1")
        duration_entry = ttk.Entry(container, textvariable=self.duration_var, width=38)
        duration_entry.grid(row=3, column=1, sticky=tk.EW, pady=(0, 10))
        
        # Payment method
        payment_label = ttk.Label(container, text="Payment Method *", style="Heading.TLabel")
        payment_label.grid(row=4, column=0, sticky=tk.W, pady=(0, 5))
        
        self.payment_var = tk.StringVar(value="Cash")
        payment_combo = ttk.Combobox(
            container,
            textvariable=self.payment_var,
            values=["Cash", "Online", "Mixed"],
            state="readonly",
            width=35
        )
        payment_combo.grid(row=4, column=1, sticky=tk.EW, pady=(0, 10))
        
        # Notes
        notes_label = ttk.Label(container, text="Notes (Optional)", style="Heading.TLabel")
        notes_label.grid(row=5, column=0, sticky=tk.NW, pady=(0, 5))
        
        self.notes_text = tk.Text(container, height=3, width=38, bg=COLORS["bg_card"], fg=COLORS["text_primary"])
        self.notes_text.grid(row=5, column=1, sticky=tk.EW, pady=(0, 10))
        
        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=(20, 0))
        
        start_btn = ttk.Button(button_frame, text="Start Session", command=self._start_session)
        start_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _on_system_changed(self, event=None):
        """Update hourly rate when system selection changes."""
        selected_idx = self.available_systems[0:1]  # Start with first
        
        # Find selected system in list
        for i, system in enumerate(self.available_systems):
            system_display = f"{system.system_name} ({system.system_type})"
            if self.system_var.get() == system_display:
                self.rate_var.set(str(system.default_hourly_rate))
                break
    
    def _start_session(self):
        """Create the session and close dialog."""
        # Validate system selection
        if not self.system_var.get():
            show_validation_error(self.dialog, "Please select a system.")
            return
        
        # Validate customer name
        customer_name = self.customer_var.get()
        is_valid, error_msg = validate_customer_name(customer_name)
        if not is_valid:
            show_validation_error(self.dialog, error_msg)
            return
        
        # Validate hourly rate
        rate_str = self.rate_var.get()
        is_valid, error_msg = validate_hourly_rate(rate_str)
        if not is_valid:
            show_validation_error(self.dialog, error_msg)
            return
        
        rate = float(rate_str)
        
        # Validate planned duration (hours)
        duration_str = self.duration_var.get()
        try:
            duration_hours = float(duration_str)
            if duration_hours <= 0:
                raise ValueError("must be greater than 0")
            if duration_hours > 24:
                raise ValueError("cannot exceed 24 hours")
            duration_min = int(duration_hours * 60)
        except ValueError as e:
            show_validation_error(self.dialog, f"Invalid planned duration: {str(e)}")
            return
        
        # Get selected system
        system_display = self.system_var.get()
        selected_system = None
        for system in self.available_systems:
            system_text = f"{system.system_name} ({system.system_type})"
            if system_text == system_display:
                selected_system = system
                break
        
        if not selected_system:
            show_error(self.dialog, "Error", "Selected system not found.")
            return
        
        # Double-check system is still available (prevent race condition)
        try:
            current_system = self.system_service.get_system_by_id(selected_system.id)
            if current_system and current_system.availability != "Available":
                show_error(self.dialog, "System In Use", 
                          f"{selected_system.system_name} is no longer available.")
                return
        except Exception as e:
            show_error(self.dialog, "Database Error", 
                      f"Failed to check system availability: {str(e)}")
            return
        
        # Get payment method
        payment_method = self.payment_var.get()
        
        try:
            # Validate notes if provided
            notes = self.notes_text.get("1.0", tk.END).strip() or None
            if notes:
                is_valid, error_msg = validate_notes(notes)
                if not is_valid:
                    show_validation_error(self.dialog, error_msg)
                    return
            
            # Calculate total amount based on planned duration
            total_amount = (duration_hours * rate)
            
            # Create prepaid session (PLANNED state)
            session_id = self.session_service.create_prepaid_session(
                date=datetime.now().strftime("%Y-%m-%d"),
                customer_name=customer_name.strip(),
                system_id=selected_system.id,
                planned_duration_min=duration_min,
                hourly_rate=rate,
                payment_method=payment_method,
                extra_charges=0.0,
                notes=notes
            )
            
            # Immediately start the session with current time (transition PLANNED -> ACTIVE)
            # Use the actual current time (with microseconds precision), not user input, to ensure accurate countdown
            # This captures the exact moment start_session() is called, ensuring each session has a unique timestamp
            login_time_24hr = datetime.now().strftime("%H:%M:%S")
            success = self.session_service.start_session(session_id, login_time_24hr)
            if not success:
                show_error(self.dialog, "Failed to Start Session", 
                          "Session was created but could not be started.")
                return
            
            # Mark system as in use
            self.system_service.set_system_availability(selected_system.id, "In Use")
            
            # Format duration for display
            from app.utils.time_utils import format_duration
            duration_display = format_duration(duration_min)
            
            show_success(self.dialog, "Session Started", 
                        f"Session started for {customer_name}\n" + 
                        f"System: {selected_system.system_name}\n" +
                        f"Duration: {duration_display} = ₹{total_amount:.2f}")
            
            # Call success callback if provided
            if self.on_success:
                self.on_success()
            
            self.dialog.destroy()
            
        except SessionError as e:
            show_validation_error(self.dialog, str(e))
        except Exception as e:
            show_error(self.dialog, "Failed to Create Session", 
                      f"An error occurred while creating the session: {str(e)}")
