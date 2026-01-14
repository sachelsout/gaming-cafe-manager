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
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, timer_manager=None):
        """
        Initialize dashboard.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            timer_manager: Optional SessionTimerManager for managing session timers
        """
        self.parent = parent
        self.db = db
        self.timer_manager = timer_manager
        self.system_service = SystemService(db)
        self.session_service = SessionService(db)
        
        # Timer state
        self.timer_id = None
        self.flicker_state = {}  # Track flicker on/off state for each session
        self.flicker_toggle = True  # Toggle for flicker effect
        
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
        columns = ("System", "Customer", "Planned", "Remaining", "Rate", "Total")
        self.sessions_tree = ttk.Treeview(self.sessions_frame, columns=columns, height=8)
        
        # Define column headings
        self.sessions_tree.column("#0", width=0, stretch=tk.NO)
        self.sessions_tree.heading("#0", text="", anchor=tk.W)
        
        self.sessions_tree.column("System", anchor=tk.W, width=75)
        self.sessions_tree.heading("System", text="System", anchor=tk.W)
        
        self.sessions_tree.column("Customer", anchor=tk.W, width=100)
        self.sessions_tree.heading("Customer", text="Customer", anchor=tk.W)
        
        self.sessions_tree.column("Planned", anchor=tk.CENTER, width=70)
        self.sessions_tree.heading("Planned", text="Planned Hrs", anchor=tk.CENTER)
        
        self.sessions_tree.column("Remaining", anchor=tk.CENTER, width=80)
        self.sessions_tree.heading("Remaining", text="Time Left", anchor=tk.CENTER)
        
        self.sessions_tree.column("Rate", anchor=tk.CENTER, width=70)
        self.sessions_tree.heading("Rate", text="Rate/hr", anchor=tk.CENTER)
        
        self.sessions_tree.column("Total", anchor=tk.E, width=70)
        self.sessions_tree.heading("Total", text="Total Due", anchor=tk.CENTER)
        
        # Configure tags for row coloring
        self.sessions_tree.tag_configure("alert", background="#FF6B6B", foreground="white")    # Red for time exceeded
        
        self.sessions_tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.sessions_frame, orient=tk.VERTICAL, command=self.sessions_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sessions_tree.configure(yscroll=scrollbar.set)
        
        # Bind double-click to end session
        self.sessions_tree.bind("<Double-1>", self._on_session_double_click)
        
        # Bind right-click to context menu
        self.sessions_tree.bind("<Button-3>", self._on_session_right_click)
    
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
        
        # Refresh active sessions
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
        
        # Add sessions to treeview with remaining time
        for session in sessions:
            # Start/update timer for this session if timer_manager is available
            if self.timer_manager and session.planned_duration_min:
                timer = self.timer_manager.get_timer(session.id)
                if not timer:
                    # Start new timer for this session
                    self.timer_manager.add_session(
                        session_id=session.id,
                        customer_name=session.customer_name,
                        system_name=session.system_name,
                        planned_duration_min=session.planned_duration_min,
                        login_time_24hr=session.login_time
                    )
            
            # Get remaining time for display (if timer available)
            remaining_time_str = "N/A"
            if self.timer_manager and session.planned_duration_min:
                timer = self.timer_manager.get_timer(session.id)
                if timer:
                    remaining_time_str = timer.get_remaining_time_formatted()
            
            # Format planned duration in XhYm format
            from app.utils.time_utils import format_duration
            planned_str = format_duration(session.planned_duration_min) if session.planned_duration_min else "N/A"
            
            # Format display values
            system_name = session.system_name
            customer = session.customer_name
            rate = f"{session.hourly_rate}"
            total = f"{session.total_due:.0f}" if session.total_due else "Calculating..."
            
            self.sessions_tree.insert(
                "",
                "end",
                values=(system_name, customer, planned_str, remaining_time_str, rate, total)
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
    
    def _on_session_right_click(self, event):
        """Handle right-click on session to show context menu."""
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
                # Show context menu
                self._show_session_context_menu(session.id, event)
                break
    
    def _show_session_context_menu(self, session_id: int, event):
        """Show context menu for session actions."""
        menu = tk.Menu(self.sessions_tree, tearoff=False)
        menu.add_command(label="Extend Session", command=lambda: self._show_extend_session_dialog(session_id))
        menu.add_command(label="End Session", command=lambda: self._show_end_session_dialog(session_id))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def _show_extend_session_dialog(self, session_id: int):
        """Show dialog to extend session time."""
        from app.ui.dialogs.extend_session_dialog import ExtendSessionDialog
        
        ExtendSessionDialog(self.parent, self.db, session_id, self.timer_manager, on_success=self.refresh)
    
    def _show_end_session_dialog(self, session_id: int):
        """Show end session dialog."""
        from app.ui.dialogs.end_session_dialog import EndSessionDialog
        
        def on_end_success():
            # Stop timer for this session
            if self.timer_manager:
                self.timer_manager.remove_session(session_id)
            # Refresh dashboard
            self.refresh()
        
        EndSessionDialog(self.parent, self.db, session_id, on_success=on_end_success)
    
    def _schedule_timer_update(self):
        """Schedule periodic updates of remaining times for active sessions."""
        # Update every 200ms for smooth countdown display
        self._update_remaining_times()
        
        # Toggle flicker effect every 1 second (on for 1s, off for 1s = 2 second blink cycle)
        import time
        current_time = int(time.time() * 1000)  # milliseconds
        if current_time % 2000 < 1000:  # 1000ms on, 1000ms off pattern
            self.flicker_toggle = True
        else:
            self.flicker_toggle = False
        
        self._apply_flicker()
        self.timer_id = self.parent.after(200, self._schedule_timer_update)
    
    def _update_remaining_times(self):
        """Update remaining times in the sessions treeview without full refresh."""
        # Get current items in treeview
        items = self.sessions_tree.get_children()
        if not items:
            return
        
        # Fetch active sessions
        sessions = self.session_service.get_active_sessions()
        if not sessions:
            return
        
        # Clear flicker state and update each item's remaining time and apply color coding
        self.flicker_state.clear()
        for i, item in enumerate(items):
            if i < len(sessions):
                session = sessions[i]
                try:
                    # Get remaining time from timer manager
                    remaining_time_str = "N/A"
                    remaining_minutes = 0
                    if self.timer_manager and session.planned_duration_min:
                        timer = self.timer_manager.get_timer(session.id)
                        if timer:
                            remaining_time_str = timer.get_remaining_time_formatted()
                            remaining_minutes = timer.get_remaining_time()
                    
                    # Get current values
                    values = list(self.sessions_tree.item(item)["values"])
                    # Update remaining time (column index 3 - after System, Customer, Planned)
                    values[3] = remaining_time_str
                    
                    # Determine tag based on remaining time
                    tag_type = ""
                    if remaining_minutes <= 0:
                        # Time exceeded - red alert
                        tag_type = "alert"
                    
                    # Store flicker state for this item
                    if tag_type:
                        self.flicker_state[item] = tag_type
                    
                    # Update the row (without tag yet - will be applied by _apply_flicker)
                    self.sessions_tree.item(item, values=values, tags=())
                except Exception:
                    pass  # Skip on error, next full refresh will handle it
    
    def _apply_flicker(self):
        """Apply flicker effect to warning and alert rows."""
        # Apply tags only if flicker_toggle is True (on phase)
        for item, tag_type in self.flicker_state.items():
            if self.flicker_toggle:
                self.sessions_tree.item(item, tags=(tag_type,))
            else:
                self.sessions_tree.item(item, tags=())
    
    def stop_timer(self):
        """Stop the timer when closing the dashboard."""
        if self.timer_id:
            self.parent.after_cancel(self.timer_id)
            self.timer_id = None
