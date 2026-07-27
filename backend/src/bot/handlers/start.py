"""
Seeker Bot — /start and /help handlers.
"""

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from src.common.logging import logger

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    logger.info("cmd_start", user_id=message.from_user.id)

    welcome_text = (
        "👋 <b>Добро пожаловать в Seeker Bot!</b>\n\n"
        "Я собираю новости культуры со всей России:\n"
        "🎨 Выставки\n"
        "🎭 Театр\n"
        "🎬 Кино\n"
        "🏛 Музеи\n"
        "🎵 Концерты\n"
        "🎪 Фестивали\n\n"
        "Чтобы начать настройку, отправьте /settings.\n"
        "Для просмотра ленты — /feed.\n"
        "Помощь — /help."
    )
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = (
        "<b>📖 Помощь по Seeker Bot</b>\n\n"
        "/start — Запуск и приветствие\n"
        "/help — Это сообщение\n"
        "/feed — Персонализированная лента событий\n"
        "/today — События на сегодня\n"
        "/settings — Настройка городов и категорий\n"
        "/search <запрос> — Поиск по событиям\n"
        "/subscribe — Настройка уведомлений\n"
        "/unsubscribe — Отключить уведомления\n\n"
        ""
        "Также вы можете открыть <b>Mini App</b> для удобного просмотра и фильтрации."
    )
    await message.answer(help_text)
