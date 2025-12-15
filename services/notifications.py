"""Notification service for sending alerts to admins."""
import logging
from typing import Optional

from aiogram import Bot

from database.db import Database
from config import ADMIN_IDS


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications to administrators."""
    
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
    
    async def _send_to_admin(self, admin_id: int, text: str) -> bool:
        """
        Send message to a specific admin.
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            await self.bot.send_message(admin_id, text, parse_mode="HTML")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")
            return False
    
    async def _send_to_admins(self, text: str, check_settings: bool = True) -> int:
        """
        Send message to all admins.
        
        Returns:
            Number of admins who received the message
        """
        sent_count = 0
        for admin_id in ADMIN_IDS:
            if await self._send_to_admin(admin_id, text):
                sent_count += 1
        return sent_count
    
    # ==================== Specific Notifications ====================
    
    async def notify_new_user(self, user_id: int, username: Optional[str] = None) -> None:
        """Notify admins about a new user."""
        for admin_id in ADMIN_IDS:
            settings = await self.db.get_notification_settings(admin_id)
            if not settings.get('notify_new_users', True):
                continue
            
            user_display = f"@{username}" if username else f"ID: {user_id}"
            text = f"🆕 <b>Новый пользователь</b>\n\n{user_display}"
            
            await self._send_to_admin(admin_id, text)
    
    async def notify_successful_order(
        self,
        user_id: int,
        username: Optional[str] = None,
        nickname: Optional[str] = None,
        price: Optional[int] = None
    ) -> None:
        """Notify admins about a successful order."""
        for admin_id in ADMIN_IDS:
            settings = await self.db.get_notification_settings(admin_id)
            if not settings.get('notify_orders', True):
                continue
            
            user_display = f"@{username}" if username else f"ID: {user_id}"
            text = f"💰 <b>Заказ оформлен!</b>\n\n"
            text += f"👤 Пользователь: {user_display}\n"
            
            if nickname:
                text += f"📝 Ник: {nickname}\n"
            if price:
                text += f"💵 Цена: ${price:,}\n"
            
            await self._send_to_admin(admin_id, text)
    
    async def notify_abandoned_checkouts_alert(self, count: int, period_hours: int = 1) -> None:
        """Notify admins about high number of abandoned checkouts."""
        for admin_id in ADMIN_IDS:
            settings = await self.db.get_notification_settings(admin_id)
            if not settings.get('notify_abandoned_checkouts', True):
                continue
            
            threshold = settings.get('abandoned_threshold', 10)
            if count <= threshold:
                continue
            
            text = f"⚠️ <b>Внимание!</b>\n\n"
            text += f"<b>{count}</b> брошенных оформлений за последний час\n"
            text += f"Это выше порога ({threshold})"
            
            await self._send_to_admin(admin_id, text)
    
    async def send_daily_report(self, stats: dict) -> None:
        """Send daily statistics report to all admins."""
        text = "📊 <b>Дневной отчёт</b>\n\n"
        text += f"👥 Всего пользователей: {stats.get('total_users', 0)}\n"
        text += f"🆕 Новых за 24 часа: {stats.get('new_users_24h', 0)}\n"
        text += f"🔁 Запусков сегодня: {stats.get('restarts_today', 0)}\n\n"
        text += f"👣 <b>Переходы:</b>\n"
        text += f"• В группу: {stats.get('group_visits', 0)}\n"
        text += f"• К менеджеру: {stats.get('manager_contacts', 0)}\n\n"
        text += f"💰 <b>Действия:</b>\n"
        text += f"• Проверок ника: {stats.get('nickname_checks', 0)}\n"
        text += f"• Начали оформление: {stats.get('checkout_starts', 0)}\n"
        text += f"• Успешные заказы: {stats.get('successful_orders', 0)}\n"
        text += f"• Брошенные оформления: {stats.get('abandoned_checkouts', 0)}\n"
        
        await self._send_to_admins(text, check_settings=False)
