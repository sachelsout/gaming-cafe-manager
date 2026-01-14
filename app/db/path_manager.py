"""Database path and persistence management."""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


class DatabasePathManager:
    """Manages database paths and ensures they are outside the executable."""
    
    # Directory names
    APP_NAME = "GamingCafeManager"
    DATA_DIRNAME = "data"
    BACKUPS_DIRNAME = "backups"
    
    @staticmethod
    def get_app_data_dir() -> Path:
        """
        Get the application data directory.
        
        On Windows: %APPDATA%\GamingCafeManager\data
        On macOS: ~/Library/Application Support/GamingCafeManager/data
        On Linux: ~/.local/share/GamingCafeManager/data
        
        Returns:
            Path to the application data directory
        """
        if os.name == 'nt':  # Windows
            # Use Windows AppData directory
            appdata = os.getenv('APPDATA')
            if appdata:
                app_dir = Path(appdata) / DatabasePathManager.APP_NAME
            else:
                # Fallback to home directory
                app_dir = Path.home() / "AppData" / "Roaming" / DatabasePathManager.APP_NAME
        elif os.name == 'posix':
            # macOS and Linux
            if os.uname().sysname == 'Darwin':  # macOS
                app_dir = Path.home() / "Library" / "Application Support" / DatabasePathManager.APP_NAME
            else:  # Linux
                app_dir = Path.home() / ".local" / "share" / DatabasePathManager.APP_NAME
        else:
            # Fallback to home directory
            app_dir = Path.home() / DatabasePathManager.APP_NAME
        
        return app_dir
    
    @staticmethod
    def get_data_dir() -> Path:
        """
        Get the data directory for the application.
        
        Creates the directory if it doesn't exist.
        
        Returns:
            Path to the data directory
        """
        data_dir = DatabasePathManager.get_app_data_dir() / DatabasePathManager.DATA_DIRNAME
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    
    @staticmethod
    def get_database_path(filename: str = "cafe.db") -> Path:
        """
        Get the full path to the database file.
        
        Creates the data directory if needed.
        
        Args:
            filename: Name of the database file (default: cafe.db)
        
        Returns:
            Path to the database file
        """
        data_dir = DatabasePathManager.get_data_dir()
        return data_dir / filename
    
    @staticmethod
    def get_backups_dir() -> Path:
        """
        Get the backups directory for the application.
        
        Creates the directory if it doesn't exist.
        
        Returns:
            Path to the backups directory
        """
        backups_dir = DatabasePathManager.get_app_data_dir() / DatabasePathManager.BACKUPS_DIRNAME
        backups_dir.mkdir(parents=True, exist_ok=True)
        return backups_dir


class DatabaseBackupManager:
    """Manages database backups and restoration."""
    
    BACKUP_EXTENSION = ".backup"
    
    def __init__(self, database_path: Path):
        """
        Initialize backup manager.
        
        Args:
            database_path: Path to the database file
        """
        self.database_path = database_path
        self.backups_dir = DatabasePathManager.get_backups_dir()
    
    def create_backup(self, description: str = None) -> Optional[Path]:
        """
        Create a backup of the database.
        
        Backup filename format: cafe-YYYYMMDD-HHMMSS.backup
        with optional description in a metadata file.
        
        Args:
            description: Optional description of the backup
        
        Returns:
            Path to the backup file, or None if backup failed
        
        Raises:
            FileNotFoundError: If database file doesn't exist
            IOError: If backup operation fails
        """
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.database_path}")
        
        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            db_name = self.database_path.stem
            backup_filename = f"{db_name}-{timestamp}{self.BACKUP_EXTENSION}"
            backup_path = self.backups_dir / backup_filename
            
            # Copy database file to backup location
            shutil.copy2(self.database_path, backup_path)
            
            # Write metadata file if description provided
            if description:
                metadata_path = backup_path.with_suffix(self.BACKUP_EXTENSION + ".meta")
                with open(metadata_path, "w") as f:
                    f.write(f"timestamp: {datetime.now().isoformat()}\n")
                    f.write(f"description: {description}\n")
                    f.write(f"database: {self.database_path.name}\n")
            
            return backup_path
        
        except Exception as e:
            raise IOError(f"Failed to create backup: {str(e)}") from e
    
    def list_backups(self) -> List[Tuple[Path, Optional[str]]]:
        """
        List all available backups.
        
        Returns:
            List of tuples containing (backup_path, description)
        """
        backups = []
        
        for backup_file in self.backups_dir.glob(f"*{self.BACKUP_EXTENSION}"):
            # Skip metadata files
            if backup_file.suffix == ".meta":
                continue
            
            # Try to read metadata
            description = None
            metadata_path = backup_file.with_suffix(self.BACKUP_EXTENSION + ".meta")
            if metadata_path.exists():
                try:
                    with open(metadata_path, "r") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.startswith("description:"):
                                description = line.replace("description:", "").strip()
                except Exception:
                    pass
            
            backups.append((backup_file, description))
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
        
        return backups
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore a database from backup.
        
        Creates a backup of current database before restoring.
        
        Args:
            backup_path: Path to the backup file
        
        Returns:
            True if restoration successful, False otherwise
        
        Raises:
            FileNotFoundError: If backup file doesn't exist
            IOError: If restoration fails
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        try:
            # Create backup of current database as safety measure
            if self.database_path.exists():
                safety_backup = self.create_backup(description="Auto-backup before restore")
            
            # Restore from backup
            shutil.copy2(backup_path, self.database_path)
            
            return True
        
        except Exception as e:
            raise IOError(f"Failed to restore backup: {str(e)}") from e
    
    def delete_backup(self, backup_path: Path) -> bool:
        """
        Delete a backup file.
        
        Args:
            backup_path: Path to the backup file
        
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            if backup_path.exists():
                backup_path.unlink()
            
            # Delete metadata file if exists
            metadata_path = backup_path.with_suffix(".backup.meta")
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        except Exception:
            return False
    
    def get_backup_info(self, backup_path: Path) -> dict:
        """
        Get information about a backup file.
        
        Args:
            backup_path: Path to the backup file
        
        Returns:
            Dictionary with backup information
        """
        if not backup_path.exists():
            return {}
        
        stat = backup_path.stat()
        created_time = datetime.fromtimestamp(stat.st_mtime)
        
        info = {
            "path": str(backup_path),
            "filename": backup_path.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": created_time.isoformat(),
            "created_formatted": created_time.strftime("%Y-%m-%d %H:%M:%S"),
            "description": None
        }
        
        # Read description from metadata
        metadata_path = backup_path.with_suffix(".backup.meta")
        if metadata_path.exists():
            try:
                with open(metadata_path, "r") as f:
                    for line in f:
                        if line.startswith("description:"):
                            info["description"] = line.replace("description:", "").strip()
                            break
            except Exception:
                pass
        
        return info
