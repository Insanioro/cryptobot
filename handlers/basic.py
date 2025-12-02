import json
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode

from database.db import db
from states import BotStates
from keyboards.builders import get_lang_kb, get_main_menu, get_sell_kb, get_channel_kb
from config import CHANNEL_URL
from handlers.valuation import evaluate_username


router = Router()

LOCALES_DIR = Path(__file__).parent.parent / "locales"


def load_texts(lang: str) -> dict:
    """Load localization texts for specified language."""
    file_path = LOCALES_DIR / f"{lang}.json"
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load all languages for button text matching
ALL_TEXTS = {
    "en": load_texts("en"),
    "ru": load_texts("ru"),
    "es": load_texts("es"),
}


def get_all_button_texts(key: str) -> list[str]:
    """Get button text in all languages for filtering."""
    return [ALL_TEXTS[lang][key] for lang in ALL_TEXTS]


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    await db.add_user(message.from_user.id)
    texts = load_texts("en")
    await message.answer(
        texts["welcome"],
        reply_markup=get_lang_kb()
    )


@router.callback_query(F.data.startswith("lang_"))
async def process_language(callback: CallbackQuery, state: FSMContext):
    """Handle language selection."""
    lang = callback.data.split("_")[1]  # lang_en -> en
    await db.set_language(callback.from_user.id, lang)
    
    texts = load_texts(lang)
    await state.update_data(lang=lang)
    
    await callback.message.answer(
        texts["lang_set"],
        reply_markup=get_main_menu(texts),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(BotStates.waiting_for_username)
    await callback.answer()


@router.message(F.text.in_(get_all_button_texts("btn_lang")))
async def btn_change_language(message: Message):
    """Handle 'Change language' button."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    await message.answer(
        texts["welcome"],
        reply_markup=get_lang_kb()
    )


@router.message(F.text.in_(get_all_button_texts("btn_method")))
async def btn_methodology(message: Message):
    """Handle 'Valuation methodology' button."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    await message.answer(texts["methodology"])


@router.message(F.text.in_(get_all_button_texts("btn_sell")))
async def btn_sell(message: Message):
    """Handle 'Sell your handle' button."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    await message.answer(
        texts["sell_info"].format(username="your handle"),
        reply_markup=get_sell_kb(texts)
    )


@router.message(F.text.in_(get_all_button_texts("btn_evaluate")))
async def btn_evaluate(message: Message, state: FSMContext):
    """Handle 'Evaluate a handle' button - evaluate user's own username."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    
    # Получаем username пользователя
    user_username = message.from_user.username
    
    if not user_username:
        # Если у пользователя нет username - просим ввести вручную
        await message.answer(texts["no_username"], parse_mode=ParseMode.HTML)
        await state.set_state(BotStates.waiting_for_username)
        return
    
    # Сразу оцениваем username пользователя
    await evaluate_username(user_username, message, state, lang, texts)


@router.message(F.text.in_(get_all_button_texts("btn_channel")))
async def btn_channel(message: Message):
    """Handle 'Channel' button - send channel link."""
    lang = await db.get_language(message.from_user.id)
    texts = load_texts(lang)
    await message.answer(
        texts["channel_info"],
        reply_markup=get_channel_kb(texts)
    )
