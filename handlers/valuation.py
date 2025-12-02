import asyncio
import json
import re
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import db
from states import BotStates
from services.logic import get_valuation_data, check_username_exists
from keyboards.builders import get_valuation_kb, get_sell_kb, get_main_menu


router = Router()

LOCALES_DIR = Path(__file__).parent.parent / "locales"


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


@router.message(BotStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    """Process username input for valuation."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    
    username = message.text.strip()
    
    if not is_valid_username(username):
        await message.answer(texts["error_format"])
        return
    
    # Send "evaluating" message
    eval_msg = await message.answer(texts["evaluating"].format(username=username))
    
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
    
    # Save current username to state for sell_current callback
    await state.update_data(last_username=username)
    
    await message.answer(
        result,
        reply_markup=get_valuation_kb(texts)
    )


@router.callback_query(F.data == "eval_again")
async def callback_eval_again(callback: CallbackQuery, state: FSMContext):
    """Handle 'Get another valuation' button."""
    lang = await db.get_language(callback.from_user.id)
    texts = load_texts(lang)
    
    await callback.message.answer(texts["lang_set"])
    await state.set_state(BotStates.waiting_for_username)
    await callback.answer()


@router.callback_query(F.data == "sell_current")
async def callback_sell_current(callback: CallbackQuery, state: FSMContext):
    """Handle 'Sell this handle' button."""
    lang = await db.get_language(callback.from_user.id)
    texts = load_texts(lang)
    
    data = await state.get_data()
    username = data.get("last_username", "your handle")
    
    await callback.message.answer(
        texts["sell_info"].format(username=username),
        reply_markup=get_sell_kb(texts)
    )
    await callback.answer()
