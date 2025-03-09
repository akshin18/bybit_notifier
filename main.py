import asyncio
import logging

from loguru import logger
from tortoise import Tortoise

from src.app import bot, dp
from src.config import settings
from src.handlers.admin import router as admin_router
from src.worker.task import listen_klines


async def on_startup() -> None:
    await init_db()
    asyncio.create_task(listen_klines())
    logger.info("Bot started!")


async def on_shutdown() -> None:
    await Tortoise.close_connections()
    logger.info("Bot stopped!")


async def init_db() -> None:
    await Tortoise.init(
        db_url=settings.DB_URL,
        modules={"models": ["src.db.models"]},
        timezone="Europe/Moscow",
    )
    await Tortoise.generate_schemas()


async def main() -> None:
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.include_routers(
        admin_router,
    )
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
