"""Formatting utilities for statistics display."""
from datetime import datetime, date
from typing import Optional

from database.models import EventType


def format_main_stats(stats: dict) -> str:
    """
    Format main statistics for display.
    
    Args:
        stats: Dictionary with statistics data
        
    Returns:
        Formatted string ready to send to user
    """
    text = "📊 <b>Статистика бота</b>\n\n"
    text += f"👥 Всего пользователей: <b>{stats.get('total_users', 0)}</b>\n"
    text += f"🆕 Новых за 24 часа: <b>{stats.get('new_users_24h', 0)}</b>\n"
    text += f"🔁 Запусков сегодня: <b>{stats.get('restarts_today', 0)}</b>\n\n"
    
    text += "👣 <b>Переходы:</b>\n"
    text += f"• В группу: {stats.get('group_visits', 0)}\n"
    text += f"• К менеджеру: {stats.get('manager_contacts', 0)}\n\n"
    
    text += "💰 <b>Действия:</b>\n"
    text += f"• Проверили стоимость ника: {stats.get('nickname_checks', 0)}\n"
    text += f"• Начали оформление: {stats.get('checkout_starts', 0)}\n"
    text += f"• Успешные заказы: {stats.get('successful_orders', 0)}\n"
    text += f"• Брошенные оформления: {stats.get('abandoned_checkouts', 0)}"
    
    return text


def format_date_stats(stats: dict) -> str:
    """
    Format statistics for a specific date.
    
    Args:
        stats: Dictionary with date statistics
        
    Returns:
        Formatted string
    """
    target_date = stats.get('date', date.today())
    date_str = target_date.strftime("%d.%m.%Y")
    
    text = f"📅 <b>Статистика за {date_str}</b>\n\n"
    text += f"— Новые пользователи: <b>{stats.get('new_users', 0)}</b>\n"
    text += f"— Проверок ника: {stats.get(EventType.CHECK_NICKNAME, 0)}\n"
    text += f"— Переходов в группу: {stats.get(EventType.GO_TO_GROUP, 0)}\n"
    text += f"— Переходов к менеджеру: {stats.get(EventType.CONTACT_MANAGER, 0)}\n"
    text += f"— Оформлений: {stats.get(EventType.START_CHECKOUT, 0)}\n"
    text += f"— Успешных покупок: {stats.get(EventType.SUCCESSFUL_ORDER, 0)}\n"
    text += f"— Брошенных оформлений: {stats.get(EventType.ABANDONED_CHECKOUT, 0)}"
    
    return text


def format_period_stats(stats: dict) -> str:
    """
    Format statistics for a date range.
    
    Args:
        stats: Dictionary with period statistics
        
    Returns:
        Formatted string
    """
    start_date = stats.get('start_date', date.today())
    end_date = stats.get('end_date', date.today())
    
    start_str = start_date.strftime("%d.%m.%Y")
    end_str = end_date.strftime("%d.%m.%Y")
    
    text = f"📊 <b>Статистика за период</b>\n"
    text += f"<i>{start_str} — {end_str}</i>\n\n"
    text += f"— Новые пользователи: <b>{stats.get('new_users', 0)}</b>\n"
    text += f"— Проверок ника: {stats.get(EventType.CHECK_NICKNAME, 0)}\n"
    text += f"— Переходов в группу: {stats.get(EventType.GO_TO_GROUP, 0)}\n"
    text += f"— Переходов к менеджеру: {stats.get(EventType.CONTACT_MANAGER, 0)}\n"
    text += f"— Оформлений: {stats.get(EventType.START_CHECKOUT, 0)}\n"
    text += f"— Успешных покупок: {stats.get(EventType.SUCCESSFUL_ORDER, 0)}\n"
    text += f"— Брошенных оформлений: {stats.get(EventType.ABANDONED_CHECKOUT, 0)}"
    
    return text


def format_user_card(user_data: dict, language: str = "ru") -> str:
    """
    Format user information card.
    
    Args:
        user_data: User statistics data
        language: Display language
        
    Returns:
        Formatted string
    """
    user_id = user_data.get('user_id', 0)
    username = user_data.get('username')
    first_seen = user_data.get('first_seen', datetime.now())
    last_activity = user_data.get('last_activity', datetime.now())
    
    user_display = f"@{username}" if username else f"ID {user_id}"
    
    text = f"👤 <b>Пользователь:</b> {user_display}\n"
    text += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
    text += f"📅 <b>Регистрация:</b> {first_seen.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"⏰ <b>Последняя активность:</b> {last_activity.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"🌍 <b>Язык:</b> {user_data.get('language', 'en').upper()}\n\n"
    
    event_counts = user_data.get('event_counts', {})
    if event_counts:
        text += "<b>📊 Статистика действий:</b>\n"
        for event_type, count in event_counts.items():
            emoji = EventType.get_emoji(event_type)
            text += f"{emoji} {event_type}: {count}\n"
    
    return text


def format_user_history(events: list[dict]) -> str:
    """
    Format user event history.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Formatted string
    """
    if not events:
        return "История действий пуста"
    
    text = "<b>История действий:</b>\n\n"
    
    for event in events[:20]:  # Show last 20 events
        timestamp = event.get('timestamp', datetime.now())
        time_str = timestamp.strftime('%H:%M')
        event_type = event.get('event_type', 'unknown')
        emoji = EventType.get_emoji(event_type)
        
        metadata = event.get('metadata', {})
        extra_info = ""
        
        if event_type == EventType.CHECK_NICKNAME and 'nickname' in metadata:
            extra_info = f" ({metadata['nickname']})"
        elif event_type == EventType.SUCCESSFUL_ORDER:
            if 'nickname' in metadata:
                extra_info = f" ({metadata['nickname']})"
            if 'price' in metadata:
                extra_info += f" ${metadata['price']:,}"
        
        text += f"{emoji} {time_str} — {event_type}{extra_info}\n"
    
    if len(events) > 20:
        text += f"\n<i>... и ещё {len(events) - 20} событий</i>"
    
    return text


def format_users_list(users_data: dict) -> str:
    """
    Format paginated users list.
    
    Args:
        users_data: Dictionary with users list and pagination info
        
    Returns:
        Formatted string
    """
    users = users_data.get('users', [])
    page = users_data.get('page', 1)
    total_pages = users_data.get('total_pages', 1)
    total_count = users_data.get('total_count', 0)
    
    text = f"👥 <b>Список пользователей</b>\n"
    text += f"<i>Страница {page} из {total_pages} (всего: {total_count})</i>\n\n"
    
    if not users:
        return text + "Пользователей не найдено"
    
    for user in users:
        user_id = user.get('user_id', 0)
        username = user.get('username')
        last_activity = user.get('last_activity', datetime.now())
        total_events = user.get('total_events', 0)
        
        if username:
            user_display = f"@{username}"
        else:
            user_display = f"ID {user_id}"
        
        activity_str = last_activity.strftime('%d.%m %H:%M')
        
        text += f"• {user_display}\n"
        text += f"  └ Активность: {activity_str} | События: {total_events}\n"
    
    return text


def format_event_type_stats(stats: dict, event_type: str) -> str:
    """
    Format statistics for a specific event type.
    
    Args:
        stats: Statistics dictionary
        event_type: Type of event
        
    Returns:
        Formatted string
    """
    emoji = EventType.get_emoji(event_type)
    count = stats.get(event_type, 0)
    
    text = f"{emoji} <b>Статистика: {event_type}</b>\n\n"
    text += f"Всего событий: <b>{count}</b>\n"
    
    # Add context-specific information
    if event_type == EventType.SUCCESSFUL_ORDER:
        text += "\n💰 Это успешно завершённые заказы"
    elif event_type == EventType.ABANDONED_CHECKOUT:
        text += "\n⚠️ Пользователи начали, но не завершили оформление"
    elif event_type == EventType.CHECK_NICKNAME:
        text += "\n🔍 Проверки стоимости никнеймов"
    
    return text
