"""Service for broadcast functionality."""
import asyncio
import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import FSInputFile
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from database.db import Database


logger = logging.getLogger(__name__)


class BroadcastService:
    """Service for managing broadcasts."""
    
    def __init__(self, db: Database):
        self.db = db
    
    async def get_active_users(self) -> list[dict]:
        """Get list of active users for broadcast."""
        return await self.db.get_active_users_for_broadcast()
    
    async def send_broadcast_message(
        self,
        bot: Bot,
        user_id: int,
        text: str,
        photo: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send broadcast message to a single user.
        
        Returns:
            tuple: (success: bool, error_message: Optional[str])
        """
        try:
            if photo:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=FSInputFile(photo),
                    caption=text
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=text
                )
            return (True, None)
        
        except TelegramForbiddenError:
            # User blocked the bot
            await self.db.mark_user_blocked(user_id)
            logger.info(f"User {user_id} has blocked the bot")
            return (False, "blocked")
        
        except TelegramBadRequest as e:
            logger.warning(f"Bad request for user {user_id}: {e}")
            return (False, f"bad_request: {e}")
        
        except Exception as e:
            logger.error(f"Error sending broadcast to user {user_id}: {e}")
            return (False, f"error: {e}")
    
    async def execute_broadcast(
        self,
        bot: Bot,
        text: str,
        photo: Optional[str] = None,
        delay: float = 0.05
    ) -> dict:
        """
        Execute broadcast to all active users.
        
        Args:
            bot: Bot instance
            text: Message text
            photo: Optional path to photo file
            delay: Delay between messages in seconds (default 0.05s = 20 msg/s)
        
        Returns:
            dict: Statistics of the broadcast
        """
        users = await self.get_active_users()
        total = len(users)
        success = 0
        blocked = 0
        failed = 0
        
        logger.info(f"Starting broadcast to {total} users")
        
        for user in users:
            user_id = user['user_id']
            is_success, error = await self.send_broadcast_message(
                bot, user_id, text, photo
            )
            
            if is_success:
                success += 1
            elif error == "blocked":
                blocked += 1
            else:
                failed += 1
            
            # Add delay to avoid hitting rate limits
            await asyncio.sleep(delay)
        
        stats = {
            'total': total,
            'success': success,
            'blocked': blocked,
            'failed': failed
        }
        
        logger.info(f"Broadcast completed: {stats}")
        return stats
