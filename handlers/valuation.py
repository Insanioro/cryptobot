import asyncio
import json
import re
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from database.db import db
from states import BotStates
from services.logic import get_valuation_data, check_username_exists
from services.event_logger import EventLogger
from keyboards.builders import get_valuation_kb, get_sell_kb, get_main_menu


router = Router()

LOCALES_DIR = Path(__file__).parent.parent / "locales"

# Initialize event logger
event_logger = EventLogger(db)


def load_texts(lang: str) -> dict:
    """Load localization texts for specified language."""
    file_path = LOCALES_DIR / f"{lang}.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_valid_username(text: str) -> bool:
    """Validate Telegram username format."""
    # Telegram: 5-32 символов, начинается с буквы, только a-z, 0-9, _
    pattern = r'^@?[a-zA-Z][a-zA-Z0-9_]{3,31}$'
    return bool(re.match(pattern, text))


async def evaluate_username(username: str, message: Message, state: FSMContext, lang: str, texts: dict):
    """Common function to evaluate a username."""
    # Ensure username starts with @
    if not username.startswith("@"):
        username = f"@{username}"
    
    if not is_valid_username(username):
        await message.answer(texts["error_format"])
        return
    
    # Send "evaluating" message
    eval_msg = await message.answer(
        texts["evaluating"].format(username=username),
        parse_mode=ParseMode.HTML
    )
    
    # Check if username actually exists on Telegram
    exists = await check_username_exists(username)
    
    if not exists:
        await eval_msg.edit_text(texts["error_not_found"].format(username=username))
        return
    
    # Check if we have cached valuation
    cached_data = await db.get_valuation(username)
    
    if cached_data:
        data = cached_data
    else:
        # Simulate additional analysis delay
        await asyncio.sleep(3)
        
        # Get valuation data and save to cache
        data = get_valuation_data(username)
        await db.save_valuation(data)
    
    # Format result
    result = texts["result_template"].format(
        username=data["username"],
        structure=data["structure"],
        category=data["category"],
        rarity=data["rarity"],
        demand=data["demand"],
        score=data["score"],
        branding=data["branding"],
        price_low=data["price_low"],
        price_high=data["price_high"]
    )
    
    # Add valuation instructions with the evaluated username
    result += "\n\n" + texts["valuation_instructions"].format(username=username)
    
    # Save current username to state for sell_current callback
    await state.update_data(last_username=username)
    
    # Log nickname check event
    from services.event_logger import EventLogger
    event_logger = EventLogger(db)
    user_username = message.from_user.username
    metadata = {'nickname': username}
    if data:
        metadata['price_low'] = data["price_low"]
        metadata['price_high'] = data["price_high"]
    await event_logger.log_event(
        message.from_user.id,
        'check_nickname',
        metadata,
        user_username
    )
    
    # Create valuation record in database
    estimated_price = f"${data['price_low']} - ${data['price_high']}"
    await db.create_valuation(
        user_id=message.from_user.id,
        username_checked=username,
        estimated_price=estimated_price
    )
    
    # Use new valuation result keyboard
    from keyboards.builders import get_valuation_result_keyboard
    from config import MANAGER_LINK, CHANNEL_URL, SHOW_GROUP_BUTTON
    
    keyboard = get_valuation_result_keyboard(
        manager_link=MANAGER_LINK,
        channel_url=CHANNEL_URL,
        texts=texts,
        show_group_button=SHOW_GROUP_BUTTON
    )
    
    await message.answer(
        result,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@router.message(BotStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    """Process username input for valuation."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    
    username = message.text.strip()
    await evaluate_username(username, message, state, lang, texts)


@router.callback_query(F.data == "eval_again")
async def callback_eval_again(callback: CallbackQuery, state: FSMContext):
    """Handle 'Get another valuation' button."""
    lang = await db.get_language(callback.from_user.id)
    texts = load_texts(lang)
    
    await callback.message.answer(texts["lang_set"], parse_mode=ParseMode.HTML)
    await state.set_state(BotStates.waiting_for_username)
    await callback.answer()


@router.callback_query(F.data == "sell_current")
async def callback_sell_current(callback: CallbackQuery, state: FSMContext):
    """Handle 'Sell this handle' button."""
    lang = await db.get_language(callback.from_user.id)
    texts = load_texts(lang)
    
    data = await state.get_data()
    username = data.get("last_username", "your handle")
    
    # Log start checkout event
    await event_logger.log_event(
        callback.from_user.id,
        'start_checkout',
        {'nickname': username},
        callback.from_user.username
    )
    
    await callback.message.answer(
        texts["sell_info"].format(username=username),
        reply_markup=get_sell_kb(texts)
    )
    await callback.answer()
