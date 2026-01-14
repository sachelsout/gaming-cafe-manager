"""Data validation utilities for the gaming cafe application."""

import re
from typing import Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_customer_name(name: str) -> Tuple[bool, str]:
    """
    Validate customer name.
    
    Args:
        name: Customer name to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not name or not name.strip():
        return False, "Customer name cannot be empty."
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Customer name must be at least 2 characters long."
    
    if len(name) > 100:
        return False, "Customer name cannot exceed 100 characters."
    
    # Check for valid characters (letters, numbers, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z0-9\s\-']+$", name):
        return False, "Customer name contains invalid characters. Use letters, numbers, spaces, hyphens, or apostrophes."
    
    return True, ""


def validate_time_format(time_str: str) -> Tuple[bool, str]:
    """
    Validate time format (accepts both 12-hour and 24-hour formats).
    
    Args:
        time_str: Time string to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not time_str or not time_str.strip():
        return False, "Time cannot be empty."
    
    time_str = time_str.strip()
    
    # Pattern for 12-hour format: H:MM AM/PM or HH:MM AM/PM (with optional space)
    # Allows 1-12 for hours, with or without leading zero
    pattern_12hr = r"^([1-9]|0[1-9]|1[0-2]):[0-5][0-9]\s*(AM|PM|am|pm)$"
    
    # Pattern for 24-hour format: HH:MM or H:MM
    pattern_24hr = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    
    if re.match(pattern_12hr, time_str) or re.match(pattern_24hr, time_str):
        return True, ""
    
    return False, "Invalid time format. Use HH:MM AM/PM (e.g., 2:30 PM) or HH:MM in 24-hour format."


def validate_hourly_rate(rate: str) -> Tuple[bool, str]:
    """
    Validate hourly rate.
    
    Args:
        rate: Rate string to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not rate or not rate.strip():
        return False, "Hourly rate cannot be empty."
    
    try:
        rate_float = float(rate.strip())
        if rate_float <= 0:
            return False, "Hourly rate must be greater than 0."
        if rate_float > 10000:
            return False, "Hourly rate seems too high. Please verify."
        return True, ""
    except ValueError:
        return False, "Hourly rate must be a valid number (e.g., 50.00)."


def validate_extra_charges(charges: str) -> Tuple[bool, str]:
    """
    Validate extra charges amount.
    
    Args:
        charges: Charges string to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not charges or not charges.strip():
        return False, "Extra charges cannot be empty."
    
    try:
        charges_float = float(charges.strip())
        if charges_float < 0:
            return False, "Extra charges cannot be negative."
        if charges_float > 100000:
            return False, "Extra charges amount seems too high. Please verify."
        return True, ""
    except ValueError:
        return False, "Extra charges must be a valid number (e.g., 10.50)."


def validate_notes(notes: str) -> Tuple[bool, str]:
    """
    Validate notes field.
    
    Args:
        notes: Notes text to validate
    
    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not notes:
        return True, ""
    
    if len(notes) > 500:
        return False, "Notes cannot exceed 500 characters."
    
    return True, ""
