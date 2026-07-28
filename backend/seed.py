#!/usr/bin/env python3
"""
Seeker Bot — Seed script.

Загружает начальные данные из YAML в БД: города, категории, источники.

Использование:
    python seed.py                          # загрузить всё
    python seed.py --sources-only           # только источники
    python seed.py --data-only              # только города + категории
    python seed.py --clear                  # очистить и перезалить
"""

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))

from src.common.logging import logger
from src.common.constants import SourceType
from src.db.session import async_session_factory
from src.db.models.city import City
from src.db.models.category import Category
from src.db.models.source import ContentSource, SourceDefaultCategory
from sqlalchemy import select, text

DATA_DIR = Path(__file__).parent / "data"


async def load_cities(session, clear: bool = False):
    path = DATA_DIR / "cities.yml"
    if not path.exists():
        logger.warning("cities.yml не найден", path=str(path))
        return 0

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "cities" not in data:
        logger.warning("cities.yml пуст")
        return 0

    if clear:
        await session.execute(text("DELETE FROM user_city_preferences"))
        await session.execute(text("DELETE FROM event_city_assignments"))
        await session.execute(text("DELETE FROM cities"))
        logger.info("cities очищены")

    count = 0
    for item in data["cities"]:
        existing = await session.execute(select(City).where(City.slug == item["slug"]))
        if existing.scalar_one_or_none():
            continue

        city = City(
            id=item.get("id", count + 1),
            slug=item["slug"],
            name_ru=item["name_ru"],
            name_en=item.get("name_en", ""),
            name_ru_prepositional=item.get("name_ru_prepositional", ""),
            name_ru_genitive=item.get("name_ru_genitive", ""),
            region=item.get("region", ""),
            country=item.get("country", "Россия"),
            timezone=item.get("timezone", "Europe/Moscow"),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            aliases=item.get("aliases", []),
            sort_order=item.get("sort_order", 0),
            is_active=item.get("is_active", True),
        )
        session.add(city)
        count += 1

    await session.flush()
    logger.info("cities загружены", count=count)
    return count


async def load_categories(session, clear: bool = False):
    path = DATA_DIR / "categories.yml"
    if not path.exists():
        logger.warning("categories.yml не найден", path=str(path))
        return 0

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "categories" not in data:
        logger.warning("categories.yml пуст")
        return 0

    if clear:
        await session.execute(text("DELETE FROM source_default_categories"))
        await session.execute(text("DELETE FROM event_category_assignments"))
        await session.execute(text("DELETE FROM user_category_preferences"))
        await session.execute(text("DELETE FROM categories"))
        logger.info("categories очищены")

    count = 0
    for item in data["categories"]:
        existing = await session.execute(select(Category).where(Category.slug == item["slug"]))
        if existing.scalar_one_or_none():
            continue

        cat = Category(
            id=item.get("id", count + 1),
            slug=item["slug"],
            name_ru=item["name_ru"],
            name_en=item.get("name_en", ""),
            emoji=item.get("emoji"),
            description=item.get("description"),
            keywords=item.get("keywords", []),
            parent_id=item.get("parent_id"),
            sort_order=item.get("sort_order", 0),
            is_active=item.get("is_active", True),
        )
        session.add(cat)
        count += 1

    await session.flush()
    logger.info("categories загружены", count=count)
    return count


async def load_sources(session, clear: bool = False):
    path = DATA_DIR / "sources.yml"
    if not path.exists():
        logger.warning("sources.yml не найден", path=str(path))
        return 0

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "sources" not in data:
        logger.warning("sources.yml пуст")
        return 0

    if clear:
        await session.execute(text("DELETE FROM source_default_categories"))
        await session.execute(text("DELETE FROM source_items"))
        await session.execute(text("DELETE FROM content_sources"))
        logger.info("sources очищены")

    result = await session.execute(select(City))
    cities = {c.slug: c.id for c in result.scalars().all()}

    result = await session.execute(select(Category))
    categories = {c.slug: c.id for c in result.scalars().all()}

    count = 0
    for item in data["sources"]:
        existing = await session.execute(select(ContentSource).where(ContentSource.slug == item["slug"]))
        if existing.scalar_one_or_none():
            logger.debug("source already exists", slug=item["slug"])
            continue

        src = ContentSource(
            name=item["name"],
            slug=item["slug"],
            source_type=SourceType(item["source_type"]),
            feed_url=item["feed_url"],
            fetch_interval_minutes=item.get("fetch_interval_minutes", 30),
            timeout_seconds=item.get("timeout_seconds", 30),
            retry_count=item.get("retry_count", 3),
            priority=item.get("priority", 0),
            default_city_id=cities.get(item.get("default_city_slug", "")),
            config=item.get("config", {}),
        )
        session.add(src)
        await session.flush()

        for cat_slug in item.get("default_category_slugs", []):
            cat_id = categories.get(cat_slug)
            if cat_id:
                session.add(SourceDefaultCategory(source_id=src.id, category_id=cat_id))

        count += 1

    logger.info("sources загружены", count=count)
    return count


async def main():
    parser = argparse.ArgumentParser(description="Seeder для Seeker Bot")
    parser.add_argument("--sources-only", action="store_true", help="Только источники")
    parser.add_argument("--data-only", action="store_true", help="Только города + категории")
    parser.add_argument("--clear", action="store_true", help="Очистить перед загрузкой")
    args = parser.parse_args()

    async with async_session_factory() as session:
        if args.data_only:
            await load_cities(session, clear=args.clear)
            await load_categories(session, clear=args.clear)
        elif args.sources_only:
            await load_sources(session, clear=args.clear)
        else:
            await load_cities(session, clear=args.clear)
            await load_categories(session, clear=args.clear)
            await load_sources(session, clear=args.clear)
        await session.commit()

    logger.info("seed complete")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
