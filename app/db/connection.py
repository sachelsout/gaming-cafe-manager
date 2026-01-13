"""Database connection and management."""

import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple, Any


class DatabaseConnection:
    """Manages SQLite database connection and basic operations."""
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
    
    def connect(self) -> sqlite3.Connection:
        """
        Establish database connection.
        
        Returns:
            sqlite3.Connection object
        """
        if self._connection is None:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create connection with row factory for dict-like access
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """
        Execute a database query.
        
        Args:
            query: SQL query string
            params: Query parameters (for safe parameterized queries)
        
        Returns:
            sqlite3.Cursor object
        """
        conn = self.connect()
        return conn.execute(query, params)
    
    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        """
        Fetch single row from database.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            Single row as sqlite3.Row or None
        """
        cursor = self.execute(query, params)
        return cursor.fetchone()
    
    def fetch_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        """
        Fetch all rows from database.
        
        Args:
            query: SQL query string
            params: Query parameters
        
        Returns:
            List of rows as sqlite3.Row objects
        """
        cursor = self.execute(query, params)
        return cursor.fetchall()
    
    def insert(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """
        Insert a row and return the last inserted row ID.
        
        Args:
            query: INSERT query string
            params: Query parameters
        
        Returns:
            Last inserted row ID
        """
        cursor = self.execute(query, params)
        self.commit()
        return cursor.lastrowid
    
    def update(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """
        Update rows in database.
        
        Args:
            query: UPDATE query string
            params: Query parameters
        
        Returns:
            Number of rows affected
        """
        cursor = self.execute(query, params)
        self.commit()
        return cursor.rowcount
    
    def delete(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """
        Delete rows from database.
        
        Args:
            query: DELETE query string
            params: Query parameters
        
        Returns:
            Number of rows deleted
        """
        cursor = self.execute(query, params)
        self.commit()
        return cursor.rowcount
    
    def commit(self):
        """Commit current transaction."""
        conn = self.connect()
        conn.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        conn = self.connect()
        conn.rollback()
    
    def execute_script(self, script: str):
        """
        Execute a SQL script (useful for schema creation).
        
        Args:
            script: SQL script as string
        """
        conn = self.connect()
        conn.executescript(script)
        conn.commit()
