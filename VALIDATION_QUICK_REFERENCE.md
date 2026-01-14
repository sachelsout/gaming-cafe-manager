# Quick Reference: Data Validation & Error Handling

## What Changed

### New Files
1. **app/utils/validators.py** - Input validation utilities
2. **app/ui/dialogs/error_dialog.py** - User-friendly error dialogs

### Enhanced Files
1. **app/ui/dialogs/start_session_dialog.py** - Comprehensive input validation
2. **app/ui/dialogs/end_session_dialog.py** - Comprehensive input validation
3. **app/services/session_service.py** - Service-level validation + SessionError

## User-Facing Changes

### Starting a Session
- ❌ Empty customer names are rejected
- ❌ Invalid times (wrong format) are rejected
- ❌ Invalid hourly rates (negative, zero, non-numeric) are rejected
- ✅ Clear error messages explain what's wrong
- ✅ Can immediately retry after fixing the issue

Example error: "Customer name must be at least 2 characters long."

### Ending a Session
- ❌ Invalid logout times are rejected
- ❌ Logout time before login time is rejected
- ❌ Invalid extra charges are rejected
- ✅ Unreasonably high amounts trigger verification
- ✅ Database errors don't crash the application

Example error: "Logout time must be after login time."

### Time Input Format
Both formats now accepted:
- ✅ 12-hour: `2:30 PM` or `02:30 PM` (space optional)
- ✅ 24-hour: `14:30`

## Technical Details

### Validation Flow
```
User Input
    ↓
Dialog Validation (validate_*)
    ↓
Service-Level Validation
    ↓
Database Operation
    ↓
Error Handling (show_error)
```

### Error Hierarchy
```
InputError (Dialog Level)
    ↓
SessionError (Service Level)
    ↓
DatabaseError (wrapped by SessionError)
    ↓
Generic Error Dialog (User Sees)
```

### Validation Rules Quick Reference
| Field | Requirements | Examples |
|-------|--------------|----------|
| Customer Name | 2-100 chars, alphanumeric + spaces/hyphens/apostrophes | "John Doe", "Mary-Jane" ✓<br>"A", "@John", "" ✗ |
| Login/Logout Time | HH:MM (12/24-hour), valid hours/minutes | "2:30 PM", "14:30" ✓<br>"25:00", "2:70 PM" ✗ |
| Hourly Rate | Positive number, max 10000 | "50", "50.50" ✓<br>"0", "-50", "abc" ✗ |
| Extra Charges | Non-negative number, max 100000 | "0", "10.50" ✓<br>"-10", "abc" ✗ |
| Notes | Max 500 characters | "Optional text" ✓<br>"Very long text..." (501+ chars) ✗ |

## Testing Validation

To test validation in the UI:
1. Try leaving customer name empty → See "Customer name cannot be empty"
2. Try entering "A" → See "Customer name must be at least 2 characters"
3. Try entering "25:00" for time → See "Invalid time format..."
4. Try entering "-50" for rate → See "Hourly rate must be greater than 0"
5. Try entering "abc" for charges → See "Extra charges must be a valid number"

All validations show user-friendly messages, not technical errors.

## Database Error Handling

If a database error occurs:
- ✅ Application doesn't crash
- ✅ User sees: "An error occurred. Please check your data and try again."
- ✅ User can retry the operation
- ✅ Errors are logged for debugging

## Code Examples

### Using Validators in Custom Code
```python
from app.utils.validators import validate_customer_name, validate_hourly_rate

# Validate customer name
is_valid, error_msg = validate_customer_name("John Doe")
if not is_valid:
    show_validation_error(parent, error_msg)

# Validate rate
is_valid, error_msg = validate_hourly_rate("50.00")
if not is_valid:
    show_validation_error(parent, error_msg)
```

### Showing Errors to User
```python
from app.ui.dialogs.error_dialog import show_error, show_validation_error, show_success

# Validation error
show_validation_error(parent_widget, "Invalid customer name")

# Database error
show_error(parent_widget, "Database Error", "Failed to save session")

# Success
show_success(parent_widget, "Success", "Session saved successfully")
```

## Acceptance Criteria Status

- ✅ App does not crash on invalid input
  - Validation catches errors before database operations
  - Exception handling wraps all database calls
  
- ✅ Clear error messages shown to the user
  - Validation errors describe the problem
  - Database errors provide recovery guidance
  - User-friendly language throughout

## Performance Notes

Validation functions are lightweight:
- Regex-based pattern matching (< 1ms)
- String length checks (< 1ms)
- Type conversion attempts (< 1ms)

No performance impact on normal operations.
