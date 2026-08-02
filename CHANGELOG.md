# CHANGELOG

## [1.2.0] — 2026-08-02

### Added
- 🚀 **Авто-деплой** на VPS через self-hosted GitHub Actions runner (job `deploy` в CI, только push в `main`)
- 🔧 Деплой: rsync кода в `/opt/seeker_bot`, генерация `.env` из GitHub secrets, `docker compose -f docker-compose.prod.yml up -d --build`, миграции, seed, healthcheck

### Fixed (найдено при реальном деплое)
- 🐛 **Celery worker падал с KeyError** (`celery_app.tasks.publisher.publish_scheduled_posts`) — модули задач не импортировались при старте. Фикс: импорт всех `celery_app.tasks.*` в `celery_app/__init__.py`
- 🐛 **`ADMIN_IDS` из секрета** — pydantic падал (`Input should be a valid list`), если секрет был одиночным числом. Фикс: нормализация в JSON-массив в workflow
- 🐛 **Дубли в RSS-лентах** (gorodskoyportal) — второй экземпляр падал на `IntegrityError ... ix_events_external_id`. Фикс: `Deduplicator.filter_new` отсекает дубли в рамках одного прогона
- 🐛 **Healthcheck api** — `curl` отсутствует в `python:3.12-slim`, контейнер висел в `health: starting`. Фикс: проверка через `urllib`

### Docs
- 📝 **DEPLOY.md** — раздел «CI/CD» переписан: авто-деплой через self-hosted runner (без SSH), актуальные секреты, настройка runner; обновлён чек-лист деплоя
- 📝 **README.md** — ссылка на DEPLOY.md в разделе «Инфраструктура»
- 📝 **CLAUDE.md** — пометка, что деплой автоматический, SSH-команда — fallback

## [1.1.0] — 2026-08-02

### Added
- ✨ 9 новых городов: Ростов-на-Дону, Самара, Челябинск, Уфа, Омск, Воронеж, Пермь, Красноярск, Волгоград
- ✨ 2 новые категории: «Детям» (🧒) и «Экскурсии» (🗺) — с классификацией и эмодзи в публикациях
- ✨ `SourceItem`-трекинг в `EventService.create_from_raw` — источник теперь запоминается для дедупликации повторных прогонов
- ✨ `RSSFetcher._looks_like_feed` — отбраковка HTML-ответов (SPA-обёртки, 404-страницы) при HTTP 200
- ✨ `RSSParser` — повторная попытка парсинга с перекодировкой windows-1251 → UTF-8
- ✨ Dry-run пайплайна: `pipeline.execute(commit=False)` + корректный rollback в `run_parser.py --dry-run`
- ✨ `PUBLISHER_CHANNEL_ID` из настроек — канал для публикаций больше не хардкод

### Changed
- 🔄 `sources.yml` переработан: проверенные живые ленты, городские афиши `gorodskoyportal.ru` (8+ городов) + культурные новости (Lenta, Газета.ru, Сноб, Jazz.ru, Mos.ru); прежние мёртвые RSS (KudaGo, музеи) убраны
- 🔄 `last_fetched_at` теперь настоящий `datetime.now(timezone.utc)` вместо placeholder
- 🔄 Dockerfile: CMD запускает uvicorn `src.api.app:app` вместо `python -m src.main`
- 🧪 Новые тесты: каталоги данных, dry-run/commit пайплайна, HTML-rejection, cp1251 re-encode, SourceItem-дедупликация, канал публикации, новые категории (всего 148, все проходят)

## [1.0.0] — 2026-07-27

### Added
- ✨ Интеграционные тесты на SQLite in-memory (12 тестов, всего 128)
- ✨ CI через GitHub Actions (backend + frontend)
- ✨ docker-compose.prod.yml для продакшен-развёртывания
- ✨ README.md с полной документацией
- ✨ .env.example — обновлён с комментариями
- ✅ Финальная проверка: 128/128 тестов, TypeScript 0 errors, Vite build успешен

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
