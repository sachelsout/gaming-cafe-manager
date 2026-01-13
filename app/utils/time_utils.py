"""Utility functions for time and billing calculations."""

from datetime import datetime, time


def calculate_duration_minutes(login_time: str, logout_time: str) -> int:
    """
    Calculate session duration in minutes.
    
    Duration in minutes is the source of truth.
    
    Args:
        login_time: Login time in HH:MM:SS format
        logout_time: Logout time in HH:MM:SS format
    
    Returns:
        Duration in minutes (integer)
    
    Handles overnight sessions where logout_time < login_time.
    """
    try:
        login = datetime.strptime(login_time, "%H:%M:%S").time()
        logout = datetime.strptime(logout_time, "%H:%M:%S").time()
        
        # Convert to minutes since midnight
        login_minutes = login.hour * 60 + login.minute
        logout_minutes = logout.hour * 60 + logout.minute
        
        if logout_minutes < login_minutes:
            # Overnight session - went past midnight
            total_minutes = (24 * 60 - login_minutes) + logout_minutes
        else:
            # Same day session
            total_minutes = logout_minutes - login_minutes
        
        return max(0, total_minutes)  # Ensure non-negative
    
    except ValueError as e:
        raise ValueError(f"Invalid time format. Expected HH:MM:SS. Error: {e}")


def format_duration(duration_minutes: int) -> str:
    """
    Format duration in minutes to human-readable HH:MM format.
    
    Args:
        duration_minutes: Duration in minutes
    
    Returns:
        Formatted string like "2h 15m"
    """
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    
    if hours == 0:
        return f"{minutes}m"
    elif minutes == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {minutes}m"


def format_duration_with_seconds(duration_seconds: int) -> str:
    """
    Format duration in seconds to human-readable HH:MM:SS format.
    
    Args:
        duration_seconds: Duration in seconds
    
    Returns:
        Formatted string like "2h 15m 30s" or "15m 30s" or "30s"
    """
    hours = duration_seconds // 3600
    remaining = duration_seconds % 3600
    minutes = remaining // 60
    seconds = remaining % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:  # Show minutes if hours exist
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")  # Always show seconds
    
    return " ".join(parts)


def calculate_bill(duration_minutes: int, hourly_rate: float, extra_charges: float = 0.0) -> float:
    """
    Calculate total billing amount.
    
    Formula: total = (hourly_rate × (duration_minutes / 60)) + extra_charges
    
    Args:
        duration_minutes: Session duration in minutes (source of truth)
        hourly_rate: Hourly rate in currency
        extra_charges: Additional charges (default 0.0)
    
    Returns:
        Total due amount (float), rounded to 2 decimal places
    """
    hours = duration_minutes / 60
    base_amount = hourly_rate * hours
    total = base_amount + extra_charges
    return round(total, 2)


def get_current_time_string() -> str:
    """Get current time as HH:MM:SS string."""
    return datetime.now().strftime("%H:%M:%S")


def calculate_elapsed_minutes(login_time: str) -> int:
    """
    Calculate elapsed minutes since login.
    
    Handles overnight sessions where current time might be on a different day.
    
    Args:
        login_time: Login time in HH:MM:SS format
    
    Returns:
        Elapsed time in minutes (integer)
    """
    try:
        login = datetime.strptime(login_time, "%H:%M:%S").time()
        now = datetime.now().time()
        
        # Convert to minutes since midnight
        login_minutes = login.hour * 60 + login.minute
        now_minutes = now.hour * 60 + now.minute
        
        if now_minutes < login_minutes:
            # Overnight session - went past midnight
            elapsed = (24 * 60 - login_minutes) + now_minutes
        else:
            # Same day session
            elapsed = now_minutes - login_minutes
        
        return max(0, elapsed)
    
    except ValueError as e:
        raise ValueError(f"Invalid time format. Expected HH:MM:SS. Error: {e}")


def calculate_elapsed_seconds(login_time: str) -> int:
    """
    Calculate elapsed seconds since login (includes minutes converted to seconds).
    
    Handles overnight sessions where current time might be on a different day.
    
    Args:
        login_time: Login time in HH:MM:SS format
    
    Returns:
        Elapsed time in seconds (integer)
    """
    try:
        login_dt = datetime.strptime(login_time, "%H:%M:%S")
        now_dt = datetime.now()
        
        # Convert to total seconds since midnight
        login_seconds = login_dt.hour * 3600 + login_dt.minute * 60 + login_dt.second
        now_seconds = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
        
        if now_seconds < login_seconds:
            # Overnight session - went past midnight
            elapsed = (24 * 3600 - login_seconds) + now_seconds
        else:
            # Same day session
            elapsed = now_seconds - login_seconds
        
        return max(0, elapsed)
    
    except ValueError as e:
        raise ValueError(f"Invalid time format. Expected HH:MM:SS. Error: {e}")
