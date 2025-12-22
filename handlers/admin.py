"""Admin handlers for statistics panel."""
import logging
from datetime import datetime, timedelta, date

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.db import db
from database.models import EventType
from services.analytics import AnalyticsService
from services.notifications import NotificationService
from states import BroadcastStates, SettingsStates
from keyboards.admin_keyboards import (
    get_admin_main_menu,
    get_events_menu,
    get_users_pagination,
    get_user_detail_keyboard,
    get_notifications_settings_keyboard,
    get_back_to_main_keyboard,
    get_settings_menu,
    get_settings_back_keyboard
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


# Broadcast handlers
@router.callback_query(F.data == "admin_broadcast")
async def callback_broadcast_menu(callback: CallbackQuery):
    """Show broadcast menu."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        from keyboards.admin_keyboards import get_broadcast_menu_keyboard
        
        text = "📣 <b>Рассылка</b>\n\n"
        text += "Здесь вы можете создать рассылку для всех пользователей бота.\n\n"
        text += "Рассылка будет отправлена всем активным пользователям (не заблокировавшим бота)."
        
        await callback.message.edit_text(
            text,
            reply_markup=get_broadcast_menu_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_menu: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "broadcast_start")
async def callback_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Start broadcast creation."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        from keyboards.admin_keyboards import get_message_type_keyboard
        from states import BroadcastStates
        
        text = "📝 <b>Создание рассылки</b>\n\n"
        text += "Выберите тип сообщения:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_message_type_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.waiting_for_message_type)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_start: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "broadcast_type_text")
async def callback_broadcast_type_text(callback: CallbackQuery, state: FSMContext):
    """Choose text-only broadcast."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        from keyboards.admin_keyboards import get_cancel_keyboard
        from states import BroadcastStates
        
        await state.update_data(broadcast_type="text")
        
        text = "📝 <b>Текст рассылки</b>\n\n"
        text += "Отправьте текст сообщения для рассылки:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.waiting_for_text)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_type_text: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "broadcast_type_photo")
async def callback_broadcast_type_photo(callback: CallbackQuery, state: FSMContext):
    """Choose photo broadcast."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        from keyboards.admin_keyboards import get_cancel_keyboard
        from states import BroadcastStates
        
        await state.update_data(broadcast_type="photo")
        
        text = "🖼 <b>Фото для рассылки</b>\n\n"
        text += "Отправьте фото:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.waiting_for_photo)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_type_photo: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(BroadcastStates.waiting_for_text)
async def handle_broadcast_text(message: Message, state: FSMContext):
    """Handle broadcast text input."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        from keyboards.admin_keyboards import get_preview_keyboard
        from states import BroadcastStates
        
        await state.update_data(broadcast_text=message.text)
        
        # Show preview
        preview_text = "👁 <b>Предпросмотр рассылки</b>\n\n"
        preview_text += "──────────────────────\n"
        preview_text += message.text
        preview_text += "\n──────────────────────\n\n"
        preview_text += "Всё верно?"
        
        await message.answer(
            preview_text,
            reply_markup=get_preview_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.confirm_broadcast)
    except Exception as e:
        logger.error(f"Error in handle_broadcast_text: {e}")
        await message.answer("❌ Ошибка")


@router.message(BroadcastStates.waiting_for_photo, F.photo)
async def handle_broadcast_photo(message: Message, state: FSMContext):
    """Handle broadcast photo input."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        from keyboards.admin_keyboards import get_cancel_keyboard
        from states import BroadcastStates
        
        # Save photo file_id
        photo_file_id = message.photo[-1].file_id
        await state.update_data(broadcast_photo=photo_file_id)
        
        text = "📝 <b>Подпись к фото</b>\n\n"
        text += "Отправьте текст, который будет под фото:"
        
        await message.answer(
            text,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.waiting_for_caption)
    except Exception as e:
        logger.error(f"Error in handle_broadcast_photo: {e}")
        await message.answer("❌ Ошибка")


@router.message(BroadcastStates.waiting_for_caption)
async def handle_broadcast_caption(message: Message, state: FSMContext):
    """Handle broadcast caption input."""
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        from keyboards.admin_keyboards import get_preview_keyboard
        from states import BroadcastStates
        
        data = await state.get_data()
        photo_file_id = data.get('broadcast_photo')
        
        await state.update_data(broadcast_text=message.text)
        
        # Show preview
        await message.answer_photo(
            photo=photo_file_id,
            caption=f"👁 <b>Предпросмотр рассылки</b>\n\n{message.text}\n\nВсё верно?",
            reply_markup=get_preview_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(BroadcastStates.confirm_broadcast)
    except Exception as e:
        logger.error(f"Error in handle_broadcast_caption: {e}")
        await message.answer("❌ Ошибка")


@router.callback_query(F.data == "broadcast_confirm")
async def callback_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot):
    """Confirm and execute broadcast."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        from services.broadcast_service import BroadcastService
        
        data = await state.get_data()
        broadcast_text = data.get('broadcast_text')
        broadcast_photo = data.get('broadcast_photo')
        broadcast_type = data.get('broadcast_type')
        
        # Delete preview message and send new status message
        try:
            await callback.message.delete()
        except Exception:
            pass
        
        status_msg = await callback.message.answer(
            "📤 Начинаю рассылку...\nЭто может занять некоторое время.",
            parse_mode="HTML"
        )
        await callback.answer()
        
        # Download photo if needed
        photo_path = None
        if broadcast_type == "photo" and broadcast_photo:
            import tempfile
            from pathlib import Path
            
            file = await bot.get_file(broadcast_photo)
            temp_dir = Path(tempfile.gettempdir())
            photo_path = temp_dir / f"broadcast_{broadcast_photo}.jpg"
            await bot.download_file(file.file_path, photo_path)
        
        # Execute broadcast
        try:
            broadcast_service = BroadcastService(db)
            stats = await broadcast_service.execute_broadcast(
                bot=bot,
                text=broadcast_text,
                photo=str(photo_path) if photo_path else None
            )
        except RuntimeError as e:
            # Database pool not ready
            logger.error(f"Database error during broadcast: {e}")
            await status_msg.edit_text(
                "❌ Ошибка подключения к базе данных.\n"
                "Попробуйте еще раз через несколько секунд.",
                reply_markup=get_admin_main_menu()
            )
            if photo_path and photo_path.exists():
                photo_path.unlink()
            await state.clear()
            return
        except Exception as e:
            logger.error(f"Error during broadcast execution: {e}")
            await status_msg.edit_text(
                f"❌ Ошибка при выполнении рассылки: {e}",
                reply_markup=get_admin_main_menu()
            )
            if photo_path and photo_path.exists():
                photo_path.unlink()
            await state.clear()
            return
        
        # Show results
        result_text = "✅ <b>Рассылка завершена!</b>\n\n"
        result_text += f"📊 Статистика:\n"
        result_text += f"• Всего пользователей: {stats['total']}\n"
        result_text += f"• Успешно отправлено: {stats['success']}\n"
        result_text += f"• Заблокировали бота: {stats['blocked']}\n"
        result_text += f"• Ошибки: {stats['failed']}\n"
        
        # Delete status message and send result
        try:
            await status_msg.delete()
        except Exception:
            pass
        
        await callback.message.answer(
            result_text,
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML"
        )
        
        # Clean up
        if photo_path and photo_path.exists():
            photo_path.unlink()
        
        await state.clear()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_confirm: {e}")
        await callback.message.answer("❌ Ошибка при выполнении рассылки")
        await state.clear()


@router.callback_query(F.data == "broadcast_cancel")
async def callback_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast creation."""
    try:
        await state.clear()
        
        text = "❌ Рассылка отменена"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_admin_main_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_cancel: {e}")
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "broadcast_edit_text")
async def callback_broadcast_edit_text(callback: CallbackQuery, state: FSMContext):
    """Edit broadcast text."""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    try:
        from keyboards.admin_keyboards import get_cancel_keyboard
        from states import BroadcastStates
        
        text = "📝 <b>Новый текст рассылки</b>\n\n"
        text += "Отправьте новый текст сообщения:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_cancel_keyboard(),
            parse_mode="HTML"
        )
        
        data = await state.get_data()
        if data.get('broadcast_type') == 'photo':
            await state.set_state(BroadcastStates.waiting_for_caption)
        else:
            await state.set_state(BroadcastStates.waiting_for_text)
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_broadcast_edit_text: {e}")


@router.callback_query(F.data == "admin_settings")
async def callback_settings_menu(callback: CallbackQuery):
    """Show system settings menu."""
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет доступа", show_alert=True)
            return
        
        # Get current settings from database
        reminder_interval = await db.get_system_setting('reminder_check_interval', '1')
        reminder_delay = await db.get_system_setting('reminder_delay_minutes', '15')
        reminder_enabled = await db.get_system_setting('reminder_enabled', 'true')
        
        text = "⚙️ <b>Настройки системы</b>\n\n"
        text += "📊 <b>Текущие настройки напоминаний:</b>\n"
        text += f"• Интервал проверки: {reminder_interval} мин\n"
        text += f"• Задержка отправки: {reminder_delay} мин\n"
        text += f"• Статус: {'✅ Включено' if reminder_enabled == 'true' else '❌ Выключено'}\n\n"
        text += "Выберите параметр для изменения:"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_menu(),
            parse_mode="HTML"
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_settings_menu: {e}")
        await callback.answer("Ошибка при загрузке настроек", show_alert=True)


@router.callback_query(F.data == "settings_reminder_interval")
async def callback_set_reminder_interval(callback: CallbackQuery, state: FSMContext):
    """Start process to set reminder check interval."""
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет доступа", show_alert=True)
            return
        
        current = await db.get_system_setting('reminder_check_interval', '1')
        
        text = "⏱ <b>Настройка интервала проверки напоминаний</b>\n\n"
        text += f"Текущее значение: <b>{current} мин</b>\n\n"
        text += "Это интервал, с которым бот проверяет базу данных на наличие "
        text += "пользователей, которым нужно отправить напоминание.\n\n"
        text += "⚠️ <b>Важно:</b> Меньший интервал = более быстрая отправка, "
        text += "но больше нагрузка на сервер.\n\n"
        text += "Введите новое значение в минутах (1-60):"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_back_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(SettingsStates.waiting_for_reminder_interval)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_set_reminder_interval: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.message(SettingsStates.waiting_for_reminder_interval)
async def process_reminder_interval(message: Message, state: FSMContext):
    """Process new reminder check interval value."""
    try:
        if message.from_user.id not in ADMIN_IDS:
            return
        
        # Validate input
        try:
            interval = int(message.text)
            if interval < 1 or interval > 60:
                await message.answer(
                    "❌ Неверное значение. Введите число от 1 до 60:",
                    reply_markup=get_settings_back_keyboard()
                )
                return
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите целое число:",
                reply_markup=get_settings_back_keyboard()
            )
            return
        
        # Save to database
        await db.set_system_setting('reminder_check_interval', str(interval), message.from_user.id)
        
        # Sync to .env file
        from services.config_sync import ConfigSyncService
        config_sync = ConfigSyncService(db)
        await config_sync.sync_to_env('reminder_check_interval', str(interval))
        
        await state.clear()
        
        text = f"✅ Интервал проверки напоминаний обновлен: <b>{interval} мин</b>\n\n"
        text += "🔄 Изменения применятся автоматически в течение 10 секунд!\n"
        text += "📝 Файл .env также обновлен"
        
        await message.answer(
            text,
            reply_markup=get_settings_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in process_reminder_interval: {e}")
        await message.answer("Ошибка при сохранении настроек")


@router.callback_query(F.data == "settings_reminder_delay")
async def callback_set_reminder_delay(callback: CallbackQuery, state: FSMContext):
    """Start process to set reminder delay."""
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ У вас нет доступа", show_alert=True)
            return
        
        current = await db.get_system_setting('reminder_delay_minutes', '15')
        
        text = "⏰ <b>Настройка задержки отправки напоминания</b>\n\n"
        text += f"Текущее значение: <b>{current} мин</b>\n\n"
        text += "Это время, которое должно пройти после оценки username, "
        text += "прежде чем пользователю будет отправлено напоминание.\n\n"
        text += "Введите новое значение в минутах (1-1440):"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_settings_back_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(SettingsStates.waiting_for_reminder_delay)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_set_reminder_delay: {e}")
        await callback.answer("Ошибка", show_alert=True)


@router.message(SettingsStates.waiting_for_reminder_delay)
async def process_reminder_delay(message: Message, state: FSMContext):
    """Process new reminder delay value."""
    try:
        if message.from_user.id not in ADMIN_IDS:
            return
        
        # Validate input
        try:
            delay = int(message.text)
            if delay < 1 or delay > 1440:
                await message.answer(
                    "❌ Неверное значение. Введите число от 1 до 1440 (24 часа):",
                    reply_markup=get_settings_back_keyboard()
                )
                return
        except ValueError:
            await message.answer(
                "❌ Пожалуйста, введите целое число:",
                reply_markup=get_settings_back_keyboard()
            )
            return
        
        # Save to database
        await db.set_system_setting('reminder_delay_minutes', str(delay), message.from_user.id)
        
        # Sync to .env file
        from services.config_sync import ConfigSyncService
        config_sync = ConfigSyncService(db)
        await config_sync.sync_to_env('reminder_delay_minutes', str(delay))
        
        await state.clear()
        
        text = f"✅ Задержка отправки напоминаний обновлена: <b>{delay} мин</b>\n\n"
        text += "📝 Файл .env также обновлен"
        
        await message.answer(
            text,
            reply_markup=get_settings_menu(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error in process_reminder_delay: {e}")
        await message.answer("Ошибка при сохранении настроек")
        await callback.answer("❌ Ошибка", show_alert=True)
