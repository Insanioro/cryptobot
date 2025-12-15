"""Event logging service for tracking user actions."""
import logging
from typing import Optional

from database.db import Database
from database.models import EventType


logger = logging.getLogger(__name__)


class EventLogger:
    """Service for logging user events."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def log_event(
        self,
        user_id: int,
        event_type: str,
        metadata: Optional[dict] = None,
        username: Optional[str] = None
    ) -> None:
        """
        Log an event to the database.
        
        Args:
            user_id: User ID who triggered the event
            event_type: Type of event (use EventType constants)
            metadata: Additional data about the event
            username: Username to save (optional)
        """
        try:
            await self.db.add_event(user_id, event_type, metadata or {})
            # Update username if provided
            if username:
                await self.db.update_user_info(user_id, username)
            logger.info(f"Event logged: {event_type} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to log event {event_type} for user {user_id}: {e}")
    
    # Convenience methods for specific events
    
    async def log_first_start(self, user_id: int, username: Optional[str] = None) -> None:
        """Log user's first start of the bot."""
        metadata = {}
        if username:
            metadata['username'] = username
        await self.log_event(user_id, EventType.FIRST_START, metadata)
    
    async def log_bot_restart(self, user_id: int) -> None:
        """Log user restarting the bot."""
        await self.log_event(user_id, EventType.BOT_RESTART)
    
    async def log_go_to_group(self, user_id: int, group_url: Optional[str] = None) -> None:
        """Log user clicking 'Go to group' button."""
        metadata = {}
        if group_url:
            metadata['group_url'] = group_url
        await self.log_event(user_id, EventType.GO_TO_GROUP, metadata)
    
    async def log_contact_manager(self, user_id: int, manager_username: Optional[str] = None) -> None:
        """Log user clicking 'Contact manager' button."""
        metadata = {}
        if manager_username:
            metadata['manager_username'] = manager_username
        await self.log_event(user_id, EventType.CONTACT_MANAGER, metadata)
    
    async def log_check_nickname(self, user_id: int, nickname: str, price_range: Optional[tuple] = None) -> None:
        """Log user checking nickname valuation."""
        metadata = {'nickname': nickname}
        if price_range:
            metadata['price_low'] = price_range[0]
            metadata['price_high'] = price_range[1]
        await self.log_event(user_id, EventType.CHECK_NICKNAME, metadata)
    
    async def log_exit_without_action(self, user_id: int) -> None:
        """Log user exiting without completing any action."""
        await self.log_event(user_id, EventType.EXIT_WITHOUT_ACTION)
    
    async def log_start_checkout(self, user_id: int, nickname: Optional[str] = None) -> None:
        """Log user starting checkout process."""
        metadata = {}
        if nickname:
            metadata['nickname'] = nickname
        await self.log_event(user_id, EventType.START_CHECKOUT, metadata)
    
    async def log_abandoned_checkout(self, user_id: int, nickname: Optional[str] = None) -> None:
        """Log user abandoning checkout process."""
        metadata = {}
        if nickname:
            metadata['nickname'] = nickname
        await self.log_event(user_id, EventType.ABANDONED_CHECKOUT, metadata)
    
    async def log_successful_order(
        self,
        user_id: int,
        nickname: Optional[str] = None,
        price: Optional[int] = None
    ) -> None:
        """Log successful order completion."""
        metadata = {}
        if nickname:
            metadata['nickname'] = nickname
        if price:
            metadata['price'] = price
        await self.log_event(user_id, EventType.SUCCESSFUL_ORDER, metadata)
