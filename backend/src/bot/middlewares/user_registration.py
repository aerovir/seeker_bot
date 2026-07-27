"""
Seeker Bot — Middleware to auto-register users on any message.
"""

from typing import Callable, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser

from src.common.logging import logger
from src.db.session import async_session_factory
from src.repositories.user_repo import UserRepository


class UserRegistrationMiddleware(BaseMiddleware):
    """Auto-creates user record if it doesn't exist."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[None]],
        event: TelegramObject,
        data: dict,
    ) -> None:
        telegram_user: TelegramUser | None = None

        if hasattr(event, "from_user"):
            telegram_user = event.from_user

        if telegram_user and not telegram_user.is_bot:
            async with async_session_factory() as session:
                repo = UserRepository(session)
                user = await repo.get_by_telegram_id(telegram_user.id)

                if user is None:
                    user = await repo.create(
                        telegram_id=telegram_user.id,
                        username=telegram_user.username,
                        first_name=telegram_user.first_name,
                        last_name=telegram_user.last_name,
                        language_code=telegram_user.language_code or "ru",
                    )
                    await session.commit()
                    logger.info(
                        "user_registered",
                        user_id=telegram_user.id,
                        username=telegram_user.username,
                    )

                data["user"] = user
                data["session"] = async_session_factory()

        return await handler(event, data)
