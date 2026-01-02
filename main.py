# main.py — ИСПРАВЛЕННАЯ ВЕРСИЯ
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# ИМПОРТЫ
from config import BOT_TOKEN
from database.db import init_db, close_db
from middlewares.auth_middleware import AuthMiddleware
from handlers.user_handlers import router as user_router
from handlers.admin_handlers import router as admin_router
from handlers.subscription_handlers import router as sub_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск LegitimVPN бота...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Инициализация базы данных
    await init_db()
    logger.info("✅ База данных инициализирована")
    
    # Подключение middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(sub_router)
    
    logger.info("✅ Роутеры зарегистрированы")
    
    try:
        # Удаление вебхука и запуск polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ LegitimVPN бот успешно запущен!")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await close_db()
        logger.info("⛔ Бот остановлен")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Бот остановлен пользователем")