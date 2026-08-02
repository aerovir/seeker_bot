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
# 2. Запуск тестов (pytest)
# 3. Установка Node.js 20 + зависимостей
# 4. TypeScript typecheck
# 5. Vite build
# 6. Деплой на VPS (только push в main, self-hosted runner)
```

### Авто-деплой через self-hosted runner

Воркфлоу содержит job `deploy`, который срабатывает **только на push в `main`**
(после зелёного CI, `needs: [backend, frontend]`) и выполняется **прямо на
сервере** через self-hosted GitHub Actions runner (`runs-on: self-hosted`).

**Почему без SSH:** runner установлен на целевом VPS и привязан к репозиторию
(`Settings → Actions → Runners`). Job выполняется локально на сервере, поэтому
SSH-ключи для деплоя не нужны.

**Что делает deploy job:**
1. `rsync` кода в `/opt/seeker_bot` (без `.git`, `node_modules`, `.venv`)
2. Генерирует `.env` из GitHub secrets (см. ниже)
3. `docker compose -f docker-compose.prod.yml up -d --build`
4. `alembic upgrade head` (миграции)
5. `python seed.py` (каталоги городов/категорий/источников)
6. Healthcheck API (`/health`) + отчёт о контейнерах

**Необходимые секреты (Settings → Secrets and variables → Actions):**
- `BOT_TOKEN` — токен бота
- `ADMIN_IDS` — ID администраторов (один ID или JSON-массив `[1,2]`; нормализуется в workflow)
- `PUBLISHER_CHANNEL_ID` — ID канала для публикаций
- `POSTGRES_PASSWORD` — пароль PostgreSQL (используется и в `.env`, и в БД-URL)
- `SENTRY_DSN` — опционально

> `DATABASE_URL` и `REDIS_URL` собираются в workflow из `POSTGRES_PASSWORD` —
> задавать их секретами не нужно.

**Настройка runner на сервере (однократно):**
```bash
# Зарегистрировать runner для репозитория:
#   GitHub → Settings → Actions → Runners → New self-hosted runner
#   (по инструкции: ./config.sh --url https://github.com/aerovir/seeker_bot --token <REG_TOKEN>)
./run.sh
# Желательно установить как systemd-сервис:
./svc.sh install
sudo systemctl enable --now actions.runner.aerovir-seeker_bot.*
```

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
# Просмотр логов Docker
docker compose logs -f bot
docker compose logs -f celery-worker
docker compose logs -f api

# Чтение файлового лога (на хосте)
tail -50 /var/log/seeker_bot/seeker_bot.log

# Фильтр по уровню
grep ERROR /var/log/seeker_bot/seeker_bot.log | tail -20

# Следить в реальном времени
tail -f /var/log/seeker_bot/seeker_bot.log
```

### SSH-доступ к логам

```bash
# Через ~/.ssh/config:
#   Host seeker-bot
#       HostName <IP>
#       User <username>
#       IdentityFile ~/.ssh/seeker_bot_deploy

# Tail лога
ssh seeker-bot "tail -50 /var/log/seeker_bot/seeker_bot.log"

# Docker логи
ssh seeker-bot "cd /opt/seeker_bot && docker compose logs --tail=50 bot"

# Статус
ssh seeker-bot "cd /opt/seeker_bot && docker compose ps"

# Скрипт-помощник
./scripts/logs.sh -s      # статистика
./scripts/logs.sh -d      # markdown-отчёт
./scripts/logs.sh -c bot  # логи Docker-контейнера
```

### Настройка сервера (однократно)

```bash
scp scripts/setup-server.sh user@host:/tmp/
ssh user@host "bash /tmp/setup-server.sh"
```

Скрипт `setup-server.sh`:
- Устанавливает Docker, Nginx, certbot, logrotate
- Создаёт `/opt/seeker_bot` и `/var/log/seeker_bot`
- Настраивает logrotate (ежедневная ротация, 14 дней хранения)
- Создаёт пользователя `deploy` в группе `docker`
- Добавляет alias'ы для удобного просмотра логов

### Инфраструктура логов

| Ресурс | Путь |
|--------|------|
| Файл лога (в контейнере) | `/var/log/seeker_bot/seeker_bot.log` |
| Файл лога (на хосте) | Docker volume `seeker_bot_logs` |
| Ротация | `/etc/logrotate.d/seeker_bot` (ежедневно, 14 дней) |
| Размер буфера | 10 MB на файл, 5 backup'ов |
| Переменная | `LOG_DIR` (по умолчанию `/var/log/seeker_bot`)

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
- [ ] Установлены Docker + Docker Compose
- [ ] Создан бот через @BotFather
- [ ] Создан Telegram-канал (для публициста)
- [ ] Зарегистрирован self-hosted runner для репозитория (Settings → Actions → Runners)
- [ ] Runner установлен как systemd-сервис (переживает перезагрузку)
- [ ] В GitHub Secrets заданы: `BOT_TOKEN`, `ADMIN_IDS`, `PUBLISHER_CHANNEL_ID`, `POSTGRES_PASSWORD`
- [ ] Пуш в `main` → CI зелёный → deploy job поднимает контейнеры
- [ ] API отвечает на `/health`
- [ ] Бот запущен, отвечает на `/start`
- [ ] Nginx настроен как reverse proxy (для API + статики TMA) — **обязательно для TMA, нужен HTTPS**
- [ ] SSL-сертификат (Let's Encrypt / certbot)
- [ ] TMA открывается в Telegram
- [ ] Настроен мониторинг (Sentry, логи)
- [ ] CI проходит успешно
