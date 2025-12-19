from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from config import ADMIN_USERNAME, CHANNEL_URL


def get_lang_kb() -> InlineKeyboardMarkup:
    """Language selection inline keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
        ],
        [
            InlineKeyboardButton(text="🇪🇸 Español", callback_data="lang_es"),
        ]
    ])


def get_main_menu(texts: dict) -> ReplyKeyboardMarkup:
    """Main menu reply keyboard with buttons from localization."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=texts["btn_evaluate"]),
                KeyboardButton(text=texts["btn_sell"]),
            ],
            [
                KeyboardButton(text=texts["btn_lang"]),
                KeyboardButton(text=texts["btn_method"]),
            ],
            [
                KeyboardButton(text=texts["btn_channel"]),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True
    )


def get_valuation_kb(texts: dict) -> InlineKeyboardMarkup:
    """Inline keyboard under valuation result."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=texts["btn_sell_this"], 
                callback_data="sell_current"
            ),
        ],
        [
            InlineKeyboardButton(
                text=texts["btn_another"], 
                callback_data="eval_again"
            ),
        ],
        [
            InlineKeyboardButton(
                text=texts["btn_contact"], 
                url=f"https://t.me/{ADMIN_USERNAME}"
            ),
        ],
        [
            InlineKeyboardButton(
                text=texts["btn_channel"], 
                url=CHANNEL_URL
            ),
        ],
    ])


def get_valuation_result_keyboard(
    manager_link: str,
    channel_url: str,
    texts: dict,
    show_group_button: bool = False
) -> InlineKeyboardMarkup:
    """
    Enhanced keyboard after username valuation with expert button.
    
    Args:
        manager_link: Link to manager
        channel_url: Link to channel/group
        texts: Localization texts
        show_group_button: Whether to show group button
    """
    buttons = [
        [
            InlineKeyboardButton(
                text=texts.get("button_continue_to_expert", "✅ Продолжить к эксперту"),
                url=manager_link
            ),
        ]
    ]
    
    if show_group_button:
        buttons.append([
            InlineKeyboardButton(
                text=texts.get("button_join_group", "🔹 Перейти в группу"),
                url=channel_url
            ),
        ])
    
    buttons.append([
        InlineKeyboardButton(
            text=texts.get("btn_another", "🔄 Проверить другой"),
            callback_data="eval_again"
        ),
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_manager_keyboard(manager_link: str, texts: dict) -> InlineKeyboardMarkup:
    """Simple keyboard with manager contact button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=texts.get("button_contact_manager", "Написать менеджеру"),
                url=manager_link
            ),
        ]
    ])


def get_sell_kb(texts: dict) -> InlineKeyboardMarkup:
    """Inline keyboard for sell confirmation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=texts["btn_proceed"], 
                url=f"https://t.me/{ADMIN_USERNAME}"
            ),
        ],
        [
            InlineKeyboardButton(
                text=texts["btn_channel"], 
                url=CHANNEL_URL
            ),
        ],
    ])


def get_channel_kb(texts: dict) -> InlineKeyboardMarkup:
    """Inline keyboard for channel link."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=texts["btn_go_channel"], 
                url=CHANNEL_URL
            ),
        ],
    ])
