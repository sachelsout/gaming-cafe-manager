"""UI themes and styling for the application."""

from tkinter import font as tk_font

# Dark theme color palette
COLORS = {
    # Backgrounds
    "bg_dark": "#1e1e1e",        # Main background (dark gray)
    "bg_darker": "#121212",      # Darker background
    "bg_card": "#2d2d2d",        # Card/panel background
    
    # Text
    "text_primary": "#ffffff",   # Main text (white)
    "text_secondary": "#b0b0b0", # Secondary text (light gray)
    "text_muted": "#808080",     # Muted text (medium gray)
    
    # Status colors
    "status_available": "#2ecc71",  # Green - Available
    "status_in_use": "#3498db",     # Blue - In Use
    "status_offline": "#e74c3c",    # Red - Offline/Error
    "status_pending": "#f39c12",    # Orange - Pending
    
    # Accents
    "accent_primary": "#0078d4",    # Windows blue
    "accent_hover": "#1084d7",      # Darker blue on hover
    
    # Borders and dividers
    "border": "#404040",            # Border color
}

# Fonts
FONTS = {
    "title": ("Segoe UI", 16, "bold"),
    "heading": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
}

# Configure ttk style for dark theme
def configure_dark_theme():
    """Configure ttk styles for dark theme."""
    from tkinter import ttk
    
    style = ttk.Style()
    style.theme_use("clam")
    
    # Frame style
    style.configure("TFrame", background=COLORS["bg_dark"], relief="flat")
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")
    
    # Label style
    style.configure("TLabel", 
                   background=COLORS["bg_dark"],
                   foreground=COLORS["text_primary"],
                   font=FONTS["body"])
    style.configure("Title.TLabel",
                   background=COLORS["bg_dark"],
                   foreground=COLORS["text_primary"],
                   font=FONTS["title"])
    style.configure("Heading.TLabel",
                   background=COLORS["bg_dark"],
                   foreground=COLORS["text_primary"],
                   font=FONTS["heading"])
    
    # Button style
    style.configure("TButton",
                   background=COLORS["accent_primary"],
                   foreground=COLORS["text_primary"],
                   font=FONTS["body"],
                   relief="flat",
                   padding=5)
    style.map("TButton",
             background=[("active", COLORS["accent_hover"])])
    
    # Treeview style
    style.configure("Treeview",
                   background=COLORS["bg_card"],
                   foreground=COLORS["text_primary"],
                   fieldbackground=COLORS["bg_card"],
                   font=FONTS["body"])
    style.configure("Treeview.Heading",
                   background=COLORS["bg_darker"],
                   foreground=COLORS["text_primary"],
                   font=FONTS["heading"])
    style.map("Treeview",
             background=[("selected", COLORS["accent_primary"])],
             foreground=[("selected", COLORS["text_primary"])])
