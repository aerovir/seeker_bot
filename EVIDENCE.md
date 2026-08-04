# EVIDENCE — Журнал исследований ошибок

Журнал расследований и диагнозов. Каждая запись: симптом → исследование → корень → фикс/статус.

**Статусы:**
- ✅ **Подтверждено** — корень подтверждён в коде/логах/данных
- ⚠️ **Гипотеза** — подтверждение в коде отсутствует, требует ручного внимания

---

## 2026-08-04 — Остановка публикаций (auto_queue greenlet_spawn)

**Симптом:** публикации остановились 02:35; `auto_queue_events` падает каждые 30 мин.

**Исследование:**
- `auto_queue_events` → `greenlet_spawn has not been called; can't call await_only() here`
- Очередь SCHEDULED = 0 → `publish_scheduled_posts` «успешен», но нечего публиковать
- В `_apply_venue_city` (добавлен вчера) — обращение к `event.cities` (lazy relationship)

**Корень:** ✅ Подтверждено. `get_candidates` загружает только `Event.source` (строка 64, `selectinload(Event.source)`), но не `Event.cities`. `_apply_venue_city` обращался к `event.cities` напрямую → lazy load в async-контексте → greenlet_spawn. Ошибка проявилась не сразу: очередь была заполнена заранее, посты публиковались до 02:35, затем auto_queue не смог пополнить очередь.

**Фикс:** замена города через SQL (`delete` EventCityAssignment + `session.add`) вместо lazy `event.cities`. Коммит `1bcdc7b`.

**Урок:** любые обращения к lazy relationship вне eager-load в async-контексте падают с greenlet_spawn. Проверять при добавлении кода в `auto_queue_candidates`.

---

## 2026-08-03 — Пост без фото («Алекс Лим»)

**Симптом:** пост опубликован без фотографии.

**Исследование:**
- `image_url` в БД есть, фото доступно (HTTP 200)
- `send_photo` для «Алекс Лим» падал: `Bad Request: message caption is too long`
- Полный текст поста = 1135 символов; лимит caption у фото в Telegram = **1024**

**Корень:** ✅ Подтверждено. После увеличения лимита описания до 1500, посты с длинным описанием (>1024) превышали лимит caption фото. `send_photo` падал → молчаливый fallback на `send_message` (без лога) → фото терялось.

**Фикс:** caption фото обрезается до `TG_PHOTO_CAPTION_LIMIT=1024`; fallback логируется (`publish_photo_fallback`).

---

## 2026-08-03 — Полное описание (миграция 003)

**Симптом:** в посте показывалось только 300 символов описания.

**Исследование:**
- `build_channel_message` обрезал `desc_text[:300]`
- Описания источников: медиана ~400–770, максимум до 3013
- `short_description` колонка `String(1024)`

**Корень:** ✅ Подтверждено. Двойная обрезка: `html_to_text` → 1024, пост → 300.

**Фикс:** миграция 003 (`short_description` → `Text`), лимиты → 1500.

---

## 2026-08-03 — Неверный город события («Нижний Новгород»)

**Симптом:** события из Москвы/Екатеринбурга получали город «Нижний Новгород».

**Исследование:**
- Alias «нн» (Нижний Новгород, 2 символа) матчился как подстрока в любом слове: `"нн" in "16 тонн"` → True
- Это давало ложное срабатывание gazetteer → неверный город

**Корень:** ✅ Подтверждено. `CityClassifier` матчил формы ≤2 символа как подстроку.

**Фикс:** исключение форм ≤2 символа из индекса; приоритет города из адреса места (`_apply_venue_city`).

---

## 2026-08-03 — auto_queue: StringDataRightTruncationError

**Симптом:** `auto_queue_events` падал: `value too long for type character varying(1024)`.

**Исследование:** `short_description` заполнялся из HTML-описания без обрезки; описания >1024.

**Корень:** ✅ Подтверждено. `html_to_text` не обрезал до лимита колонки.

**Фикс:** `SHORT_DESC_LIMIT=1024` (позже 1500) в `html_to_text`.

---

## 2026-08-02 — Кнопка «Купить билеты» ведёт на поиск

**Симптом:** кнопка «Купить билеты» ведёт на `afisha.yandex.ru/search?...` (поисковая выдача, не прямая покупка).

**Исследование:**
- afisha.yandex.ru: события рендерятся JS (SPA), статически не парсятся; API требует ключ (400)
- kassir.ru: таймаут с сервера; radario/ponominalu: 403/без ключа
- gorodskoyportal: внешняя ссылка-«Источник» есть у всех, но не всегда билетная (`forsite.ru` — веб-агентство)
- Прямые билетные сайты (everjazz, jazzmap, ticketscloud) работают, но это ниши

**Статус:** ⚠️ **Гипотеза.** Надёжного универсального «найти продажу билетов по названию» без API-ключей не найдено. Требует решения: API-ключи агрегаторов, мульти-адаптер, ссылка на сайт площадки.

---

## 2026-08-02 — Деплой: неверный город (до фикса «нн»)

**Симптом:** события с местом в Москве имели хэштег `#нижний_новгород`.

**Корень:** ✅ Подтверждено (см. выше — ложный матчинг «нн»). Пересчитано 20 событий через `scripts/recalc_event_cities.py`.

---

## 2026-08-02 — Celery async: attached to a different loop

**Симптом:** все асинхронные celery-задачи падали: `attached to a different loop` / `Event loop is closed`.

**Исследование:** prefork-пул (`--concurrency=4`) + `asyncio.run()` в каждой задаче + глобальный SQLAlchemy engine с пулом → соединения asyncpg привязаны к одному loop.

**Корень:** ✅ Подтверждено.

**Фикс:** отдельный NullPool-engine для celery (`celery_session_factory`) + `--pool=solo`.

---

## 2026-08-02 — Celery worker KeyError (задачи не зарегистрированы)

**Симптом:** `KeyError: 'celery_app.tasks.publisher.publish_scheduled_posts'`.

**Корень:** ✅ Подтверждено. Модули задач не импортировались при старте worker (`autodiscover` не сработал — пустой пакет tasks/).

**Фикс:** импорт всех `celery_app.tasks.*` в `celery_app/__init__.py`.

---

## 2026-08-02 — CI: ModuleNotFoundError aiosqlite

**Симптом:** CI падал: `No module named 'aiosqlite'` (12 integration тестов).

**Корень:** ✅ Подтверждено. `aiosqlite` не был в `requirements.txt` (локально был как осиротевший пакет).

**Фикс:** добавлен в `requirements.txt`.

---

## 2026-08-02 — Публикация: greenlet_spawn (lazy city/category)

**Симптом:** `publish_post` падал: `greenlet_spawn has not been called`.

**Корень:** ✅ Подтверждено. Ленивая загрузка `assignment.city/category` в async-контексте.

**Фикс:** вложенные `selectinload` в celery-задаче и admin-хендлерах.

---

## 2026-08-02 — Inline-кнопка с относительной ссылкой

**Симптом:** `inline keyboard button URL '/rostov/...' is invalid: URL host is empty`.

**Корень:** ✅ Подтверждено. gorodskoyportal отдаёт относительные ссылки.

**Фикс:** RSS-парсер склеивает относительный `link` с доменом источника.
