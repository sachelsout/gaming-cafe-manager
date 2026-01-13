"""Main dashboard component showing systems and active sessions."""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from app.ui.styles import COLORS, FONTS
from app.services.system_service import SystemService
from app.services.session_service import SessionService
from app.db.connection import DatabaseConnection


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
        
        # Create main container
        self.container = ttk.Frame(parent)
        self.container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Build UI
        self._create_header()
        self._create_content()
        
        # Store references for updates
        self.system_frames = {}
        self.refresh()
    
    def _create_header(self):
        """Create dashboard header with title and refresh button."""
        header = ttk.Frame(self.container)
        header.pack(fill=tk.X, pady=(0, 10))
        
        title = ttk.Label(header, text="Gaming Cafe Dashboard", style="Title.TLabel")
        title.pack(side=tk.LEFT)
        
        refresh_btn = ttk.Button(header, text="🔄 Refresh", command=self.refresh)
        refresh_btn.pack(side=tk.RIGHT)
    
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
        
        # Add sessions to treeview
        for session in sessions:
            # Calculate current duration
            from datetime import datetime
            try:
                login = datetime.strptime(session.login_time, "%H:%M:%S")
                now = datetime.now().replace(second=0, microsecond=0)
                duration = now - login.replace(year=now.year, month=now.month, day=now.day)
                duration_str = f"{int(duration.total_seconds() // 60)} min"
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
