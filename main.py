import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.db import db
from handlers.basic import router as basic_router
from handlers.valuation import router as valuation_router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(basic_router)
    dp.include_router(valuation_router)
    
    try:
        logger.info("Подключение к базе данных...")
        await db.connect()
        logger.info("База данных подключена")
        
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    finally:
        logger.info("Закрытие соединения с БД...")
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
