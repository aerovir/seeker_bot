# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Seeker Bot** — Telegram Mini App + Telegram Bot + Telegram Channel для агрегации и публикации новостей культуры России. Парсинг из множества источников (RSS, scraping, API), персонализация по городу и тематике, интеграция с билетными сервисами.

**Стек**: Python 3.12+ (FastAPI, aiogram 3, SQLAlchemy 2.0, Celery), React + TypeScript + Vite (@tma.js), PostgreSQL 16, Redis 7, Docker

## Git-правила

1. **Вся разработка ведётся в ветке `dev`**. В `main` только стабильные релизы.
2. **Каждая фича — отдельная ветка** от `dev`. Формат: `feature/parser-rss`, `feature/tma-feed`, `fix/dedup-titles`.
3. **Все изменения документируются**:
   - В `CHANGELOG.md`: фичи, фиксы, ошибки, доработки с датой и описанием
   - В commit message — осмысленное описание на русском
   - Pull Request description — что сделано, почему, как тестировать

## Тестирование (Test-First)

1. **Перед написанием любого кода пишутся тесты** (pytest + pytest-asyncio).
2. **Тесты не меняются под результат кода**. Если тест не проходит — код неправильный.
3. Если после **2 итераций изменений в коде** тесты всё ещё не проходят — **остановиться и спросить** у меня решение.
4. Тесты покрывают: бизнес-логику (сервисы), парсеры (контракты данных), классификаторы, API-эндпоинты.

## Инфраструктура

### Phase 0-1 (Фундамент + Парсер) — минимальные мощности
- **VPS**: 1 vCPU, 2 GB RAM, 40 GB SSD
- **ОС**: Ubuntu 22.04+
- **Docker + Docker Compose**
- Цель: запуск парсинга и наполнение БД

### Phase 2-3 (TMA + Frontend) — средние мощности
- **VPS**: 2 vCPU, 4 GB RAM, 60 GB SSD
- **Дополнительно**: S3-совместимое хранилище (для картинок событий)
- **Цель**: TMA + API под нагрузкой до 100 concurrent users

### Phase 4-6 (Канал + Билеты + Polishing) — production
- **Бэкенд**: 2 vCPU, 4 GB RAM (можно разделить: 1 бот + 1 celery-worker)
- **PostgreSQL**: Managed (Yandex Managed Postgres / AWS RDS) — 1 vCPU, 2 GB RAM, 20 GB SSD
- **Redis**: Managed (Yandex Redis / AWS ElastiCache) — 1 GB
- **Frontend (TMA)**: Статика на CDN / S3 + Cloudflare
- **Sentry**: error tracking (бесплатный tier)
- **Prometheus + Grafana**: мониторинг (на том же сервере)
- **Цель**: Масштаб 10 000+ пользователей

### Бюджет (ориентировочный, в месяц)
| Компонент | Phase 0-1 | Phase 2-3 | Phase 4-6 |
|-----------|-----------|-----------|-----------|
| VPS | ~$6 | ~$12 | ~$24-40 |
| PostgreSQL | — | — | ~$15-30 |
| Redis | — | — | ~$10-15 |
| S3 | — | ~$2-5 | ~$5-10 |
| Sentry | free | free | free (or ~$26) |
| **Итого** | **~$6/мес** | **~$17/мес** | **~$60-120/мес** |

### Команды разработки

```bash
# Запуск окружения
docker compose up -d

# Запуск тестов
pytest -v

# Запуск конкретного теста
pytest tests/test_rss_parser.py -v -k "test_rss_feed"

# Запуск всех тестов Phase 1 (content pipeline)
pytest tests/test_aggregator_models.py tests/test_rss_fetcher.py tests/test_rss_parser.py tests/test_category_classifier.py tests/test_city_classifier.py tests/test_deduplicator.py tests/test_event_service.py tests/test_pipeline.py tests/test_celery.py -v

# Миграции БД
alembic revision --autogenerate -m "description"
alembic upgrade head

# Celery worker (отдельный терминал)
celery -A celery_app.celery worker -l info

# Celery beat (планировщик)
celery -A celery_app.celery beat -l info
```

## Архитектура Phase 1 (Content Pipeline)

```
ContentSource (RSS/API/Scrape)
    │
    ▼
RSSFetcher.fetch() → raw bytes
    │
    ▼
RSSParser.parse() → list[RawEvent]
    │
    ▼
CategoryClassifier.classify() + CityClassifier.extract() → RawEvent.categories, .cities
    │
    ▼
Deduplicator.filter_new() → RawEvent (только новые)
    │
    ▼
Enricher.enrich_all() → list[EnrichedEvent] (цены, билеты)
    │
    ▼
EventService.create_from_raw() → Event DB model (c category/city assignments)
    │
    ▼
commit + log
```

**Классификация**: pymorphy3 лемматизация + keyword matching (Tier 1). Города — gazetteer по морфологическим формам.
**Дедупликация**: по source_item_guid (SHA256 title+link).
**Источники**: 18 RSS-лент в `data/sources.yml`.

## Архитектура Phase 2 (TMA API)

### Endpoints

| Метод | Путь | Auth | Описание |
|-------|------|------|----------|
| GET | `/health` | — | Health check |
| GET | `/api/v1/feed` | — | Публичная лента событий (пагинация) |
| GET | `/api/v1/events` | — | Список событий с фильтрами (?city_id, ?category_id, ?event_type) |
| GET | `/api/v1/events/{id}` | — | Детальная карточка события |
| GET | `/api/v1/cities` | — | Список городов |
| GET | `/api/v1/categories` | — | Список категорий с эмодзи |
| GET | `/api/v1/preferences/` | `tma {initData}` | Текущие настройки пользователя |
| PUT | `/api/v1/preferences/` | `tma {initData}` | Обновить города и категории |
| GET | `/api/v1/preferences/cities` | `tma {initData}` | Выбранные города |
| GET | `/api/v1/preferences/categories` | `tma {initData}` | Выбранные категории |

**Аутентификация TMA**: `Authorization: tma {initData}`, где initData — строка из Telegram WebApp.

### FeedService персонализация
- Фильтр по городам (OR)
- Фильтр по категориям (OR)
- Статус = PUBLISHED
- Дата: start_date >= now OR end_date >= now
- Сортировка: is_featured DESC, start_date ASC, created_at DESC
- Пагинация: page + page_size (default 20, max 100)

## TMA Frontend (Phase 3)

React + TypeScript + Vite (@tma.js SDK). Структура:

```
frontend/
├── src/
│   ├── api/client.ts          — HTTP клиент (initData авторизация)
│   ├── hooks/useTMA.ts        — Telegram WebApp API
│   ├── hooks/useFeed.ts       — Лента + infinite scroll
│   ├── hooks/usePreferences.ts — Города/категории
│   ├── pages/Feed.tsx         — Лента событий
│   ├── pages/EventDetail.tsx  — Детальная карточка
│   ├── pages/Settings.tsx     — Настройки (CityPicker + CategoryPicker)
│   ├── pages/Search.tsx       — Поиск
│   ├── components/  — EventCard, CityPicker, CategoryPicker, TicketButton, Navigation
│   ├── utils/format.ts        — Форматирование дат/цен
│   └── styles.css             — Адаптивный дизайн (светлая/тёмная тема)
├── index.html                 — Подключает telegram-web-app.js
├── vite.config.ts             — Прокси /api → backend:8000
└── package.json
```

**Разработка**: `npm run dev` (порт 5173).
**Сборка**: `npm run build` → `dist/`.

## SSH-доступ к серверу (логи и управление)

При получении доступа от пользователя — заполнить в `~/.ssh/config`:

```
Host seeker-bot
    HostName <IP-адрес сервера>
    User <username>
    Port 22
    IdentityFile ~/.ssh/seeker_bot_deploy
    StrictHostKeyChecking accept-new
```

### Команды для работы с сервером через Bash

```bash
# Общий лог (последние 50 строк)
ssh seeker-bot "tail -50 /var/log/seeker_bot/seeker_bot.log"

# Только ошибки
ssh seeker-bot "grep -c 'ERROR' /var/log/seeker_bot/seeker_bot.log"

# Docker логи контейнера
ssh seeker-bot "cd /opt/seeker_bot && docker compose logs --tail=50 bot"
ssh seeker-bot "cd /opt/seeker_bot && docker compose logs --tail=50 celery-worker"

# Следить за логом в реальном времени
ssh seeker-bot "tail -f /var/log/seeker_bot/seeker_bot.log"

# Статус всех контейнеров
ssh seeker-bot "cd /opt/seeker_bot && docker compose ps"

# Перезапуск сервиса
ssh seeker-bot "cd /opt/seeker_bot && docker compose restart bot"

# Сборка и перезапуск после git pull
ssh seeker-bot "cd /opt/seeker_bot && git pull && docker compose up -d --build"

# Системные метрики
ssh seeker-bot "free -h && echo '---' && df -h / | tail -1 && echo '---' && uptime"
```

### Локальный скрипт-помощник

```bash
# Справка
./scripts/logs.sh -h

# Последние 50 строк
./scripts/logs.sh

# Только ошибки
./scripts/logs.sh -n 20 -l ERROR

# Следить в реальном времени
./scripts/logs.sh -f

# Docker логи бота
./scripts/logs.sh -c bot -n 100

# Статистика
./scripts/logs.sh -s

# Полный Markdown-отчёт (для Claude)
./scripts/logs.sh -d
```

### Настройка сервера (однократно)

```bash
# Скопировать скрипт и запустить на сервере
scp scripts/setup-server.sh user@host:/tmp/
ssh user@host "bash /tmp/setup-server.sh"
```

### Пути на сервере

| Ресурс | Путь |
|--------|------|
| Проект | `/opt/seeker_bot/` |
| Логи | `/var/log/seeker_bot/seeker_bot.log` |
| Ротация логов | `/etc/logrotate.d/seeker_bot` |
| Docker Compose | `/opt/seeker_bot/docker-compose.yml` |

### Переменные окружения для SSH (если не настроен config)

```bash
export SEEKER_SSH_HOST="<IP-адрес>"
export SEEKER_SSH_USER="<username>"
export SEEKER_SSH_KEY="~/.ssh/seeker_bot_deploy"
```
