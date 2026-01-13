"""Database initialization and setup."""

from pathlib import Path
from app.db.connection import DatabaseConnection


# Default database location
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "data" / "cafe.db"


def get_database(db_path: Path = DEFAULT_DB_PATH) -> DatabaseConnection:
    """
    Get or create the database connection.
    
    Args:
        db_path: Path to the database file (defaults to data/cafe.db)
    
    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection(db_path)


def initialize_database(db_path: Path = DEFAULT_DB_PATH) -> DatabaseConnection:
    """
    Initialize the database by creating tables and default data if needed.
    
    This function:
    1. Creates the database file if it doesn't exist
    2. Executes the schema to create tables if they don't exist
    3. Inserts default systems if the systems table is empty
    
    Args:
        db_path: Path to the database file (defaults to data/cafe.db)
    
    Returns:
        DatabaseConnection instance
    
    Raises:
        RuntimeError: If schema execution fails
    """
    try:
        # Get database connection
        db = get_database(db_path)
        db.connect()
        
        # Load and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema = f.read()
        
        db.execute_script(schema)
        
        # Insert default systems if the table is empty
        _initialize_default_systems(db)
        
        return db
    
    except Exception as e:
        raise RuntimeError(f"Failed to initialize database: {str(e)}") from e


def _initialize_default_systems(db: DatabaseConnection):
    """
    Insert default gaming systems if the systems table is empty.
    
    Default rates in PKR (Pakistani Rupees):
    - PlayStation 4: 200/hour (older console)
    - PlayStation 5: 250/hour (newer console)
    - Xbox One: 200/hour
    - PC Gaming: 300/hour (higher demand)
    
    Args:
        db: DatabaseConnection instance
    """
    # Check if systems table has data
    result = db.fetch_one("SELECT COUNT(*) as count FROM systems")
    
    if result["count"] == 0:
        # Insert default systems with types and rates
        default_systems = [
            ("PS-4", "PlayStation", 200.0),
            ("PS-5", "PlayStation", 250.0),
            ("XB-01", "Xbox", 200.0),
            ("XB-02", "Xbox", 200.0),
            ("PC-01", "PC Gaming", 300.0),
            ("PC-02", "PC Gaming", 300.0),
        ]
        
        for system_name, system_type, hourly_rate in default_systems:
            db.insert(
                "INSERT INTO systems (system_name, system_type, default_hourly_rate) VALUES (?, ?, ?)",
                (system_name, system_type, hourly_rate)
            )
