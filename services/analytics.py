"""Analytics service for generating statistics and reports."""
import logging
from datetime import datetime, timedelta, date
from typing import Optional

from database.db import Database
from database.models import EventType, DailyStats


logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating statistics and analytics."""
    
    def __init__(self, db: Database):
        self.db = db
    
    # ==================== General Statistics ====================
    
    async def get_total_users(self) -> int:
        """Get total number of users."""
        return await self.db.get_total_users()
    
    async def get_new_users(self, hours: int = 24) -> int:
        """Get number of new users in the last N hours."""
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours)
        return await self.db.get_new_users(start_date, end_date)
    
    async def get_restarts_today(self) -> int:
        """Get number of bot restarts today."""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now()
        return await self.db.get_event_count(EventType.BOT_RESTART, start_date, end_date)
    
    async def get_event_count_today(self, event_type: str) -> int:
        """Get count of specific event type today."""
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now()
        return await self.db.get_event_count(event_type, start_date, end_date)
    
    async def get_main_stats(self) -> dict:
        """
        Get main statistics for admin panel.
        
        Returns:
            dict with keys: total_users, new_users_24h, restarts_today,
                           group_visits, manager_contacts, nickname_checks,
                           checkout_starts, successful_orders, abandoned_checkouts
        """
        total_users = await self.get_total_users()
        new_users_24h = await self.get_new_users(24)
        restarts_today = await self.get_restarts_today()
        
        # Get event counts for today
        group_visits = await self.get_event_count_today(EventType.GO_TO_GROUP)
        manager_contacts = await self.get_event_count_today(EventType.CONTACT_MANAGER)
        nickname_checks = await self.get_event_count_today(EventType.CHECK_NICKNAME)
        checkout_starts = await self.get_event_count_today(EventType.START_CHECKOUT)
        successful_orders = await self.get_event_count_today(EventType.SUCCESSFUL_ORDER)
        abandoned_checkouts = await self.get_event_count_today(EventType.ABANDONED_CHECKOUT)
        
        return {
            'total_users': total_users,
            'new_users_24h': new_users_24h,
            'restarts_today': restarts_today,
            'group_visits': group_visits,
            'manager_contacts': manager_contacts,
            'nickname_checks': nickname_checks,
            'checkout_starts': checkout_starts,
            'successful_orders': successful_orders,
            'abandoned_checkouts': abandoned_checkouts,
        }
    
    # ==================== Date-specific Statistics ====================
    
    async def get_stats_by_date(self, target_date: date) -> dict:
        """Get statistics for a specific date."""
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        new_users = await self.db.get_new_users(start_datetime, end_datetime)
        
        stats = {
            'date': target_date,
            'new_users': new_users,
        }
        
        # Get counts for each event type
        for event_type in EventType.all_types():
            count = await self.db.get_event_count(event_type, start_datetime, end_datetime)
            stats[event_type] = count
        
        return stats
    
    async def get_stats_for_period(self, start_date: date, end_date: date) -> dict:
        """Get aggregated statistics for a date range."""
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        new_users = await self.db.get_new_users(start_datetime, end_datetime)
        
        stats = {
            'start_date': start_date,
            'end_date': end_date,
            'new_users': new_users,
        }
        
        # Get counts for each event type
        for event_type in EventType.all_types():
            count = await self.db.get_event_count(event_type, start_datetime, end_datetime)
            stats[event_type] = count
        
        return stats
    
    # ==================== User-specific Statistics ====================
    
    async def get_user_history(self, user_id: int, limit: int = 50) -> list[dict]:
        """Get user's event history."""
        events = await self.db.get_events(user_id=user_id, limit=limit)
        return events
    
    async def get_user_summary(self, user_id: int) -> Optional[dict]:
        """Get summary statistics for a specific user."""
        return await self.db.get_user_stats(user_id)
    
    async def get_users_list(self, page: int = 1, page_size: int = 10) -> dict:
        """
        Get paginated list of users.
        
        Returns:
            dict with keys: users (list), total_count, page, page_size, total_pages
        """
        offset = (page - 1) * page_size
        users = await self.db.get_users_list(limit=page_size, offset=offset)
        total_count = await self.db.get_total_users()
        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        
        return {
            'users': users,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }
    
    # ==================== Alert Checking ====================
    
    async def check_abandoned_checkouts_alert(self, threshold: int = 10) -> Optional[int]:
        """
        Check if abandoned checkouts in the last hour exceed threshold.
        
        Returns:
            Number of abandoned checkouts if threshold exceeded, None otherwise
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=1)
        
        count = await self.db.get_event_count(
            EventType.ABANDONED_CHECKOUT,
            start_date,
            end_date
        )
        
        if count > threshold:
            return count
        return None
