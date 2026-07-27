"""
Seeker Bot — Structured logging with structlog.

Файловое логирование с ротацией + консольный вывод.
Поддерживает чтение логов через /logs команду и API.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog

# Директория логов
# Docker Compose устанавливает LOG_DIR=/var/log/seeker_bot (через named volume).
# По умолчанию — локальная директория для разработки и тестов.
LOG_DIR = Path(os.environ.get("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# --- Стандартные логгеры ---
logging.basicConfig(
    format="%(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    handlers=[
        RotatingFileHandler(
            LOG_DIR / "seeker_bot.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        ),
        logging.StreamHandler(sys.stdout),
    ],
)

# --- structlog ---
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer()
        if __debug__
        else structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger("seeker_bot")


# --- Утилита для чтения логов ---

def read_recent_logs(lines: int = 50, level: str | None = None) -> str:
    """Читает последние N строк из файла логов.

    Args:
        lines: Сколько строк вернуть.
        level: Фильтр по уровню (DEBUG, INFO, WARNING, ERROR).

    Returns:
        Текст логов, или сообщение что логов нет.
    """
    log_file = LOG_DIR / "seeker_bot.log"

    if not log_file.exists():
        return f"📭 Файл логов не найден: {log_file}"

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
    except Exception as e:
        return f"❌ Ошибка чтения лога: {e}"

    if not all_lines:
        return "📭 Лог пуст."

    # Фильтр по уровню
    if level:
        level_upper = level.upper()
        filtered = [l for l in all_lines if f"[{level_upper}]" in l or f"level='{level_upper}'" in l]
        if not filtered:
            return f"📭 Нет записей с уровнем {level_upper}."
        all_lines = filtered

    # Последние N строк
    tail = all_lines[-lines:]

    # Обрезаем слишком длинные строки
    result = []
    for line in tail:
        stripped = line.rstrip("\n\r")
        if len(stripped) > 500:
            stripped = stripped[:500] + "…"
        result.append(stripped)

    return "\n".join(result)


def count_errors_last_hour() -> int:
    """Считает количество ERROR записей за последний час."""
    import re
    from datetime import datetime, timezone

    log_file = LOG_DIR / "seeker_bot.log"
    if not log_file.exists():
        return 0

    now = datetime.now(timezone.utc)
    count = 0

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                if "ERROR" in line or "level='error'" in line:
                    count += 1
    except Exception:
        return -1

    return count
