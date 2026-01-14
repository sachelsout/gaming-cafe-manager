"""Database backup and restore dialog."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional, Callable
from app.ui.styles import COLORS, FONTS
from app.db.path_manager import DatabaseBackupManager
from app.ui.dialogs.error_dialog import show_error, show_success, show_warning


class BackupManagerDialog:
    """Dialog for managing database backups."""
    
    def __init__(self, parent: tk.Widget, db_path: Path, on_backup_created: Optional[Callable] = None):
        """
        Initialize backup manager dialog.
        
        Args:
            parent: Parent widget
            db_path: Path to the database file
            on_backup_created: Optional callback when backup is created
        """
        self.parent = parent
        self.db_path = db_path
        self.backup_manager = DatabaseBackupManager(db_path)
        self.on_backup_created = on_backup_created
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Database Backup Manager")
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
        self._refresh_backups()
    
    def _create_ui(self):
        """Create dialog UI components."""
        # Main container
        container = ttk.Frame(self.dialog)
        container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Title
        title_label = ttk.Label(container, text="Database Backup Manager", style="Title.TLabel")
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Info section
        info_frame = ttk.LabelFrame(container, text="Database Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        db_label = ttk.Label(info_frame, text="Database Location:")
        db_label.pack(anchor=tk.W)
        db_value = ttk.Label(info_frame, text=str(self.db_path), foreground="gray")
        db_value.pack(anchor=tk.W, pady=(0, 5))
        
        backups_label = ttk.Label(info_frame, text="Backups Location:")
        backups_label.pack(anchor=tk.W)
        backups_value = ttk.Label(info_frame, text=str(self.backup_manager.backups_dir), foreground="gray")
        backups_value.pack(anchor=tk.W)
        
        # Action buttons
        action_frame = ttk.Frame(container)
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
        create_btn = ttk.Button(action_frame, text="Create Backup Now", command=self._create_backup)
        create_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        refresh_btn = ttk.Button(action_frame, text="Refresh", command=self._refresh_backups)
        refresh_btn.pack(side=tk.LEFT)
        
        # Backups list section
        list_label = ttk.Label(container, text="Available Backups", style="Heading.TLabel")
        list_label.pack(anchor=tk.W, pady=(10, 5))
        
        # Create treeview for backups
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        self.backups_tree = ttk.Treeview(
            tree_frame,
            columns=("Created", "Size"),
            height=12,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.backups_tree.yview)
        
        # Configure columns
        self.backups_tree.column("#0", width=250)
        self.backups_tree.heading("#0", text="Backup File")
        self.backups_tree.column("Created", width=180)
        self.backups_tree.heading("Created", text="Created")
        self.backups_tree.column("Size", width=80)
        self.backups_tree.heading("Size", text="Size")
        
        self.backups_tree.pack(fill=tk.BOTH, expand=True)
        
        # Backup details
        details_frame = ttk.LabelFrame(container, text="Backup Details", padding=10)
        details_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.details_label = ttk.Label(details_frame, text="Select a backup to see details", wraplength=600)
        self.details_label.pack(anchor=tk.W)
        
        # Bind selection event
        self.backups_tree.bind("<<TreeviewSelect>>", self._on_backup_selected)
        
        # Button frame
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X)
        
        restore_btn = ttk.Button(button_frame, text="Restore Selected", command=self._restore_backup)
        restore_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_btn = ttk.Button(button_frame, text="Delete Selected", command=self._delete_backup)
        delete_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        open_btn = ttk.Button(button_frame, text="Open Backups Folder", command=self._open_backups_folder)
        open_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        close_btn = ttk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_btn.pack(side=tk.RIGHT)
    
    def _refresh_backups(self):
        """Refresh the backup list."""
        # Clear existing items
        for item in self.backups_tree.get_children():
            self.backups_tree.delete(item)
        
        # Load backups
        try:
            backups = self.backup_manager.list_backups()
            
            for backup_path, description in backups:
                info = self.backup_manager.get_backup_info(backup_path)
                created = info.get("created_formatted", "Unknown")
                size = f"{info.get('size_mb', 0)} MB"
                
                # Create display text with description if available
                display_name = backup_path.name
                if description:
                    display_name += f" ({description})"
                
                self.backups_tree.insert("", "end", iid=str(backup_path), text=display_name, values=(created, size))
            
            if not backups:
                self.details_label.config(text="No backups available. Click 'Create Backup Now' to create one.")
        
        except Exception as e:
            show_error(self.dialog, "Error Loading Backups", str(e))
    
    def _on_backup_selected(self, event=None):
        """Handle backup selection."""
        selection = self.backups_tree.selection()
        if not selection:
            self.details_label.config(text="Select a backup to see details")
            return
        
        backup_path = Path(selection[0])
        try:
            info = self.backup_manager.get_backup_info(backup_path)
            
            details_text = f"Filename: {info['filename']}\n"
            details_text += f"Created: {info['created_formatted']}\n"
            details_text += f"Size: {info['size_mb']} MB\n"
            if info['description']:
                details_text += f"Description: {info['description']}"
            
            self.details_label.config(text=details_text)
        
        except Exception as e:
            show_error(self.dialog, "Error Reading Backup Info", str(e))
    
    def _create_backup(self):
        """Create a new backup."""
        try:
            # Ask for optional description
            description = tk.simpledialog.askstring(
                "Backup Description",
                "Enter an optional description for this backup:",
                parent=self.dialog
            )
            
            backup_path = self.backup_manager.create_backup(description=description)
            
            show_success(self.dialog, "Backup Created", f"Backup saved to:\n{backup_path.name}")
            
            # Refresh list
            self._refresh_backups()
            
            # Call callback if provided
            if self.on_backup_created:
                self.on_backup_created(backup_path)
        
        except FileNotFoundError as e:
            show_error(self.dialog, "Database Not Found", str(e))
        except IOError as e:
            show_error(self.dialog, "Backup Failed", str(e))
        except Exception as e:
            show_error(self.dialog, "Error Creating Backup", str(e))
    
    def _restore_backup(self):
        """Restore a backup."""
        selection = self.backups_tree.selection()
        if not selection:
            show_warning(self.dialog, "No Selection", "Please select a backup to restore.")
            return
        
        backup_path = Path(selection[0])
        
        # Confirm restoration
        confirm = messagebox.askyesno(
            "Confirm Restore",
            f"Restore from {backup_path.name}?\n\n"
            "Your current database will be saved as a safety backup.",
            parent=self.dialog
        )
        
        if not confirm:
            return
        
        try:
            self.backup_manager.restore_backup(backup_path)
            show_success(self.dialog, "Backup Restored", "Database restored successfully.")
            
            # Refresh list
            self._refresh_backups()
        
        except FileNotFoundError as e:
            show_error(self.dialog, "Backup Not Found", str(e))
        except IOError as e:
            show_error(self.dialog, "Restore Failed", str(e))
        except Exception as e:
            show_error(self.dialog, "Error Restoring Backup", str(e))
    
    def _delete_backup(self):
        """Delete a backup."""
        selection = self.backups_tree.selection()
        if not selection:
            show_warning(self.dialog, "No Selection", "Please select a backup to delete.")
            return
        
        backup_path = Path(selection[0])
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete {backup_path.name}?\n\nThis cannot be undone.",
            parent=self.dialog
        )
        
        if not confirm:
            return
        
        try:
            success = self.backup_manager.delete_backup(backup_path)
            if success:
                show_success(self.dialog, "Backup Deleted", "Backup deleted successfully.")
                self._refresh_backups()
            else:
                show_error(self.dialog, "Delete Failed", "Could not delete backup.")
        
        except Exception as e:
            show_error(self.dialog, "Error Deleting Backup", str(e))
    
    def _open_backups_folder(self):
        """Open the backups folder in file explorer."""
        try:
            import subprocess
            import platform
            
            backups_path = self.backup_manager.backups_dir
            
            if platform.system() == "Windows":
                subprocess.Popen(f'explorer /select,"{backups_path}"')
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", str(backups_path)])
            else:  # Linux
                subprocess.Popen(["xdg-open", str(backups_path)])
        
        except Exception as e:
            show_error(self.dialog, "Error Opening Folder", f"Could not open backups folder:\n{str(e)}")


# Import here to avoid circular imports
import tkinter.simpledialog
