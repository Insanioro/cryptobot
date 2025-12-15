"""Admin handlers for statistics panel."""
import logging
from datetime import datetime, timedelta, date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.db import db
from database.models import EventType
from services.analytics import AnalyticsService
from services.notifications import NotificationService
from keyboards.admin_keyboards import (
    get_admin_main_menu,
    get_events_menu,
    get_users_pagination,
    get_user_detail_keyboard,
    get_notifications_settings_keyboard,
    get_back_to_main_keyboard
)
from utils.formatters import (
    format_main_stats,
    format_date_stats,
    format_period_stats,
    format_user_card,
    format_user_history,
    format_users_list
)
from config import ADMIN_IDS


router = Router()
logger = logging.getLogger(__name__)

# Initialize services
analytics = AnalyticsService(db)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command - open admin panel."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    text = "🔧 <b>Админ-панель</b>\n\n"
    text += "Выберите действие:"
    
    await message.answer(
        text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Handle /stats command - show main statistics."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    try:
        stats = await analytics.get_main_stats()
        text = format_main_stats(stats)
        
        await message.answer(
            text,
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error getting main stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.message(Command("stats_today"))
async def cmd_stats_today(message: Message):
    """Handle /stats_today command - statistics for today."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    try:
        today = date.today()
        stats = await analytics.get_stats_by_date(today)
        text = format_date_stats(stats)
        
        await message.answer(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error getting today stats: {e}")
        await message.answer("❌ Ошибка при получении статистики")


@router.message(Command("stats_users"))
async def cmd_stats_users(message: Message):
    """Handle /stats_users command - list of users."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    try:
        users_data = await analytics.get_users_list(page=1, page_size=10)
        text = format_users_list(users_data)
        
        await message.answer(
            text,
            reply_markup=get_users_pagination(
                users_data['page'],
                users_data['total_pages']
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        await message.answer("❌ Ошибка при получении списка пользователей")


@router.message(Command("stats_events"))
async def cmd_stats_events(message: Message):
    """Handle /stats_events command - events by type."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    await message.answer(
        "📋 <b>Статистика по типам событий</b>\n\nВыберите тип:",
        reply_markup=get_events_menu(),
        parse_mode="HTML"
    )


# ==================== Callback Handlers ====================


@router.callback_query(F.data == "admin_main")
async def callback_admin_main(callback: CallbackQuery):
    """Return to main admin menu."""
    text = "🔧 <b>Админ-панель</b>\n\n"
    text += "Выберите действие:"
    
    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats_main")
async def callback_stats_main(callback: CallbackQuery):
    """Show main statistics."""
    try:
        stats = await analytics.get_main_stats()
        text = format_main_stats(stats)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_stats_main: {e}")
        await callback.answer("❌ Ошибка при получении статистики", show_alert=True)


@router.callback_query(F.data == "admin_stats_today")
async def callback_stats_today(callback: CallbackQuery):
    """Show statistics for today."""
    try:
        today = date.today()
        stats = await analytics.get_stats_by_date(today)
        text = format_date_stats(stats)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_stats_today: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_stats_yesterday")
async def callback_stats_yesterday(callback: CallbackQuery):
    """Show statistics for yesterday."""
    try:
        yesterday = date.today() - timedelta(days=1)
        stats = await analytics.get_stats_by_date(yesterday)
        text = format_date_stats(stats)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_stats_yesterday: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_stats_week")
async def callback_stats_week(callback: CallbackQuery):
    """Show statistics for the last week."""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        stats = await analytics.get_stats_for_period(start_date, end_date)
        text = format_period_stats(stats)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_stats_week: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_stats_month")
async def callback_stats_month(callback: CallbackQuery):
    """Show statistics for the last month."""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        stats = await analytics.get_stats_for_period(start_date, end_date)
        text = format_period_stats(stats)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_stats_month: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_events_menu")
async def callback_events_menu(callback: CallbackQuery):
    """Show events type menu."""
    await callback.message.edit_text(
        "📋 <b>Статистика по типам событий</b>\n\nВыберите тип:",
        reply_markup=get_events_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_event_"))
async def callback_event_stats(callback: CallbackQuery):
    """Show statistics for specific event type."""
    try:
        event_type = callback.data.replace("admin_event_", "")
        
        # Get today's stats for this event
        today = date.today()
        stats = await analytics.get_stats_by_date(today)
        
        emoji = EventType.get_emoji(event_type)
        count = stats.get(event_type, 0)
        
        text = f"{emoji} <b>Статистика: {event_type}</b>\n\n"
        text += f"Сегодня: <b>{count}</b>\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_main_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_event_stats: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_users_list:"))
async def callback_users_list(callback: CallbackQuery):
    """Show paginated users list."""
    try:
        page = int(callback.data.split(":")[1])
        users_data = await analytics.get_users_list(page=page, page_size=10)
        text = format_users_list(users_data)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_users_pagination(
                users_data['page'],
                users_data['total_pages']
            ),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_users_list: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_users_current")
async def callback_users_current(callback: CallbackQuery):
    """Handle click on current page indicator."""
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_detail:"))
async def callback_user_detail(callback: CallbackQuery):
    """Show detailed user information."""
    try:
        user_id = int(callback.data.split(":")[1])
        user_data = await analytics.get_user_summary(user_id)
        
        if not user_data:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        text = format_user_card(user_data)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_user_detail_keyboard(user_id),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_user_detail: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_user_history:"))
async def callback_user_history(callback: CallbackQuery):
    """Show user event history."""
    try:
        user_id = int(callback.data.split(":")[1])
        events = await analytics.get_user_history(user_id, limit=20)
        
        user_data = await analytics.get_user_summary(user_id)
        if not user_data:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return
        
        username = user_data.get('username')
        user_display = f"@{username}" if username else f"ID {user_id}"
        
        text = f"👤 <b>Пользователь:</b> {user_display}\n\n"
        text += format_user_history(events)
        
        await callback.message.edit_text(
            text,
            reply_markup=get_user_detail_keyboard(user_id),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_user_history: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_notifications")
async def callback_notifications(callback: CallbackQuery):
    """Show notification settings."""
    try:
        settings = await db.get_notification_settings(callback.from_user.id)
        
        text = "🔔 <b>Настройки уведомлений</b>\n\n"
        text += "Выберите типы уведомлений, которые хотите получать:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_notifications_settings_keyboard(settings),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_notifications: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_notif_toggle_new_users")
async def callback_toggle_new_users(callback: CallbackQuery):
    """Toggle new users notifications."""
    try:
        settings = await db.get_notification_settings(callback.from_user.id)
        new_value = not settings.get('notify_new_users', True)
        
        await db.update_notification_settings(
            callback.from_user.id,
            notify_new_users=new_value
        )
        
        settings['notify_new_users'] = new_value
        
        text = "🔔 <b>Настройки уведомлений</b>\n\n"
        text += "Выберите типы уведомлений, которые хотите получать:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_notifications_settings_keyboard(settings),
            parse_mode="HTML"
        )
        await callback.answer("✅ Настройка обновлена")
    except Exception as e:
        logger.error(f"Error in callback_toggle_new_users: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_notif_toggle_orders")
async def callback_toggle_orders(callback: CallbackQuery):
    """Toggle order notifications."""
    try:
        settings = await db.get_notification_settings(callback.from_user.id)
        new_value = not settings.get('notify_orders', True)
        
        await db.update_notification_settings(
            callback.from_user.id,
            notify_orders=new_value
        )
        
        settings['notify_orders'] = new_value
        
        text = "🔔 <b>Настройки уведомлений</b>\n\n"
        text += "Выберите типы уведомлений, которые хотите получать:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_notifications_settings_keyboard(settings),
            parse_mode="HTML"
        )
        await callback.answer("✅ Настройка обновлена")
    except Exception as e:
        logger.error(f"Error in callback_toggle_orders: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_notif_toggle_abandoned")
async def callback_toggle_abandoned(callback: CallbackQuery):
    """Toggle abandoned checkout notifications."""
    try:
        settings = await db.get_notification_settings(callback.from_user.id)
        new_value = not settings.get('notify_abandoned_checkouts', True)
        
        await db.update_notification_settings(
            callback.from_user.id,
            notify_abandoned_checkouts=new_value
        )
        
        settings['notify_abandoned_checkouts'] = new_value
        
        text = "🔔 <b>Настройки уведомлений</b>\n\n"
        text += "Выберите типы уведомлений, которые хотите получать:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_notifications_settings_keyboard(settings),
            parse_mode="HTML"
        )
        await callback.answer("✅ Настройка обновлена")
    except Exception as e:
        logger.error(f"Error in callback_toggle_abandoned: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)
