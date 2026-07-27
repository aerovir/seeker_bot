"""
Seeker Bot — aiogram bot entry point.

Initializes Dispatcher, registers routers and middlewares, starts polling.
"""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import settings
from src.common.logging import logger
from src.bot.handlers.start import router as start_router
from src.bot.handlers.publisher import router as publisher_router
from src.bot.middlewares.user_registration import UserRegistrationMiddleware


def create_bot() -> Bot:
    """Create and configure the bot instance."""
    return Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Create and configure the dispatcher with routers and middlewares."""
    dp = Dispatcher()

    # Register routers
    dp.include_router(start_router)
    dp.include_router(publisher_router)

    # Register middlewares
    dp.message.middleware(UserRegistrationMiddleware())

    return dp


async def main():
    """Start the bot."""
    logger.info("bot_starting")

    bot = create_bot()
    dp = create_dispatcher()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("bot_stopped")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
