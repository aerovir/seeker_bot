# CHANGELOG

## [0.6.0] — 2026-07-27

### Added
- ✨ TicketAdapters: YandexAfishaAdapter, KassirAdapter, DirectLinkAdapter + BaseTicketAdapter
- ✨ TicketInfo dataclass с price, provider, availability
- ✨ Enricher.integration: _enrich_tickets с перебором адаптеров
- ✨ NotificationService: send_digest, send_breaking_news, send_mass_notification
- ✨ NotificationService: get_digest_events (по предпочтениям пользователя)
- ✨ Daily + Weekly digest (Celery задачи, настоящая реализация вместо placeholder)
- ✨ _event_matches_preferences — проверка города/категории перед уведомлением
- ✨ 20 новых тестов (всего 116, все проходят)
- ✨ Pipeline: enrich_all теперь async (интеграция с ticket адаптерами)

## [0.5.0] — 2026-07-27

### Added
- ✨ PublisherService — управление очередью публикаций в Telegram-канал
- ✨ PostQueue модель + Alembic migration 002 (таблица post_queue)
- ✨ Формирование сообщений для канала: HTML, inline кнопки, изображения
- ✨ Планирование постов с отложенной публикацией (кастомная задержка)
- ✨ Celery задачи: publish_scheduled_posts (каждые 5 мин), auto_queue_events (каждые 30 мин)
- ✨ Admin-команды бота: /post, /queue, /publish_all, /candidates
- ✨ Автоматический выбор кандидатов из опубликованных событий
- ✨ 9 тестов (всего 96, все проходят)

## [0.4.0] — 2026-07-27

### Added
- ✨ TMA Frontend: React + TypeScript + Vite (@tma.js SDK)
- ✨ Страницы: Feed, EventDetail, Settings, Search
- ✨ Компоненты: EventCard, CityPicker, CategoryPicker, TicketButton, Navigation
- ✨ API client с initData авторизацией
- ✨ Hooks: useTMA, useFeed, usePreferences
- ✨ Адаптивная CSS (светлая/тёмная тема Telegram)
- ✨ Infinite scroll, поиск по событиям
- ✨ Сборка проходит чисто (0 errors)

## [0.3.0] — 2026-07-27

### Added
- ✨ TMA верификация initData (HMAC-SHA256) через Authorization header
- ✨ Pydantic схемы: EventOut, EventDetailOut, FeedResponse, PreferencesUpdate, CityOut, CategoryOut
- ✨ Public API: GET /api/v1/feed, /events, /events/:id, /cities, /categories
- ✨ Authenticated API: GET/PUT /api/v1/preferences/ + city/category sub-endpoints
- ✨ FeedService — персонализированная лента (фильтр по городу + категории + дате)
- ✨ FeedService — get_upcoming_events (7 дней), get_today_events
- ✨ UserService — get_or_create, set_city_preferences, set_category_preferences
- ✨ API dependency get_current_user — аутентификация через initData
- ✨ 26 новых тестов (всего 87, все проходят)

## [0.2.0] — 2026-07-27

### Added
- ✨ Content Pipeline: AggregationPipeline (fetch → parse → classify → dedup → enrich → store)
- ✨ RSSFetcher — асинхронная загрузка RSS-лент через aiohttp
- ✨ RSSParser — парсинг RSS/Atom в RawEvent через feedparser
- ✨ CategoryClassifier — классификация категорий (pymorphy3 + keyword matching)
- ✨ CityClassifier — извлечение города из текста (gazetteer + морфология)
- ✨ Deduplicator — дедупликация по source_item_guid
- ✨ Enricher — обогащение событий (извлечение цен из текста)
- ✨ EventService.create_from_raw() — сохранение событий с категориями и городами
- ✨ Celery app + Beat schedule + aggregation tasks
- ✨ data/sources.yml — 18 реальных RSS-лент культуры РФ
- ✨ 37 новых тестов (всего 61, все проходят)

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
