# Seeker Bot — Развёртывание и инфраструктура

## 1. Переменные окружения (GitHub Secrets / .env)

### Обязательные

| Переменная | Описание | Пример |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram-бота от @BotFather | `123456:ABC-DEF123...` |
| `DATABASE_URL` | Строка подключения к PostgreSQL (asyncpg) | `postgresql+asyncpg://user:pass@host:5432/seeker_bot` |
| `REDIS_URL` | Строка подключения к Redis | `redis://user:pass@host:6379/0` |

### Для администрирования

| Переменная | Описание | Пример |
|---|---|---|
| `ADMIN_IDS` | Telegram ID администраторов (JSON-массив) | `[123456789, 987654321]` |
| `PUBLISHER_CHANNEL_ID` | ID канала для публициста | `@my_channel` или `-1001234567890` |

### Опциональные

| Переменная | Описание |
|---|---|
| `SENTRY_DSN` | DSN для Sentry (error tracking) |
| `YANDEX_AFISHA_API_KEY` | API ключ Яндекс Афиши |
| `KASSIR_API_KEY` | API ключ Kassir.ru |
| `TMA_URL` | URL фронтенда Telegram Mini App |
| `TMA_SECRET` | Секретный ключ для TMA |
| `LOG_LEVEL` | Уровень логирования (по умолчанию `INFO`) |
| `POSTGRES_PASSWORD` | Пароль PostgreSQL (для docker-compose) |

---

## 2. Системные требования по этапам

### 🟢 Этап 1: MVP / Разработка

**VPS**: 2 vCPU, 4 GB RAM, 60 GB SSD, Ubuntu 22.04+

Всё на одном сервере через Docker Compose.

**Состав:**
- `bot` — aiogram (публицист + команды)
- `api` — FastAPI (REST API для TMA)
- `celery-worker` — обработка задач
- `celery-beat` — планировщик
- `postgres:16-alpine` — БД (в контейнере)
- `redis:7-alpine` — кэш + брокер
- `nginx` — прокси для TMA + статика

**Нагрузка**: до ~1 000 пользователей, до 50 RSS-источников

**Бюджет**: ~$12–17/мес

```bash
# Деплой одной командой
git clone git@github.com:aerovir/seeker_bot.git
cd seeker_bot
cp .env.example .env
# Заполнить .env
docker compose up -d
docker compose exec bot alembic upgrade head
```

---

### 🟡 Этап 2: Production (10 000+ пользователей)

**Раздельная инфраструктура:**

| Сервер | Мощности | Назначение | Стоимость |
|---|---|---|---|
| **VPS #1** | 2–4 vCPU, 4–8 GB RAM | bot + api + celery-worker | ~$20–40/мес |
| **PostgreSQL** | Managed 1–2 vCPU, 2–4 GB | Основная БД | ~$15–30/мес |
| **Redis** | Managed 1–2 GB | Кэш + Celery broker | ~$10–15/мес |
| **TMA Frontend** | S3 + Cloudflare / CDN | Статика фронтенда | ~$5–10/мес |
| **Мониторинг** | Sentry + Prometheus + Grafana | На том же VPS | free–$26/мес |
| **Итого** | | | **~$60–120/мес** |

**Особенности:**
- PostgreSQL выносится из Docker в managed-сервис (Yandex Managed Postgres / AWS RDS / TimeScale)
- Redis выносится в managed-сервис (Yandex Redis / AWS ElastiCache)
- Celery-воркеры можно масштабировать горизонтально
- Для бота используется `docker-compose.prod.yml`
- Nginx с кэшированием статики, SSL (Let's Encrypt)

```bash
# Production-запуск
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec bot alembic upgrade head
```

---

### 🟠 Этап 3: Enterprise (десятки тысяч пользователей)

| Компонент | Мощности |
|---|---|
| **Bot** | 2× 2–4 vCPU (горизонтальное масштабирование, webhook-режим) |
| **API (TMA)** | 2× 2–4 vCPU за балансировщиком |
| **Celery workers** | 3–4 воркера по типу очередей (high_priority, default, notifications, maintenance) |
| **PostgreSQL** | 4 vCPU, 8 GB RAM + read-only реплика |
| **Redis** | Кластер из 3 узлов |
| **CDN** | Cloudflare для TMA + изображения событий |
| **Storage** | S3 (Yandex Object Storage / AWS S3) для картинок |

---

## 3. Telegram Mini App: настройка

### BotFather
1. `/newbot` — создать бота (или `/setdomain` для существующего)
2. `/mybots` → выберите бота → **Bot Settings** → **Menu Button** → указать URL TMA
3. В `index.html` фронтенда подключён скрипт Telegram WebApp:
   ```html
   <script src="https://telegram.org/js/telegram-web-app.js"></script>
   ```

### Требования к TMA-ссылке
- **HTTPS обязателен** (кроме localhost)
- Страница должна открываться в течение 5 секунд
- Минимальные размеры: не менее 400×300 px

---

## 4. Alembic миграции

```bash
# Создать новую миграцию
docker compose exec bot alembic revision --autogenerate -m "description"

# Применить миграции
docker compose exec bot alembic upgrade head

# Откатить на одну
docker compose exec bot alembic downgrade -1

# Посмотреть историю
docker compose exec bot alembic history
```

Миграции применяются **автоматически при старте** через скрипт в `Dockerfile`, если настроить `entrypoint`.

---

## 5. CI/CD (GitHub Actions)

Файл: `.github/workflows/ci.yml`

```yaml
# На каждый push/PR:
# 1. Установка Python 3.12 + зависимостей
# 2. Запуск 128 тестов
# 3. Установка Node.js 20 + зависимостей
# 4. TypeScript typecheck
# 5. Vite build
```

**Для деплоя добавить:**
```yaml
deploy:
  needs: [backend, frontend]
  runs-on: ubuntu-latest
  steps:
    - name: Deploy to VPS
      uses: appleboy/ssh-action@v1
      with:
        host: ${{ secrets.VPS_HOST }}
        username: ${{ secrets.VPS_USER }}
        key: ${{ secrets.VPS_SSH_KEY }}
        script: |
          cd /opt/seeker_bot
          git pull origin main
          docker compose down
          docker compose up -d --build
          docker compose exec -T bot alembic upgrade head
```

**Необходимые секреты для деплоя:**
- `VPS_HOST` — IP-адрес сервера
- `VPS_USER` — пользователь SSH
- `VPS_SSH_KEY` — приватный SSH-ключ
- `BOT_TOKEN` — токен бота
- `DATABASE_URL` — строка подключения к БД
- `REDIS_URL` — строка подключения к Redis
- `ADMIN_IDS` — ID администраторов
- `PUBLISHER_CHANNEL_ID` — ID канала
- `SENTRY_DSN` — опционально
- `YANDEX_AFISHA_API_KEY` — опционально

---

## 6. Мониторинг

### Sentry (error tracking)
```python
# В src/config.py раскомментировать sentry_sdk.init()
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    traces_sample_rate=0.1,
    environment="production",
)
```

### Prometheus + Grafana (метрики)
Выводятся на `/metrics` через `prometheus-client`.
Готовые метрики:
- `events_ingested_total` — всего обработано событий
- `users_registered_total` — зарегистрировано пользователей
- `feed_requests_total` — запросов ленты
- `post_published_total` — опубликовано в канал
- `notifications_sent_total` — отправлено уведомлений

### Логирование (structlog)
```bash
# Просмотр логов в реальном времени
docker compose logs -f bot
docker compose logs -f celery-worker
docker compose logs -f api
```

---

## 7. Производительность: узкие места

| Компонент | Узкое место | Решение |
|---|---|---|
| **PostgreSQL** | Запросы персонализированной ленты | Индексы уже созданы, Managed PG при росте |
| **Celery worker** | Парсинг RSS (CPU) | Увеличить `worker_concurrency` |
| **Enricher** | HTTP-запросы к билетным сервисам | Кэширование, таймауты |
| **TMA API** | Количество concurrent-пользователей | Горизонтальное масштабирование |
| **Память** | BeautifulSoup парсинг HTML | Лимиты контейнера, оптимизация селекторов |

---

## 8. Быстрый чек-лист деплоя

- [ ] Куплен VPS (минимум 2 vCPU, 4 GB RAM)
- [ ] Настроен SSH-доступ
- [ ] Установлены Docker + Docker Compose
- [ ] Создан бот через @BotFather
- [ ] Создан Telegram-канал (для публициста)
- [ ] Настроен `.env` с реальными значениями
- [ ] Nginx настроен как reverse proxy (для API + статики TMA)
- [ ] SSL-сертификат (Let's Encrypt / certbot)
- [ ] Выполнены миграции (`alembic upgrade head`)
- [ ] Бот запущен, отвечает на `/start`
- [ ] TMA открывается в Telegram
- [ ] Настроен мониторинг (Sentry, логи)
- [ ] CI проходит успешно
