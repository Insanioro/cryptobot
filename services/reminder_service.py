"""Service for reminder functionality."""
import logging
from typing import Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from database.db import Database
from config import MANAGER_LINK


logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing user reminders."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def check_pending_reminders(self) -> list[dict]:
        """Check for users who need reminders."""
        # Get delay from database settings
        delay_str = await self.db.get_system_setting('reminder_delay_minutes', '15')
        try:
            delay_minutes = int(delay_str)
        except ValueError:
            delay_minutes = 15
            logger.warning(f"Invalid reminder_delay_minutes value: {delay_str}, using default: 15")
        
        return await self.db.get_users_for_reminder(delay_minutes)
    
    async def send_reminder(
        self,
        bot: Bot,
        user_id: int,
        texts: dict,
        manager_link: str = MANAGER_LINK
    ) -> bool:
        """
        Send reminder to a specific user.
        
        Args:
            bot: Bot instance
            user_id: User ID to send reminder to
            texts: Localization texts
            manager_link: Link to manager
        
        Returns:
            bool: True if sent successfully
        """
        try:
            from keyboards.builders import get_manager_keyboard
            
            reminder_text = texts.get('reminder_message', '')
            keyboard = get_manager_keyboard(manager_link, texts)
            
            await bot.send_message(
                chat_id=user_id,
                text=reminder_text,
                reply_markup=keyboard
            )
            
            # Mark reminder as sent
            await self.db.mark_reminder_sent(user_id)
            logger.info(f"Reminder sent to user {user_id}")
            return True
        
        except TelegramForbiddenError:
            # User blocked the bot
            await self.db.mark_user_blocked(user_id)
            logger.info(f"Cannot send reminder - user {user_id} blocked the bot")
            return False
        
        except TelegramBadRequest as e:
            logger.warning(f"Bad request when sending reminder to {user_id}: {e}")
            return False
        
        except Exception as e:
            logger.error(f"Error sending reminder to {user_id}: {e}")
            return False
    
    async def process_reminders(self, bot: Bot) -> dict:
        """
        Process all pending reminders.
        
        Returns:
            dict: Statistics of reminder processing
        """
        pending_users = await self.check_pending_reminders()
        
        if not pending_users:
            logger.debug("No pending reminders")
            return {'total': 0, 'sent': 0, 'failed': 0}
        
        sent = 0
        failed = 0
        
        logger.info(f"Processing {len(pending_users)} pending reminders")
        
        for user_data in pending_users:
            user_id = user_data['user_id']
            
            # Get user's language
            lang = await self.db.get_language(user_id) or 'en'
            
            # Load texts for user's language
            import json
            from pathlib import Path
            locales_dir = Path(__file__).parent.parent / "locales"
            with open(locales_dir / f"{lang}.json", "r", encoding="utf-8") as f:
                texts = json.load(f)
            
            success = await self.send_reminder(bot, user_id, texts)
            
            if success:
                sent += 1
            else:
                failed += 1
        
        stats = {
            'total': len(pending_users),
            'sent': sent,
            'failed': failed
        }
        
        logger.info(f"Reminder processing completed: {stats}")
        return stats
