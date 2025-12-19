import asyncpg
from typing import Optional
from datetime import datetime, date, timedelta
import json

from config import PG_DSN


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(dsn=PG_DSN)
        await self._create_tables()

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def _create_tables(self) -> None:
        async with self.pool.acquire() as conn:
            # Users table with extended fields
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    language VARCHAR(5) DEFAULT 'en',
                    join_date TIMESTAMP DEFAULT NOW(),
                    first_seen TIMESTAMP DEFAULT NOW(),
                    last_activity TIMESTAMP DEFAULT NOW(),
                    username VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Add new columns if they don't exist (migration)
            await conn.execute("""
                DO $$ 
                BEGIN
                    BEGIN
                        ALTER TABLE users ADD COLUMN first_seen TIMESTAMP DEFAULT NOW();
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN last_activity TIMESTAMP DEFAULT NOW();
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN username VARCHAR(255);
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN is_bot_blocked BOOLEAN DEFAULT FALSE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN last_valuation_date TIMESTAMP;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN contacted_manager BOOLEAN DEFAULT FALSE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                    BEGIN
                        ALTER TABLE users ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE;
                    EXCEPTION
                        WHEN duplicate_column THEN NULL;
                    END;
                END $$;
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS username_valuations (
                    username VARCHAR(33) PRIMARY KEY,
                    structure VARCHAR(50),
                    category VARCHAR(50),
                    rarity VARCHAR(50),
                    demand VARCHAR(50),
                    score VARCHAR(10),
                    branding VARCHAR(50),
                    price_low INTEGER,
                    price_high INTEGER,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Events table for logging
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)
            
            # Create indexes for events table
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_user_event ON events(user_id, event_type);
            """)
            
            # Admin notification settings table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_notification_settings (
                    admin_id BIGINT PRIMARY KEY,
                    notify_new_users BOOLEAN DEFAULT TRUE,
                    notify_orders BOOLEAN DEFAULT TRUE,
                    notify_abandoned_checkouts BOOLEAN DEFAULT TRUE,
                    abandoned_threshold INTEGER DEFAULT 10,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Daily stats cache table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats_cache (
                    stat_date DATE PRIMARY KEY,
                    total_users INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    bot_restarts INTEGER DEFAULT 0,
                    group_visits INTEGER DEFAULT 0,
                    manager_contacts INTEGER DEFAULT 0,
                    nickname_checks INTEGER DEFAULT 0,
                    checkout_starts INTEGER DEFAULT 0,
                    successful_orders INTEGER DEFAULT 0,
                    abandoned_checkouts INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Valuations table for tracking user evaluations
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS valuations (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    username_checked VARCHAR(255) NOT NULL,
                    estimated_price VARCHAR(100),
                    valuation_date TIMESTAMP DEFAULT NOW(),
                    manager_contacted BOOLEAN DEFAULT FALSE,
                    reminder_sent BOOLEAN DEFAULT FALSE,
                    reminder_sent_at TIMESTAMP
                )
            """)
            
            # Create indexes for valuations table
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_valuations_user_id ON valuations(user_id);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_valuations_date ON valuations(valuation_date);
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_valuations_reminder ON valuations(reminder_sent, manager_contacted);
            """)
            
            # System settings table for configurable parameters
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    setting_key VARCHAR(100) PRIMARY KEY,
                    setting_value TEXT NOT NULL,
                    setting_type VARCHAR(20) DEFAULT 'string',
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT NOW(),
                    updated_by BIGINT
                )
            """)
            
            # Initialize default settings
            await conn.execute("""
                INSERT INTO system_settings (setting_key, setting_value, setting_type, description)
                VALUES 
                    ('reminder_check_interval', '1', 'int', 'Interval in minutes to check for pending reminders'),
                    ('reminder_enabled', 'true', 'bool', 'Enable/disable reminder system'),
                    ('reminder_delay_minutes', '15', 'int', 'Minutes to wait before sending reminder after valuation')
                ON CONFLICT (setting_key) DO NOTHING
            """)
    
    async def add_user(self, user_id: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users (user_id) VALUES ($1) ON CONFLICT DO NOTHING",
                user_id
            )

    async def set_language(self, user_id: int, lang: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET language = $2 WHERE user_id = $1",
                user_id, lang
            )

    async def get_language(self, user_id: int) -> str:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT language FROM users WHERE user_id = $1",
                user_id
            )
            return result if result else "en"

    async def get_valuation(self, username: str) -> dict | None:
        """Get cached valuation for username."""
        clean_username = username.lstrip("@").lower()
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM username_valuations WHERE username = $1",
                clean_username
            )
            if row:
                return {
                    "username": f"@{clean_username}",
                    "structure": row["structure"],
                    "category": row["category"],
                    "rarity": row["rarity"],
                    "demand": row["demand"],
                    "score": row["score"],
                    "branding": row["branding"],
                    "price_low": row["price_low"],
                    "price_high": row["price_high"],
                }
            return None

    async def save_valuation(self, data: dict) -> None:
        """Save valuation data to cache."""
        clean_username = data["username"].lstrip("@").lower()
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO username_valuations 
                (username, structure, category, rarity, demand, score, branding, price_low, price_high)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (username) DO NOTHING
                """,
                clean_username,
                data["structure"],
                data["category"],
                data["rarity"],
                data["demand"],
                data["score"],
                data["branding"],
                data["price_low"],
                data["price_high"]
            )
    
    # ==================== Event Logging Methods ====================
    
    async def add_event(self, user_id: int, event_type: str, metadata: dict = None) -> None:
        """Log an event to the database."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO events (user_id, event_type, metadata)
                VALUES ($1, $2, $3)
                """,
                user_id,
                event_type,
                json.dumps(metadata or {})
            )
            # Update user last activity
            await conn.execute(
                "UPDATE users SET last_activity = NOW() WHERE user_id = $1",
                user_id
            )
    
    async def get_events(
        self,
        user_id: Optional[int] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """Get events with filters."""
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        param_idx = 1
        
        if user_id:
            query += f" AND user_id = ${param_idx}"
            params.append(user_id)
            param_idx += 1
        
        if event_type:
            query += f" AND event_type = ${param_idx}"
            params.append(event_type)
            param_idx += 1
        
        if start_date:
            query += f" AND timestamp >= ${param_idx}"
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            query += f" AND timestamp <= ${param_idx}"
            params.append(end_date)
            param_idx += 1
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
        params.extend([limit, offset])
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_event_count(
        self,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """Get count of events with filters."""
        query = "SELECT COUNT(*) FROM events WHERE 1=1"
        params = []
        param_idx = 1
        
        if event_type:
            query += f" AND event_type = ${param_idx}"
            params.append(event_type)
            param_idx += 1
        
        if start_date:
            query += f" AND timestamp >= ${param_idx}"
            params.append(start_date)
            param_idx += 1
        
        if end_date:
            query += f" AND timestamp <= ${param_idx}"
            params.append(end_date)
            param_idx += 1
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *params)
    
    # ==================== Statistics Methods ====================
    
    async def get_total_users(self) -> int:
        """Get total number of users."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM users")
    
    async def get_new_users(self, start_date: datetime, end_date: datetime) -> int:
        """Get number of new users in date range."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE first_seen >= $1 AND first_seen <= $2",
                start_date, end_date
            )
    
    async def get_user_stats(self, user_id: int) -> Optional[dict]:
        """Get statistics for a specific user."""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE user_id = $1",
                user_id
            )
            if not user:
                return None
            
            event_counts = await conn.fetch(
                """
                SELECT event_type, COUNT(*) as count
                FROM events
                WHERE user_id = $1
                GROUP BY event_type
                """,
                user_id
            )
            
            stats = dict(user)
            stats['event_counts'] = {row['event_type']: row['count'] for row in event_counts}
            return stats
    
    async def get_users_list(self, limit: int = 10, offset: int = 0) -> list[dict]:
        """Get paginated list of users."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, username, first_seen, last_activity,
                       (SELECT COUNT(*) FROM events WHERE events.user_id = users.user_id) as total_events
                FROM users
                ORDER BY (username IS NOT NULL AND username != '') DESC, last_activity DESC
                LIMIT $1 OFFSET $2
                """,
                limit, offset
            )
            return [dict(row) for row in rows]
    
    async def update_user_info(self, user_id: int, username: Optional[str] = None) -> None:
        """Update user information."""
        async with self.pool.acquire() as conn:
            if username:
                await conn.execute(
                    "UPDATE users SET username = $2, last_activity = NOW() WHERE user_id = $1",
                    user_id, username
                )
            else:
                await conn.execute(
                    "UPDATE users SET last_activity = NOW() WHERE user_id = $1",
                    user_id
                )
    
    # ==================== Notification Settings Methods ====================
    
    async def get_notification_settings(self, admin_id: int) -> dict:
        """Get notification settings for admin."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM admin_notification_settings WHERE admin_id = $1",
                admin_id
            )
            if row:
                return dict(row)
            # Return defaults
            from config import (
                DEFAULT_NOTIFY_NEW_USERS,
                DEFAULT_NOTIFY_ORDERS,
                DEFAULT_NOTIFY_ABANDONED,
                DEFAULT_ABANDONED_THRESHOLD
            )
            return {
                'admin_id': admin_id,
                'notify_new_users': DEFAULT_NOTIFY_NEW_USERS,
                'notify_orders': DEFAULT_NOTIFY_ORDERS,
                'notify_abandoned_checkouts': DEFAULT_NOTIFY_ABANDONED,
                'abandoned_threshold': DEFAULT_ABANDONED_THRESHOLD
            }
    
    async def update_notification_settings(
        self,
        admin_id: int,
        notify_new_users: Optional[bool] = None,
        notify_orders: Optional[bool] = None,
        notify_abandoned_checkouts: Optional[bool] = None,
        abandoned_threshold: Optional[int] = None
    ) -> None:
        """Update notification settings for admin."""
        async with self.pool.acquire() as conn:
            # Check if settings exist
            exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM admin_notification_settings WHERE admin_id = $1)",
                admin_id
            )
            
            if exists:
                # Update existing
                updates = []
                params = [admin_id]
                param_idx = 2
                
                if notify_new_users is not None:
                    updates.append(f"notify_new_users = ${param_idx}")
                    params.append(notify_new_users)
                    param_idx += 1
                
                if notify_orders is not None:
                    updates.append(f"notify_orders = ${param_idx}")
                    params.append(notify_orders)
                    param_idx += 1
                
                if notify_abandoned_checkouts is not None:
                    updates.append(f"notify_abandoned_checkouts = ${param_idx}")
                    params.append(notify_abandoned_checkouts)
                    param_idx += 1
                
                if abandoned_threshold is not None:
                    updates.append(f"abandoned_threshold = ${param_idx}")
                    params.append(abandoned_threshold)
                    param_idx += 1
                
                if updates:
                    updates.append("updated_at = NOW()")
                    query = f"UPDATE admin_notification_settings SET {', '.join(updates)} WHERE admin_id = $1"
                    await conn.execute(query, *params)
            else:
                # Insert new
                await conn.execute(
                    """
                    INSERT INTO admin_notification_settings 
                    (admin_id, notify_new_users, notify_orders, notify_abandoned_checkouts, abandoned_threshold)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    admin_id,
                    notify_new_users if notify_new_users is not None else True,
                    notify_orders if notify_orders is not None else True,
                    notify_abandoned_checkouts if notify_abandoned_checkouts is not None else True,
                    abandoned_threshold if abandoned_threshold is not None else 10
                )
    
    # Valuation methods
    async def create_valuation(self, user_id: int, username_checked: str, estimated_price: str) -> int:
        """Create a new valuation record."""
        async with self.pool.acquire() as conn:
            # Update user's last valuation date and reset flags
            await conn.execute(
                """
                UPDATE users 
                SET last_valuation_date = NOW(), 
                    contacted_manager = FALSE, 
                    reminder_sent = FALSE
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Create valuation record
            valuation_id = await conn.fetchval(
                """
                INSERT INTO valuations (user_id, username_checked, estimated_price, valuation_date)
                VALUES ($1, $2, $3, NOW())
                RETURNING id
                """,
                user_id, username_checked, estimated_price
            )
            return valuation_id
    
    async def mark_manager_contacted(self, user_id: int) -> None:
        """Mark user as having contacted the manager."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET contacted_manager = TRUE WHERE user_id = $1",
                user_id
            )
            # Also update all pending valuations
            await conn.execute(
                """
                UPDATE valuations 
                SET manager_contacted = TRUE 
                WHERE user_id = $1 AND manager_contacted = FALSE
                """,
                user_id
            )
    
    async def mark_reminder_sent(self, user_id: int) -> None:
        """Mark reminder as sent for user."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET reminder_sent = TRUE WHERE user_id = $1",
                user_id
            )
            # Update the latest valuation using subquery
            await conn.execute(
                """
                UPDATE valuations 
                SET reminder_sent = TRUE, reminder_sent_at = NOW()
                WHERE id = (
                    SELECT id 
                    FROM valuations 
                    WHERE user_id = $1 
                    AND reminder_sent = FALSE
                    AND manager_contacted = FALSE
                    ORDER BY valuation_date DESC
                    LIMIT 1
                )
                """,
                user_id
            )
    
    async def get_users_for_reminder(self, delay_minutes: int) -> list:
        """Get users who need reminders."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (u.user_id) u.user_id, u.username, v.id as valuation_id, v.valuation_date
                FROM users u
                INNER JOIN valuations v ON u.user_id = v.user_id
                WHERE v.valuation_date < NOW() - INTERVAL '%s minutes'
                AND v.manager_contacted = FALSE
                AND v.reminder_sent = FALSE
                AND u.is_bot_blocked = FALSE
                ORDER BY u.user_id, v.valuation_date DESC
                """ % delay_minutes
            )
            return [dict(row) for row in rows]
    
    async def mark_user_blocked(self, user_id: int) -> None:
        """Mark user as having blocked the bot."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_bot_blocked = TRUE WHERE user_id = $1",
                user_id
            )
    
    async def mark_user_unblocked(self, user_id: int) -> None:
        """Mark user as having unblocked the bot."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_bot_blocked = FALSE WHERE user_id = $1",
                user_id
            )
    
    # System Settings Methods
    async def get_system_setting(self, key: str, default: str = None) -> str:
        """Get system setting value by key."""
        async with self.pool.acquire() as conn:
            value = await conn.fetchval(
                "SELECT setting_value FROM system_settings WHERE setting_key = $1",
                key
            )
            return value if value is not None else default
    
    async def set_system_setting(self, key: str, value: str, admin_id: int = None) -> None:
        """Set system setting value."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO system_settings (setting_key, setting_value, updated_by, updated_at)
                VALUES ($1, $2, $3, NOW())
                ON CONFLICT (setting_key) 
                DO UPDATE SET 
                    setting_value = $2,
                    updated_by = $3,
                    updated_at = NOW()
            """, key, value, admin_id)
    
    async def get_all_system_settings(self) -> dict:
        """Get all system settings as a dictionary."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT setting_key, setting_value, setting_type, description FROM system_settings"
            )
            return {row['setting_key']: {
                'value': row['setting_value'],
                'type': row['setting_type'],
                'description': row['description']
            } for row in rows}
    
    async def get_active_users_for_broadcast(self) -> list:
        """Get all active users for broadcast (not blocked)."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, username, language
                FROM users
                WHERE is_bot_blocked = FALSE
                ORDER BY user_id
                """
            )
            return [dict(row) for row in rows]


db = Database()
