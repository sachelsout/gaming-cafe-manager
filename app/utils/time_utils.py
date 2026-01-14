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
    Format duration in minutes to human-readable format with leading zeros.
    
    Args:
        duration_minutes: Duration in minutes
    
    Returns:
        Formatted string like "01h30m", "02h00m", "00h45m"
    """
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    return f"{hours:02d}h{minutes:02d}m"


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
    """Get current time as HH:MM:SS string (24-hour format for storage)."""
    return datetime.now().strftime("%H:%M:%S")


def format_time_12hr(time_24hr: str) -> str:
    """
    Convert 24-hour time to 12-hour format with AM/PM.
    
    Args:
        time_24hr: Time in HH:MM:SS format (24-hour)
    
    Returns:
        Time in HH:MM AM/PM format (12-hour)
    """
    try:
        dt = datetime.strptime(time_24hr, "%H:%M:%S")
        return dt.strftime("%I:%M %p")
    except ValueError:
        raise ValueError(f"Invalid time format. Expected HH:MM:SS. Got: {time_24hr}")


def parse_time_12hr(time_12hr: str) -> str:
    """
    Convert 12-hour time with AM/PM to 24-hour HH:MM:SS format.
    
    Args:
        time_12hr: Time in HH:MM AM/PM or H:MM AM/PM format
    
    Returns:
        Time in HH:MM:SS format (24-hour)
    """
    try:
        # Try parsing with space between time and AM/PM
        dt = datetime.strptime(time_12hr.strip(), "%I:%M %p")
        return dt.strftime("%H:%M:%S")
    except ValueError:
        try:
            # Try other formats
            dt = datetime.strptime(time_12hr.strip(), "%I:%M%p")
            return dt.strftime("%H:%M:%S")
        except ValueError:
            raise ValueError(f"Invalid 12-hour time format. Use HH:MM AM/PM or H:MM AM/PM. Got: {time_12hr}")


def get_current_time_12hr() -> str:
    """Get current time in 12-hour AM/PM format for display."""
    return datetime.now().strftime("%I:%M %p")


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

def parse_time_24hr_to_datetime(time_24hr: str) -> datetime:
    """
    Convert 24-hour time string to datetime object with today's date.
    
    Args:
        time_24hr: Time in HH:MM:SS format (24-hour)
    
    Returns:
        datetime object with today's date and given time
    """
    try:
        return datetime.strptime(time_24hr, "%H:%M:%S").replace(
            year=datetime.now().year,
            month=datetime.now().month,
            day=datetime.now().day
        )
    except ValueError:
        raise ValueError(f"Invalid time format. Expected HH:MM:SS. Got: {time_24hr}")