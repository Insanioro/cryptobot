"""Middleware to check admin permissions."""
from typing import Callable, Awaitable, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from config import ADMIN_IDS


class AdminCheckMiddleware(BaseMiddleware):
    """Middleware to verify admin permissions."""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any]
    ) -> Any:
        """Check if user is admin before processing admin commands."""
        user_id = event.from_user.id
        
        # Check if this is an admin command/callback
        is_admin_action = False
        
        if isinstance(event, Message):
            if event.text and event.text.startswith('/admin') or event.text.startswith('/stats'):
                is_admin_action = True
        elif isinstance(event, CallbackQuery):
            if event.data and event.data.startswith('admin_'):
                is_admin_action = True
        
        # If admin action, check permissions
        if is_admin_action and user_id not in ADMIN_IDS:
            if isinstance(event, Message):
                await event.answer("❌ У вас нет доступа к этой команде")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ У вас нет доступа", show_alert=True)
            return
        
        # Add is_admin flag to data
        data['is_admin'] = user_id in ADMIN_IDS
        
        return await handler(event, data)
