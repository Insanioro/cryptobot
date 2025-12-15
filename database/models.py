"""Data models for admin statistics system."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """Represents a user event."""
    id: Optional[int]
    user_id: int
    event_type: str
    timestamp: datetime
    metadata: dict
    
    @classmethod
    def from_row(cls, row) -> 'Event':
        """Create Event from database row."""
        return cls(
            id=row['id'],
            user_id=row['user_id'],
            event_type=row['event_type'],
            timestamp=row['timestamp'],
            metadata=row['metadata']
        )


@dataclass
class UserStats:
    """User statistics summary."""
    user_id: int
    username: Optional[str]
    first_seen: datetime
    last_activity: datetime
    total_events: int
    nickname_checks: int
    successful_orders: int
    abandoned_checkouts: int


@dataclass
class DailyStats:
    """Daily statistics summary."""
    stat_date: datetime
    total_users: int
    new_users: int
    bot_restarts: int
    group_visits: int
    manager_contacts: int
    nickname_checks: int
    checkout_starts: int
    successful_orders: int
    abandoned_checkouts: int


@dataclass
class NotificationSettings:
    """Admin notification settings."""
    admin_id: int
    notify_new_users: bool = True
    notify_orders: bool = True
    notify_abandoned_checkouts: bool = True
    abandoned_threshold: int = 10
    updated_at: Optional[datetime] = None


# Event type constants
class EventType:
    """Event type constants."""
    FIRST_START = "first_start"
    BOT_RESTART = "bot_restart"
    GO_TO_GROUP = "go_to_group"
    CONTACT_MANAGER = "contact_manager"
    CHECK_NICKNAME = "check_nickname"
    EXIT_WITHOUT_ACTION = "exit_without_action"
    START_CHECKOUT = "start_checkout"
    ABANDONED_CHECKOUT = "abandoned_checkout"
    SUCCESSFUL_ORDER = "successful_order"
    
    @classmethod
    def all_types(cls) -> list[str]:
        """Return all event types."""
        return [
            cls.FIRST_START,
            cls.BOT_RESTART,
            cls.GO_TO_GROUP,
            cls.CONTACT_MANAGER,
            cls.CHECK_NICKNAME,
            cls.EXIT_WITHOUT_ACTION,
            cls.START_CHECKOUT,
            cls.ABANDONED_CHECKOUT,
            cls.SUCCESSFUL_ORDER,
        ]
    
    @classmethod
    def get_emoji(cls, event_type: str) -> str:
        """Get emoji for event type."""
        emoji_map = {
            cls.FIRST_START: "🎉",
            cls.BOT_RESTART: "🔄",
            cls.GO_TO_GROUP: "👥",
            cls.CONTACT_MANAGER: "💬",
            cls.CHECK_NICKNAME: "🔍",
            cls.EXIT_WITHOUT_ACTION: "🚪",
            cls.START_CHECKOUT: "🛒",
            cls.ABANDONED_CHECKOUT: "⚠️",
            cls.SUCCESSFUL_ORDER: "✅",
        }
        return emoji_map.get(event_type, "📌")
