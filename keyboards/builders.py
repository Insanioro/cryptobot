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
