"""Session History and Revenue Summary dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, date
from typing import Optional, Callable

from app.ui.styles import COLORS, FONTS
from app.services.session_service import SessionService
from app.db.connection import DatabaseConnection
from app.utils.time_utils import format_time_12hr


class SessionHistoryDialog:
    """Dialog for viewing completed sessions and daily revenue summaries."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection):
        """
        Initialize session history dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
        """
        self.parent = parent
        self.db = db
        self.session_service = SessionService(db)
        
        # Default date range: last 7 days
        self.end_date = date.today()
        self.start_date = self.end_date - timedelta(days=6)
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Session History & Revenue Summary")
        self.dialog.geometry("900x600")
        self.dialog.resizable(True, True)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (900 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (600 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self._create_ui()
        
        # Load initial data
        self._load_data()
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Filter section
        filter_frame = ttk.LabelFrame(main_frame, text="Filter", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Date range selection
        date_container = ttk.Frame(filter_frame)
        date_container.pack(fill=tk.X)
        
        ttk.Label(date_container, text="From:", font=FONTS["small"]).pack(side=tk.LEFT, padx=(0, 5))
        
        self.start_date_var = tk.StringVar(value=self.start_date.strftime("%Y-%m-%d"))
        start_entry = ttk.Entry(date_container, textvariable=self.start_date_var, width=12)
        start_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(date_container, text="To:", font=FONTS["small"]).pack(side=tk.LEFT, padx=(0, 5))
        
        self.end_date_var = tk.StringVar(value=self.end_date.strftime("%Y-%m-%d"))
        end_entry = ttk.Entry(date_container, textvariable=self.end_date_var, width=12)
        end_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        # Quick filter buttons
        ttk.Button(date_container, text="Today", command=self._filter_today).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_container, text="Last 7 Days", command=self._filter_last_7).pack(side=tk.LEFT, padx=2)
        ttk.Button(date_container, text="Last 30 Days", command=self._filter_last_30).pack(side=tk.LEFT, padx=2)
        
        refresh_btn = ttk.Button(date_container, text="Refresh", command=self._load_data)
        refresh_btn.pack(side=tk.RIGHT, padx=0)
        
        # Revenue summary section
        summary_frame = ttk.LabelFrame(main_frame, text="Daily Summary", padding=10)
        summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Summary labels
        summary_container = ttk.Frame(summary_frame)
        summary_container.pack(fill=tk.X)
        
        self.summary_label = tk.Label(
            summary_container,
            text="Total Revenue: ₹0.00 | Sessions: 0 | Cash: ₹0.00 | Online: ₹0.00 | Mixed: ₹0.00 | Pending: ₹0.00",
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
            font=FONTS["small"],
            pady=8,
            padx=10
        )
        self.summary_label.pack(fill=tk.X)
        
        # Sessions table section
        table_frame = ttk.LabelFrame(main_frame, text="Completed Sessions", padding=0)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create treeview for sessions
        self.sessions_tree = ttk.Treeview(
            table_frame,
            columns=("date", "customer", "system", "login", "logout", "duration", "rate", "extra", "total", "payment", "notes"),
            height=15,
            show="headings"
        )
        
        # Define columns
        self.sessions_tree.column("date", width=75, anchor=tk.CENTER)
        self.sessions_tree.column("customer", width=100, anchor=tk.W)
        self.sessions_tree.column("system", width=75, anchor=tk.CENTER)
        self.sessions_tree.column("login", width=75, anchor=tk.CENTER)
        self.sessions_tree.column("logout", width=75, anchor=tk.CENTER)
        self.sessions_tree.column("duration", width=65, anchor=tk.CENTER)
        self.sessions_tree.column("rate", width=60, anchor=tk.CENTER)
        self.sessions_tree.column("extra", width=60, anchor=tk.CENTER)
        self.sessions_tree.column("total", width=70, anchor=tk.E)
        self.sessions_tree.column("payment", width=75, anchor=tk.CENTER)
        self.sessions_tree.column("notes", width=120, anchor=tk.W)
        
        # Define headings
        self.sessions_tree.heading("date", text="Date")
        self.sessions_tree.heading("customer", text="Customer")
        self.sessions_tree.heading("system", text="System")
        self.sessions_tree.heading("login", text="Login")
        self.sessions_tree.heading("logout", text="Logout")
        self.sessions_tree.heading("duration", text="Duration")
        self.sessions_tree.heading("rate", text="Rate")
        self.sessions_tree.heading("extra", text="Extra")
        self.sessions_tree.heading("total", text="Total")
        self.sessions_tree.heading("payment", text="Payment")
        self.sessions_tree.heading("notes", text="Notes")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.sessions_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.sessions_tree.xview)
        
        self.sessions_tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        self.sessions_tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        export_btn = ttk.Button(button_frame, text="Export to CSV", command=self._export_csv)
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        close_btn = ttk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def _filter_today(self):
        """Set date filter to today."""
        today = date.today()
        self.start_date_var.set(today.strftime("%Y-%m-%d"))
        self.end_date_var.set(today.strftime("%Y-%m-%d"))
        self._load_data()
    
    def _filter_last_7(self):
        """Set date filter to last 7 days."""
        end = date.today()
        start = end - timedelta(days=6)
        self.start_date_var.set(start.strftime("%Y-%m-%d"))
        self.end_date_var.set(end.strftime("%Y-%m-%d"))
        self._load_data()
    
    def _filter_last_30(self):
        """Set date filter to last 30 days."""
        end = date.today()
        start = end - timedelta(days=29)
        self.start_date_var.set(start.strftime("%Y-%m-%d"))
        self.end_date_var.set(end.strftime("%Y-%m-%d"))
        self._load_data()
    
    def _load_data(self):
        """Load sessions and revenue data for the selected date range."""
        try:
            # Parse dates
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            # Validate date format
            datetime.strptime(start_date, "%Y-%m-%d")
            datetime.strptime(end_date, "%Y-%m-%d")
            
            # Fetch completed sessions
            sessions = self.session_service.get_completed_sessions(start_date, end_date)
            
            # Clear existing tree
            for item in self.sessions_tree.get_children():
                self.sessions_tree.delete(item)
            
            # Populate tree with sessions
            for session in sessions:
                duration_str = f"{session.duration_minutes}m" if session.duration_minutes else "--"
                payment_method = session.payment_status.replace("Paid-", "").replace("Pending", "Pending")
                login_12hr = format_time_12hr(session.login_time) if session.login_time else "--"
                logout_12hr = format_time_12hr(session.logout_time) if session.logout_time else "--"
                
                self.sessions_tree.insert("", tk.END, values=(
                    session.date,
                    session.customer_name,
                    session.system_name,
                    login_12hr,
                    logout_12hr,
                    duration_str,
                    f"₹{session.hourly_rate:.0f}",
                    f"₹{session.extra_charges:.2f}" if session.extra_charges else "₹0.00",
                    f"₹{session.total_due:.2f}" if session.total_due else "₹0.00",
                    payment_method,
                    session.notes or ""
                ))
            
            # Calculate and update summary
            revenue_data = self.session_service.get_date_range_revenue(start_date, end_date)
            self._update_summary(revenue_data)
        
        except ValueError as e:
            messagebox.showerror("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
    
    def _update_summary(self, revenue_data: dict):
        """Update the revenue summary display."""
        summary_text = (
            f"Total Revenue: ₹{revenue_data['total_revenue']:.2f} | "
            f"Sessions: {revenue_data['session_count']} | "
            f"Cash: ₹{revenue_data['cash_total']:.2f} | "
            f"Online: ₹{revenue_data['online_total']:.2f} | "
            f"Mixed: ₹{revenue_data['mixed_total']:.2f} | "
            f"Pending: ₹{revenue_data['pending_total']:.2f}"
        )
        self.summary_label.config(text=summary_text)
    
    def _export_csv(self):
        """Export session data to CSV file."""
        try:
            from tkinter import filedialog
            import csv
            
            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"sessions_{date.today().strftime('%Y%m%d')}.csv"
            )
            
            if not file_path:
                return
            
            # Get current data from tree
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "Date", "Customer", "System", "Login (12hr)", "Logout (12hr)", "Duration (min)", "Hourly Rate",
                    "Extra Charges", "Total Due", "Payment Method", "Notes"
                ])
                
                # Write rows
                for item in self.sessions_tree.get_children():
                    values = self.sessions_tree.item(item)["values"]
                    writer.writerow(values)
            
            messagebox.showinfo("Success", f"Data exported to {file_path}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")
