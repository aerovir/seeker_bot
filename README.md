# Seeker Bot 🎭

**Telegram-бот + Mini App + Telegram-канал** для агрегации и публикации новостей культуры России.

Парсинг из множества источников (RSS, API), персонализация по городу и тематике, интеграция с билетными сервисами, публикация в Telegram-канал.

---

## Архитектура

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Парсер     │──▶│     БД       │──▶│  Публицист   │──▶📢 Канал
│  (Celery)    │   │  PostgreSQL  │   │  (aiogram)   │
│  RSS/Scrape  │   │              │   │              │
└──────────────┘   └──┬──┬───────┘   └──────────────┘
                      │  │
           ┌──────────┘  └──────────┐
           ▼                        ▼
    ┌──────────────┐          ┌──────────────┐
    │  TMA (React) │          │  Bot (aiogram)│
    │  Личная      │          │  Дайджесты    │
    │  фильтрация  │          │  Уведомления  │
    └──────────────┘          └──────────────┘
              │
              ▼
       FastAPI (REST API)
```

### 6 фаз реализации

| Фаза | Компонент | Статус |
|------|-----------|--------|
| 0 | 🏗 Фундамент — Docker, БД, бот, health | ✅ |
| 1 | 📡 Content Pipeline — RSS, классификация, pipeline | ✅ |
| 2 | 🌐 TMA Backend — API, auth, feed/settings endpoints | ✅ |
| 3 | 🎨 TMA Frontend — React + Vite + @tma.js | ✅ |
| 4 | 📢 Публицист — очередь постов, канал, админ-команды | ✅ |
| 5 | 🎫 Билеты + Уведомления — TicketAdapters, дайджесты | ✅ |
| 6 | ✨ Полировка — интеграционные тесты, CI, документация | ✅ |

---

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone git@github.com:aerovir/seeker_bot.git
cd seeker_bot
cp .env.example .env
```

### 2. Заполните `.env`

```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=postgresql+asyncpg://seeker:seeker_dev_pass@postgres:5432/seeker_bot
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
ADMIN_IDS=[123456789]  # JSON-массив ID администраторов
TMA_URL=http://localhost:5173
```

### 3. Запуск (Docker Compose)

```bash
docker compose up -d
```

Запускает 5 сервисов:
- **bot** — aiogram бот (публицист + команды)
- **api** — FastAPI (REST API для TMA)
- **celery-worker** — обработка задач
- **celery-beat** — планировщик задач
- **postgres** — база данных
- **redis** — кэш и брокер

### 4. Миграции БД

```bash
docker compose exec bot alembic upgrade head
```

### 5. TMA Frontend (отдельно)

```bash
cd frontend
npm install
npm run dev   # порт 5173, прокси на /api → localhost:8000
```

### 6. Запуск тестов

```bash
cd backend
BOT_TOKEN=test:token python3 -m pytest tests/ -v
```

---

## API Endpoints

### Публичные

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Health check |
| GET | `/api/v1/feed` | Лента событий (пагинация) |
| GET | `/api/v1/events` | Список с фильтрами |
| GET | `/api/v1/events/{id}` | Детальная карточка |
| GET | `/api/v1/cities` | Список городов |
| GET | `/api/v1/categories` | Список категорий |

### Авторизованные (TMA)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/preferences/` | Настройки пользователя |
| PUT | `/api/v1/preferences/` | Обновить города и категории |
| GET | `/api/v1/preferences/cities` | Выбранные города |
| GET | `/api/v1/preferences/categories` | Выбранные категории |

**Аутентификация**: `Authorization: tma {initData}`

### Команды бота

| Команда | Доступ | Описание |
|---------|--------|----------|
| `/start` | Все | Приветствие |
| `/help` | Все | Помощь |
| `/feed` | Все | Персонализированная лента |
| `/post <id>` | Админ | Запланировать пост |
| `/queue` | Админ | Очередь публикаций |
| `/publish_all` | Админ | Опубликовать всё сейчас |
| `/candidates` | Админ | Кандидаты на публикацию |

---

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| **Backend** | Python 3.12+ (FastAPI, aiogram 3, SQLAlchemy 2.0) |
| **Task Queue** | Celery 5 + Redis |
| **Frontend** | React 19 + TypeScript + Vite (@tma.js) |
| **Database** | PostgreSQL 16 (asyncpg) |
| **Cache/Broker** | Redis 7 |
| **Container** | Docker + Docker Compose |
| **CI** | GitHub Actions |

---

## Структура проекта

```
seeker_bot/
├── backend/                  # Python-бэкенд
│   ├── src/
│   │   ├── api/              # FastAPI роутеры (TMA endpoints)
│   │   ├── aggregator/       # Парсер-пайплайн (RSS, классификация)
│   │   ├── bot/              # aiogram бот (handlers, middleware)
│   │   ├── common/           # Логирование, константы, исключения
│   │   ├── db/               # SQLAlchemy модели, session
│   │   ├── nlp/              # NLP для русского языка
│   │   ├── repositories/     # Data Access Layer
│   │   ├── services/         # Бизнес-логика
│   │   └── tickets/          # Ticket Adapters
│   ├── celery_app/           # Celery задачи
│   ├── alembic/              # Миграции БД
│   ├── data/                 # YAML-конфиги (sources, categories, cities)
│   └── tests/                # 128 тестов
├── frontend/                 # TMA React-приложение
│   └── src/
│       ├── api/              # HTTP-клиент
│       ├── components/       # EventCard, CityPicker, и др.
│       ├── hooks/            # useTMA, useFeed, usePreferences
│       ├── pages/            # Feed, EventDetail, Settings, Search
│       └── utils/            # Форматирование
├── .github/workflows/        # CI
├── docker-compose.yml
└── README.md
```

---

## Источники контента

18 RSS-лент в `backend/data/sources.yml`. Основные источники:
- **Culture.ru** — новости и афиша
- **KudaGo** — Москва и Санкт-Петербург
- **TimeOut** — Москва
- **Третьяковская галерея** — новости и выставки
- **ГМИИ им. Пушкина**, **Эрмитаж**, **Русский музей**
- **Большой театр**, **Мариинский театр**
- **Кинопоиск**
- **Афиша Daily**

---

## Инфраструктура

| Этап | Мощности | Бюджет/мес |
|------|----------|------------|
| Разработка (Phase 0-1) | 1 vCPU, 2 GB RAM | ~$6 |
| TMA (Phase 2-3) | 2 vCPU, 4 GB RAM + S3 | ~$17 |
| Production (Phase 4-6) | 2 vCPU + managed PG/Redis | ~$60-120 |

---

## Лицензия

MIT
