"""Manage Systems dialog for adding, editing, and deleting gaming systems."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable

from app.ui.styles import COLORS, FONTS
from app.services.system_service import SystemService
from app.db.connection import DatabaseConnection
from app.ui.dialogs.error_dialog import show_validation_error, show_error, show_success


class ManageSystemsDialog:
    """Dialog for managing gaming systems (add, edit, delete)."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, on_success: Optional[Callable] = None):
        """
        Initialize manage systems dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            on_success: Optional callback when systems are modified
        """
        self.parent = parent
        self.db = db
        self.on_success = on_success
        self.system_service = SystemService(db)
        self.selected_system = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manage Gaming Systems")
        self.dialog.geometry("700x500")
        self.dialog.resizable(True, True)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (700 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self._create_ui()
        self._load_systems()
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title = ttk.Label(main_frame, text="Gaming Systems", style="Heading.TLabel")
        title.pack(anchor=tk.W, pady=(0, 10))
        
        # Systems list section
        list_frame = ttk.LabelFrame(main_frame, text="Systems List", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Create treeview for systems
        self.systems_tree = ttk.Treeview(
            list_frame,
            columns=("name", "type", "rate", "status"),
            height=12,
            show="headings"
        )
        
        # Define columns
        self.systems_tree.column("name", width=150, anchor=tk.W)
        self.systems_tree.heading("name", text="System Name", anchor=tk.W)
        
        self.systems_tree.column("type", width=100, anchor=tk.W)
        self.systems_tree.heading("type", text="Type", anchor=tk.W)
        
        self.systems_tree.column("rate", width=100, anchor=tk.CENTER)
        self.systems_tree.heading("rate", text="Hourly Rate", anchor=tk.CENTER)
        
        self.systems_tree.column("status", width=100, anchor=tk.CENTER)
        self.systems_tree.heading("status", text="Status", anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.systems_tree.yview)
        self.systems_tree.configure(yscroll=scrollbar.set)
        
        self.systems_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection
        self.systems_tree.bind("<<TreeviewSelect>>", self._on_system_selected)
        
        # Action buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        add_btn = ttk.Button(button_frame, text="+ Add System", command=self._show_add_dialog)
        add_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        edit_btn = ttk.Button(button_frame, text="Edit Selected", command=self._show_edit_dialog)
        edit_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = ttk.Button(button_frame, text="Delete Selected", command=self._delete_system)
        delete_btn.pack(side=tk.LEFT)
        
        close_btn = ttk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def _load_systems(self):
        """Load and display all systems."""
        # Clear existing items
        for item in self.systems_tree.get_children():
            self.systems_tree.delete(item)
        
        # Fetch all systems
        systems = self.system_service.get_all_systems()
        
        # Add to treeview
        for system in systems:
            self.systems_tree.insert(
                "",
                "end",
                values=(
                    system.system_name,
                    system.system_type,
                    f"₹{system.default_hourly_rate:.2f}",
                    system.availability
                )
            )
    
    def _on_system_selected(self, event):
        """Handle system selection."""
        selected = self.systems_tree.selection()
        if selected:
            self.selected_system = selected[0]
        else:
            self.selected_system = None
    
    def _show_add_dialog(self):
        """Show dialog to add a new system."""
        SystemFormDialog(
            self.dialog,
            self.db,
            self.system_service,
            mode="add",
            on_success=self._on_form_success
        )
    
    def _show_edit_dialog(self):
        """Show dialog to edit selected system."""
        if not self.selected_system:
            messagebox.showwarning("No Selection", "Please select a system to edit.")
            return
        
        values = self.systems_tree.item(self.selected_system)["values"]
        system_name = values[0]
        
        # Get full system object
        systems = self.system_service.get_all_systems()
        system = next((s for s in systems if s.system_name == system_name), None)
        
        if system:
            SystemFormDialog(
                self.dialog,
                self.db,
                self.system_service,
                mode="edit",
                system=system,
                on_success=self._on_form_success
            )
    
    def _delete_system(self):
        """Delete selected system."""
        if not self.selected_system:
            messagebox.showwarning("No Selection", "Please select a system to delete.")
            return
        
        values = self.systems_tree.item(self.selected_system)["values"]
        system_name = values[0]
        
        try:
            # Get system ID
            systems = self.system_service.get_all_systems()
            system = next((s for s in systems if s.system_name == system_name), None)
            
            if not system:
                messagebox.showerror("Error", "System not found.")
                return
            
            # Check if system has any sessions
            result = self.db.fetch_one(
                "SELECT COUNT(*) as session_count FROM sessions WHERE system_id = ?",
                (system.id,)
            )
            
            session_count = result["session_count"] if result else 0
            
            # Confirm deletion
            msg = f"Are you sure you want to delete the system '{system_name}'?\n\nThis action cannot be undone."
            if session_count > 0:
                msg += f"\n\n({session_count} session record(s) will be preserved in history)"
            
            response = messagebox.askyesno("Confirm Delete", msg)
            
            if not response:
                return
            
            # Delete the system (sessions will be preserved with system_id set to NULL)
            rows_affected = self.db.delete(
                "DELETE FROM systems WHERE id = ?",
                (system.id,)
            )
            
            if rows_affected > 0:
                self._load_systems()
                msg = f"System '{system_name}' deleted successfully."
                if session_count > 0:
                    msg += f"\n{session_count} session record(s) are preserved in history."
                messagebox.showinfo("Success", msg)
                if self.on_success:
                    self.on_success()
            else:
                messagebox.showerror("Error", "Failed to delete system.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete system: {str(e)}")
    
    def _on_form_success(self):
        """Callback when system form succeeds."""
        self._load_systems()
        if self.on_success:
            self.on_success()


class SystemFormDialog:
    """Dialog for adding or editing a gaming system."""
    
    def __init__(self, parent: tk.Widget, db: DatabaseConnection, system_service: SystemService, 
                 mode: str = "add", system=None, on_success: Optional[Callable] = None):
        """
        Initialize system form dialog.
        
        Args:
            parent: Parent widget
            db: DatabaseConnection instance
            system_service: SystemService instance
            mode: "add" or "edit"
            system: System object (required for edit mode)
            on_success: Optional callback when form succeeds
        """
        self.parent = parent
        self.db = db
        self.system_service = system_service
        self.mode = mode
        self.system = system
        self.on_success = on_success
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{'Add' if mode == 'add' else 'Edit'} System")
        self.dialog.geometry("400x350")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg=COLORS["bg_dark"])
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (350 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Build UI
        self._create_ui()
    
    def _create_ui(self):
        """Create form UI."""
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # System name
        name_label = ttk.Label(container, text="System Name *", style="Heading.TLabel")
        name_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.name_var = tk.StringVar(value=self.system.system_name if self.system else "")
        name_entry = ttk.Entry(container, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky=tk.EW, pady=(0, 10))
        
        # System type
        type_label = ttk.Label(container, text="System Type *", style="Heading.TLabel")
        type_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        
        self.type_var = tk.StringVar(value=self.system.system_type if self.system else "")
        type_combo = ttk.Combobox(
            container,
            textvariable=self.type_var,
            values=["PC", "Xbox", "PlayStation", "Nintendo", "VR", "Other"],
            state="readonly",
            width=27
        )
        type_combo.grid(row=1, column=1, sticky=tk.EW, pady=(0, 10))
        
        # Hourly rate
        rate_label = ttk.Label(container, text="Hourly Rate (₹) *", style="Heading.TLabel")
        rate_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        self.rate_var = tk.StringVar(value=str(self.system.default_hourly_rate) if self.system else "100")
        rate_entry = ttk.Entry(container, textvariable=self.rate_var, width=30)
        rate_entry.grid(row=2, column=1, sticky=tk.EW, pady=(0, 20))
        
        # Configure grid
        container.grid_columnconfigure(1, weight=1)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(10, 0))
        
        save_btn = ttk.Button(button_frame, text="Save", command=self._save_system)
        save_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
    
    def _save_system(self):
        """Save the system."""
        # Validate inputs
        name = self.name_var.get().strip()
        sys_type = self.type_var.get().strip()
        rate_str = self.rate_var.get().strip()
        
        if not name:
            show_validation_error(self.dialog, "System name is required.")
            return
        
        if not sys_type:
            show_validation_error(self.dialog, "System type is required.")
            return
        
        try:
            rate = float(rate_str)
            if rate <= 0:
                raise ValueError("Rate must be greater than 0")
        except ValueError:
            show_validation_error(self.dialog, "Hourly rate must be a valid number greater than 0.")
            return
        
        try:
            if self.mode == "add":
                # Insert new system
                self.db.insert(
                    "INSERT INTO systems (system_name, system_type, default_hourly_rate, availability) VALUES (?, ?, ?, 'Available')",
                    (name, sys_type, rate)
                )
                show_success(self.dialog, "Success", f"System '{name}' added successfully.")
            else:
                # Update existing system
                self.db.update(
                    "UPDATE systems SET system_name = ?, system_type = ?, default_hourly_rate = ? WHERE id = ?",
                    (name, sys_type, rate, self.system.id)
                )
                show_success(self.dialog, "Success", f"System '{name}' updated successfully.")
            
            if self.on_success:
                self.on_success()
            
            self.dialog.destroy()
        
        except Exception as e:
            show_error(self.dialog, "Error", f"Failed to save system: {str(e)}")
