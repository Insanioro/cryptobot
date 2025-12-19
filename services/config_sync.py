"""Service for syncing .env file changes to database."""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv, set_key
from database.db import Database

logger = logging.getLogger(__name__)


class ConfigSyncService:
    """Service for syncing environment variables to database settings."""
    
    def __init__(self, db: Database):
        self.db = db
        self.env_file = Path(__file__).parent.parent / '.env'
        self.last_modified = None
        
        # Mapping of env variables to database settings
        self.sync_map = {
            'REMINDER_DELAY_MINUTES': 'reminder_delay_minutes',
            'REMINDER_CHECK_INTERVAL_MINUTES': 'reminder_check_interval',
            'REMINDER_ENABLED': 'reminder_enabled'
        }
        
        # Reverse mapping for writing to .env
        self.reverse_map = {v: k for k, v in self.sync_map.items()}
    
    async def check_and_sync(self) -> bool:
        """
        Check if .env file was modified and sync changes to database.
        
        Returns:
            bool: True if changes were synced
        """
        try:
            if not self.env_file.exists():
                return False
            
            # Check if file was modified
            current_modified = self.env_file.stat().st_mtime
            
            if self.last_modified is None:
                self.last_modified = current_modified
                return False
            
            if current_modified == self.last_modified:
                return False
            
            # File was modified, reload and sync
            logger.info("Detected .env file changes, syncing to database...")
            self.last_modified = current_modified
            
            # Reload .env file
            load_dotenv(override=True)
            
            changes = []
            for env_key, db_key in self.sync_map.items():
                env_value = os.getenv(env_key)
                if env_value is not None:
                    # Get current value from DB
                    db_value = await self.db.get_system_setting(db_key)
                    
                    # Normalize values for comparison
                    env_value_normalized = str(env_value).strip()
                    db_value_normalized = str(db_value).strip() if db_value else None
                    
                    if env_value_normalized != db_value_normalized:
                        await self.db.set_system_setting(db_key, env_value_normalized, admin_id=None)
                        changes.append(f"{db_key}: {db_value_normalized} → {env_value_normalized}")
                        logger.info(f"Updated {db_key} from .env: {env_value_normalized}")
            
            if changes:
                logger.info(f"Synced {len(changes)} settings from .env to database")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error syncing .env to database: {e}")
            return False
    
    async def sync_to_env(self, db_key: str, value: str) -> bool:
        """
        Sync a database setting back to .env file.
        
        Args:
            db_key: Database setting key (e.g. 'reminder_delay_minutes')
            value: New value to write
            
        Returns:
            bool: True if successfully written
        """
        try:
            # Get env variable name
            env_key = self.reverse_map.get(db_key)
            if not env_key:
                logger.warning(f"No .env mapping found for {db_key}")
                return False
            
            if not self.env_file.exists():
                logger.error(f".env file not found at {self.env_file}")
                return False
            
            # Write to .env file
            set_key(str(self.env_file), env_key, str(value))
            logger.info(f"Updated .env file: {env_key}={value}")
            
            # Update last modified time to prevent re-sync loop
            self.last_modified = self.env_file.stat().st_mtime
            
            return True
            
        except Exception as e:
            logger.error(f"Error writing to .env file: {e}")
            return False
