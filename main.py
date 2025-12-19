import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, REMINDER_ENABLED
from database.db import db
from handlers.basic import router as basic_router
from handlers.valuation import router as valuation_router
from handlers.admin import router as admin_router
from middleware.admin_check import AdminCheckMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def reminder_task(bot: Bot):
    """Background task to check and send reminders."""
    if not REMINDER_ENABLED:
        logger.info("Reminder task is disabled")
        return
    
    from services.reminder_service import ReminderService
    from services.config_sync import ConfigSyncService
    from datetime import datetime
    
    reminder_service = ReminderService(db)
    config_sync = ConfigSyncService(db)
    logger.info("Reminder task started with dynamic interval and .env sync")
    
    last_check_time = None
    
    while True:
        try:
            # Check and sync .env file changes
            env_synced = await config_sync.check_and_sync()
            if env_synced:
                logger.info("✅ Settings synced from .env file")
            
            # Get interval from database settings (читаем каждую итерацию)
            interval_str = await db.get_system_setting('reminder_check_interval', '1')
            try:
                interval_minutes = int(interval_str)
            except ValueError:
                interval_minutes = 1
                logger.warning(f"Invalid reminder_check_interval value: {interval_str}, using default: 1")
            
            current_time = datetime.now()
            
            # Проверяем, нужно ли выполнять проверку
            should_check = False
            if last_check_time is None:
                should_check = True  # Первый запуск
            else:
                elapsed = (current_time - last_check_time).total_seconds() / 60
                if elapsed >= interval_minutes:
                    should_check = True
            
            if should_check:
                logger.debug(f"Checking for pending reminders (interval: {interval_minutes} min)...")
                stats = await reminder_service.process_reminders(bot)
                last_check_time = current_time
                
                if stats['total'] > 0:
                    logger.info(f"Processed reminders: {stats}")
            
            # Короткий sleep для быстрой реакции на изменения интервала
            await asyncio.sleep(10)
        
        except asyncio.CancelledError:
            logger.info("Reminder task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in reminder task: {e}")
            await asyncio.sleep(60)  # Wait a bit before retrying


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Add middleware
    dp.message.middleware(AdminCheckMiddleware())
    dp.callback_query.middleware(AdminCheckMiddleware())
    
    # Include routers
    dp.include_router(admin_router)  # Admin router first for priority
    dp.include_router(basic_router)
    dp.include_router(valuation_router)
    
    # Start background tasks
    reminder_task_handle = None
    
    try:
        logger.info("Подключение к базе данных...")
        await db.connect()
        logger.info("База данных подключена")
        
        # Start reminder background task
        if REMINDER_ENABLED:
            reminder_task_handle = asyncio.create_task(reminder_task(bot))
            logger.info("Reminder task создана")
        
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    finally:
        # Cancel background tasks
        if reminder_task_handle:
            reminder_task_handle.cancel()
            try:
                await reminder_task_handle
            except asyncio.CancelledError:
                pass
        
        logger.info("Закрытие соединения с БД...")
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
