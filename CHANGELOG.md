# CHANGELOG

## [0.1.0] — 2026-07-27

### Added
- ✨ Каркас проекта: структура директорий, Docker Compose, Dockerfile
- ✨ Модели БД: User, Event, City, Category, ContentSource, SourceItem, NotificationLog
- ✨ Миграция Alembic (001_initial_schema) — все таблицы
- ✨ FastAPI health endpoint (/health)
- ✨ aiogram бот с /start и /help
- ✨ Middleware авторегистрации пользователя
- ✨ Конфигурация Pydantic Settings
- ✨ Структурированное логирование (structlog)
- ✨ .env.example с переменными окружения
- ✨ data/categories.yml — конфигурация категорий с ключевыми словами
- ✨ data/cities.yml — конфигурация городов с морфологическими формами
