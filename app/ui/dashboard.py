"""Main dashboard component showing systems and active sessions."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from app.ui.styles import COLORS, FONTS
from app.services.system_service import SystemService
from app.services.session_service import SessionService
from app.db.connection import DatabaseConnection
from app.utils.time_utils import format_time_12hr


class Dashboard:
    """Dashboard component displaying systems and active sessions."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection):
        """
        Initialize dashboard.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
        """
        self.parent = parent
        self.db = db
        self.system_service = SystemService(db)
        self.session_service = SessionService(db)
        
        # Timer state
        self.timer_id = None
        
        # Create main container
        self.container = ttk.Frame(parent)
        self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Build UI
        self._create_header()
        self._create_content()
        
        # Store references for updates
        self.system_frames = {}
        self.refresh()
        
        # Start timer for updating elapsed times
        self._schedule_timer_update()
    
    def _create_header(self):
        """Create dashboard header with title and action buttons."""
        header = ttk.Frame(self.container)
        header.pack(fill=tk.X, pady=(0, 10))
        
        title = ttk.Label(header, text="Gaming Cafe Dashboard", style="Title.TLabel")
        title.pack(side=tk.LEFT)
        
        # Buttons on the right
        button_frame = ttk.Frame(header)
        button_frame.pack(side=tk.RIGHT)
        
        start_btn = ttk.Button(button_frame, text="+ Start Session", command=self._show_start_session)
        start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_btn = ttk.Button(button_frame, text="🔄 Refresh", command=self.refresh)
        refresh_btn.pack(side=tk.LEFT)
    
    def _create_content(self):
        """Create main content area with systems and sessions."""
        # Systems section
        systems_label = ttk.Label(self.container, text="System Status", style="Heading.TLabel")
        systems_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.systems_frame = ttk.Frame(self.container)
        self.systems_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 15))
        
        # Create grid layout for systems (3 columns)
        for i in range(3):
            self.systems_frame.grid_columnconfigure(i, weight=1)
        
        # Sessions section
        sessions_label = ttk.Label(self.container, text="Active Sessions", style="Heading.TLabel")
        sessions_label.pack(anchor=tk.W, pady=(10, 5))
        
        self.sessions_frame = ttk.Frame(self.container)
        self.sessions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview for sessions
        columns = ("System", "Customer", "Duration", "Rate", "Total")
        self.sessions_tree = ttk.Treeview(self.sessions_frame, columns=columns, height=8)
        
        # Define column headings
        self.sessions_tree.column("#0", width=0, stretch=tk.NO)
        self.sessions_tree.heading("#0", text="", anchor=tk.W)
        
        self.sessions_tree.column("System", anchor=tk.W, width=80)
        self.sessions_tree.heading("System", text="System", anchor=tk.W)
        
        self.sessions_tree.column("Customer", anchor=tk.W, width=120)
        self.sessions_tree.heading("Customer", text="Customer", anchor=tk.W)
        
        self.sessions_tree.column("Duration", anchor=tk.CENTER, width=80)
        self.sessions_tree.heading("Duration", text="Duration", anchor=tk.CENTER)
        
        self.sessions_tree.column("Rate", anchor=tk.CENTER, width=80)
        self.sessions_tree.heading("Rate", text="Rate/hr", anchor=tk.CENTER)
        
        self.sessions_tree.column("Total", anchor=tk.E, width=80)
        self.sessions_tree.heading("Total", text="Total Due", anchor=tk.CENTER)
        
        self.sessions_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.sessions_frame, orient=tk.VERTICAL, command=self.sessions_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sessions_tree.configure(yscroll=scrollbar.set)
        
        # Bind double-click to end session
        self.sessions_tree.bind("<Double-1>", self._on_session_double_click)
    
    def refresh(self):
        """Refresh dashboard with latest data."""
        # Clear existing system frames
        for widget in self.systems_frame.winfo_children():
            widget.destroy()
        self.system_frames.clear()
        
        # Fetch systems
        systems = self.system_service.get_all_systems()
        
        # Create system cards
        for idx, system in enumerate(systems):
            row = idx // 3
            col = idx % 3
            self._create_system_card(system, row, col)
        
        # Refresh sessions
        self._refresh_sessions()
    
    def _create_system_card(self, system, row: int, col: int):
        """
        Create a system status card.
        
        Args:
            system: System object
            row: Grid row
            col: Grid column
        """
        # Determine status color
        if system.availability == "In Use":
            status_color = COLORS["status_in_use"]
            status_text = "● In Use"
        else:
            status_color = COLORS["status_available"]
            status_text = "● Available"
        
        # Create card frame
        card = tk.Frame(self.systems_frame, bg=COLORS["bg_card"], relief=tk.RAISED, bd=1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        # System name
        name_label = tk.Label(
            card,
            text=system.system_name,
            font=FONTS["heading"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"]
        )
        name_label.pack(pady=(10, 5))
        
        # Type
        type_label = tk.Label(
            card,
            text=system.system_type,
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"]
        )
        type_label.pack()
        
        # Status indicator
        status_label = tk.Label(
            card,
            text=status_text,
            font=FONTS["body"],
            bg=COLORS["bg_card"],
            fg=status_color
        )
        status_label.pack(pady=5)
        
        # Rate
        rate_label = tk.Label(
            card,
            text=f"{system.default_hourly_rate}/hour",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_muted"]
        )
        rate_label.pack(pady=(0, 10))
        
        self.system_frames[system.id] = card
    
    def _refresh_sessions(self):
        """Refresh active sessions display."""
        # Clear treeview
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)
        
        # Fetch active sessions
        sessions = self.session_service.get_active_sessions()
        
        if not sessions:
            # Show empty state
            self.sessions_tree.insert("", "end", values=("", "No active sessions", "", "", ""))
            return
        
        # Add sessions to treeview with live elapsed times
        from app.utils.time_utils import calculate_elapsed_seconds, format_duration_with_seconds
        
        for session in sessions:
            # Calculate current elapsed time (in seconds)
            try:
                elapsed_seconds = calculate_elapsed_seconds(session.login_time)
                duration_str = format_duration_with_seconds(elapsed_seconds)
            except:
                duration_str = "N/A"
            
            # Format display values
            system_name = session.system_name
            customer = session.customer_name
            rate = f"{session.hourly_rate}"
            total = f"{session.total_due:.0f}" if session.total_due else "Calculating..."
            
            self.sessions_tree.insert(
                "",
                "end",
                values=(system_name, customer, duration_str, rate, total)
            )
    
    def _show_start_session(self):
        """Show start session dialog."""
        from app.ui.dialogs.start_session_dialog import StartSessionDialog
        StartSessionDialog(self.parent, self.db, on_success=self.refresh)
    
    def _on_session_double_click(self, event):
        """Handle double-click on session to end it."""
        selected = self.sessions_tree.selection()
        if not selected:
            return
        
        # Get the selected session's index
        item = selected[0]
        values = self.sessions_tree.item(item)["values"]
        
        # Find the session by system and customer name
        sessions = self.session_service.get_active_sessions()
        for session in sessions:
            if session.system_name == values[0] and session.customer_name == values[1]:
                self._show_end_session_dialog(session.id)
                break
    
    def _show_end_session_dialog(self, session_id: int):
        """Show end session dialog."""
        from app.ui.dialogs.end_session_dialog import EndSessionDialog
        EndSessionDialog(self.parent, self.db, session_id, on_success=self.refresh)
    
    def _schedule_timer_update(self):
        """Schedule periodic updates of elapsed times for active sessions."""
        # Update every 1 second (1000ms) for real-time display with seconds
        self._update_elapsed_times()
        self.timer_id = self.parent.after(1000, self._schedule_timer_update)
    
    def _update_elapsed_times(self):
        """Update elapsed times in the sessions treeview without full refresh."""
        from app.utils.time_utils import calculate_elapsed_seconds, format_duration_with_seconds
        
        # Get current items in treeview
        items = self.sessions_tree.get_children()
        if not items:
            return
        
        # Fetch active sessions
        sessions = self.session_service.get_active_sessions()
        if not sessions:
            return
        
        # Update each item's duration
        for i, item in enumerate(items):
            if i < len(sessions):
                session = sessions[i]
                try:
                    elapsed_seconds = calculate_elapsed_seconds(session.login_time)
                    duration_str = format_duration_with_seconds(elapsed_seconds)
                    
                    # Get current values
                    values = list(self.sessions_tree.item(item)["values"])
                    # Update duration (column index 2)
                    values[2] = duration_str
                    
                    # Update the row
                    self.sessions_tree.item(item, values=values)
                except Exception:
                    pass  # Skip on error, next full refresh will handle it
    
    def stop_timer(self):
        """Stop the timer when closing the dashboard."""
        if self.timer_id:
            self.parent.after_cancel(self.timer_id)
            self.timer_id = None
