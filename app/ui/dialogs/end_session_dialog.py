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
        self.logout_time_var = tk.StringVar(value=get_current_time_12hr())
        self.extra_charges_var = tk.StringVar(value="0.0")
        self.rate_var = tk.StringVar(value=str(self.session.hourly_rate))
        self.payment_method_var = tk.StringVar(value="Paid-Cash")
        self.notes_var = tk.StringVar()
        
        # Build UI
        self._create_ui()
        
        # Calculate initial billing
        self._update_billing()
    
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
        
        # Logout time
        logout_label = ttk.Label(container, text="Logout Time *", style="Heading.TLabel")
        logout_label.grid(row=4, column=0, sticky=tk.W, pady=(15, 5))
        logout_entry = ttk.Entry(container, textvariable=self.logout_time_var, width=30)
        logout_entry.grid(row=4, column=1, sticky=tk.EW, pady=(15, 5))
        logout_entry.bind("<KeyRelease>", lambda e: self._update_billing())
        
        # Duration display (calculated, read-only)
        duration_label = ttk.Label(container, text="Duration:", style="TLabel")
        duration_label.grid(row=5, column=0, sticky=tk.W)
        self.duration_display = ttk.Label(container, text="-- calculating --", style="TLabel")
        self.duration_display.grid(row=5, column=1, sticky=tk.W)
        
        # Billing section
        billing_label = ttk.Label(container, text="Billing Information", style="Heading.TLabel")
        billing_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        # Hourly rate (editable)
        rate_label = ttk.Label(container, text="Hourly Rate *", style="Heading.TLabel")
        rate_label.grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        rate_entry = ttk.Entry(container, textvariable=self.rate_var, width=30)
        rate_entry.grid(row=7, column=1, sticky=tk.EW, pady=(0, 5))
        rate_entry.bind("<KeyRelease>", lambda e: self._update_billing())
        
        # Base amount (calculated, read-only)
        base_label = ttk.Label(container, text="Base Amount:", style="TLabel")
        base_label.grid(row=8, column=0, sticky=tk.W)
        self.base_display = ttk.Label(container, text="0.00", style="TLabel")
        self.base_display.grid(row=8, column=1, sticky=tk.W)
        
        # Extra charges (editable)
        extra_label = ttk.Label(container, text="Extra Charges", style="Heading.TLabel")
        extra_label.grid(row=9, column=0, sticky=tk.W, pady=(10, 5))
        extra_entry = ttk.Entry(container, textvariable=self.extra_charges_var, width=30)
        extra_entry.grid(row=9, column=1, sticky=tk.EW, pady=(10, 5))
        extra_entry.bind("<KeyRelease>", lambda e: self._update_billing())
        
        # Total due (calculated, read-only, highlighted)
        total_label = tk.Label(
            container,
            text="TOTAL DUE:",
            bg=COLORS["status_pending"],
            fg=COLORS["bg_dark"],
            font=FONTS["heading"],
            pady=10
        )
        total_label.grid(row=10, column=0, sticky=tk.W, pady=(10, 0))
        
        self.total_display = tk.Label(
            container,
            text="0.00",
            bg=COLORS["status_pending"],
            fg=COLORS["bg_dark"],
            font=("Segoe UI", 16, "bold"),
            pady=10,
            padx=10
        )
        self.total_display.grid(row=10, column=1, sticky=tk.EW, pady=(10, 0))
        
        # Payment section
        payment_label = ttk.Label(container, text="Payment Information", style="Heading.TLabel")
        payment_label.grid(row=11, column=0, columnspan=2, sticky=tk.W, pady=(20, 10))
        
        # Payment method
        method_label = ttk.Label(container, text="Payment Method *", style="Heading.TLabel")
        method_label.grid(row=12, column=0, sticky=tk.W, pady=(0, 5))
        
        method_combo = ttk.Combobox(
            container,
            textvariable=self.payment_method_var,
            values=["Paid-Cash", "Paid-Online", "Paid-Mixed"],
            state="readonly",
            width=27
        )
        method_combo.grid(row=12, column=1, sticky=tk.EW, pady=(0, 5))
        
        # Notes
        notes_label = ttk.Label(container, text="Notes (Booking, Payment Split, etc.)", style="Heading.TLabel")
        notes_label.grid(row=13, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        notes_text = tk.Text(
            container,
            height=4,
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            relief=tk.FLAT,
            bd=1
        )
        notes_text.grid(row=14, column=0, columnspan=2, sticky=tk.EW, pady=(0, 10))
        
        # Bind text widget to variable
        def update_notes(event=None):
            self.notes_var.set(notes_text.get("1.0", tk.END).strip())
        
        notes_text.bind("<KeyRelease>", update_notes)
        self.notes_text = notes_text  # Store reference for later
        
        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.grid(row=15, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        end_btn = ttk.Button(button_frame, text="End Session & Save", command=self._end_session)
        end_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _update_billing(self):
        """Update calculated billing amounts."""
        try:
            logout_time_input = self.logout_time_var.get()
            
            # Parse and convert 12-hour format to 24-hour format for calculation
            logout_time_24hr = parse_time_12hr(logout_time_input)
            
            # Calculate duration
            duration_minutes = calculate_duration_minutes(self.session.login_time, logout_time_24hr)
            duration_str = format_duration(duration_minutes)
            self.duration_display.config(text=duration_str)
            
            # Parse rate
            try:
                hourly_rate = float(self.rate_var.get())
                if hourly_rate < 0:
                    raise ValueError("Rate cannot be negative")
            except ValueError:
                self.base_display.config(text="--")
                self.total_display.config(text="--")
                return
            
            # Calculate base amount
            base_amount = calculate_bill(duration_minutes, hourly_rate, 0.0)
            self.base_display.config(text=f"{base_amount:.2f}")
            
            # Parse extra charges
            try:
                extra_charges = float(self.extra_charges_var.get())
                if extra_charges < 0:
                    raise ValueError("Extra charges cannot be negative")
            except ValueError:
                extra_charges = 0.0
            
            # Calculate total
            total = calculate_bill(duration_minutes, hourly_rate, extra_charges)
            self.total_display.config(text=f"{total:.2f}")
        
        except (ValueError, TypeError):
            # Invalid input - show placeholder
            self.duration_display.config(text="--")
            self.base_display.config(text="--")
            self.total_display.config(text="--")
    
    def _end_session(self):
        """End the session and save to database."""
        # Validate logout time
        try:
            logout_time_input = self.logout_time_var.get()
            logout_time_24hr = parse_time_12hr(logout_time_input)
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid logout time format. Use HH:MM AM/PM or H:MM AM/PM (e.g., 2:30 PM).")
            return
        
        # Validate rate
        try:
            hourly_rate = float(self.rate_var.get())
            if hourly_rate < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid hourly rate (>= 0).")
            return
        
        # Validate extra charges
        try:
            extra_charges = float(self.extra_charges_var.get())
            if extra_charges < 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Extra charges must be >= 0.")
            return
        
        try:
            # Calculate final duration
            duration_minutes = calculate_duration_minutes(self.session.login_time, logout_time_24hr)
            
            # Update session with new rate if changed
            if float(self.rate_var.get()) != self.session.hourly_rate:
                # Update the session's hourly rate in the database
                self.db.update(
                    "UPDATE sessions SET hourly_rate = ? WHERE id = ?",
                    (hourly_rate, self.session_id)
                )
            
            # Get payment method and notes
            payment_status = self.payment_method_var.get()
            notes = self.notes_var.get()
            
            # End the session (calculates duration and total, saves payment info)
            success = self.session_service.end_session(
                self.session_id,
                logout_time_24hr,
                extra_charges,
                payment_status,
                notes
            )
            
            if not success:
                messagebox.showerror("Error", "Failed to end session.")
                return
            
            # Mark system as available
            self.system_service.set_system_availability(self.session.system_id, "Available")
            
            # Show confirmation
            total = calculate_bill(duration_minutes, hourly_rate, extra_charges)
            messagebox.showinfo(
                "Session Ended",
                f"Session ended for {self.session.customer_name}\n\n"
                f"Duration: {format_duration(duration_minutes)}\n"
                f"Base: {calculate_bill(duration_minutes, hourly_rate, 0.0):.2f}\n"
                f"Extra: {extra_charges:.2f}\n"
                f"Total: {total:.2f}\n"
                f"Payment: {payment_status}"
            )
            
            # Call success callback
            if self.on_success:
                self.on_success()
            
            self.dialog.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to end session: {str(e)}")
