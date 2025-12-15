"""Admin keyboards for statistics panel."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Get main admin menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Главная статистика", callback_data="admin_stats_main")
    )
    builder.row(
        InlineKeyboardButton(text="📅 За сегодня", callback_data="admin_stats_today"),
        InlineKeyboardButton(text="📆 За вчера", callback_data="admin_stats_yesterday")
    )
    builder.row(
        InlineKeyboardButton(text="📊 За неделю", callback_data="admin_stats_week"),
        InlineKeyboardButton(text="📈 За месяц", callback_data="admin_stats_month")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Список пользователей", callback_data="admin_users_list:1")
    )
    builder.row(
        InlineKeyboardButton(text="📋 По типам событий", callback_data="admin_events_menu")
    )
    builder.row(
        InlineKeyboardButton(text="🔔 Настройки уведомлений", callback_data="admin_notifications")
    )
    
    return builder.as_markup()


def get_period_menu() -> InlineKeyboardMarkup:
    """Get period selection keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="Сегодня", callback_data="admin_period_today"),
        InlineKeyboardButton(text="Вчера", callback_data="admin_period_yesterday")
    )
    builder.row(
        InlineKeyboardButton(text="Неделя", callback_data="admin_period_week"),
        InlineKeyboardButton(text="Месяц", callback_data="admin_period_month")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")
    )
    
    return builder.as_markup()


def get_events_menu() -> InlineKeyboardMarkup:
    """Get event types menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎉 Первые запуски", callback_data="admin_event_first_start")
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Повторные запуски", callback_data="admin_event_bot_restart")
    )
    builder.row(
        InlineKeyboardButton(text="👥 Переходы в группу", callback_data="admin_event_go_to_group")
    )
    builder.row(
        InlineKeyboardButton(text="💬 Обращения к менеджеру", callback_data="admin_event_contact_manager")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Проверки ника", callback_data="admin_event_check_nickname")
    )
    builder.row(
        InlineKeyboardButton(text="🛒 Начало оформления", callback_data="admin_event_start_checkout")
    )
    builder.row(
        InlineKeyboardButton(text="✅ Успешные заказы", callback_data="admin_event_successful_order")
    )
    builder.row(
        InlineKeyboardButton(text="⚠️ Брошенные оформления", callback_data="admin_event_abandoned_checkout")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")
    )
    
    return builder.as_markup()


def get_users_pagination(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    Get pagination keyboard for users list.
    
    Args:
        page: Current page number
        total_pages: Total number of pages
        
    Returns:
        Keyboard markup
    """
    builder = InlineKeyboardBuilder()
    
    # Navigation buttons
    buttons = []
    
    if page > 1:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_users_list:{page-1}"))
    
    buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="admin_users_current"))
    
    if page < total_pages:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_users_list:{page+1}"))
    
    builder.row(*buttons)
    
    # Back button
    builder.row(
        InlineKeyboardButton(text="🔙 Назад в меню", callback_data="admin_main")
    )
    
    return builder.as_markup()


def get_user_detail_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for user detail view."""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📜 История действий", callback_data=f"admin_user_history:{user_id}")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 К списку", callback_data="admin_users_list:1")
    )
    
    return builder.as_markup()


def get_notifications_settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    """
    Get keyboard for notification settings.
    
    Args:
        settings: Current notification settings
        
    Returns:
        Keyboard markup
    """
    builder = InlineKeyboardBuilder()
    
    # New users toggle
    new_users_status = "✅" if settings.get('notify_new_users', True) else "❌"
    builder.row(
        InlineKeyboardButton(
            text=f"{new_users_status} Новые пользователи",
            callback_data="admin_notif_toggle_new_users"
        )
    )
    
    # Orders toggle
    orders_status = "✅" if settings.get('notify_orders', True) else "❌"
    builder.row(
        InlineKeyboardButton(
            text=f"{orders_status} Заказы",
            callback_data="admin_notif_toggle_orders"
        )
    )
    
    # Abandoned checkouts toggle
    abandoned_status = "✅" if settings.get('notify_abandoned_checkouts', True) else "❌"
    builder.row(
        InlineKeyboardButton(
            text=f"{abandoned_status} Брошенные оформления",
            callback_data="admin_notif_toggle_abandoned"
        )
    )
    
    # Threshold setting
    threshold = settings.get('abandoned_threshold', 10)
    builder.row(
        InlineKeyboardButton(
            text=f"Порог: {threshold}",
            callback_data="admin_notif_threshold"
        )
    )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_main")
    )
    
    return builder.as_markup()


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Get simple back to main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin_main")
    )
    return builder.as_markup()
