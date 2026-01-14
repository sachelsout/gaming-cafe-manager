"""User-friendly error dialog component."""

import tkinter as tk
from tkinter import ttk, messagebox
from app.ui.styles import COLORS, FONTS


def show_error(parent: tk.Widget, title: str, message: str, details: str = None):
    """
    Show a user-friendly error dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main error message
        details: Optional technical details (shown in a collapsed section)
    """
    messagebox.showerror(title, message)


def show_validation_error(parent: tk.Widget, message: str):
    """
    Show a validation error dialog.
    
    Args:
        parent: Parent widget
        message: Validation error message
    """
    messagebox.showerror("Validation Error", message)


def show_database_error(parent: tk.Widget, operation: str = "operation", details: str = None):
    """
    Show a database error dialog with user-friendly message.
    
    Args:
        parent: Parent widget
        operation: What operation failed (e.g., "starting session", "ending session")
        details: Optional technical error details
    """
    message = f"Unable to complete {operation}.\n\nPlease check your data and try again. If the problem persists, contact support."
    if details:
        message += f"\n\nDetails: {details}"
    
    messagebox.showerror("Database Error", message)


def show_success(parent: tk.Widget, title: str, message: str):
    """
    Show a success message dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Success message
    """
    messagebox.showinfo(title, message)


def show_warning(parent: tk.Widget, title: str, message: str):
    """
    Show a warning dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Warning message
    """
    messagebox.showwarning(title, message)


def ask_confirmation(parent: tk.Widget, title: str, message: str) -> bool:
    """
    Show a confirmation dialog.
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Confirmation message
    
    Returns:
        True if user confirmed, False otherwise
    """
    return messagebox.askyesno(title, message)
