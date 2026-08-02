#!/usr/bin/env python3
"""
Seeker Bot — Recalc event cities from venue_address.

Пересчитывает города событий по адресу места проведения (приоритет места
над классификатором). Исправляет массовую ошибку: события из Москвы/других
городов получали «Нижний Новгород» из-за ложного матчинга alias «нн».

Использование:
    python scripts/recalc_event_cities.py          # все события с адресом
    python scripts/recalc_event_cities.py --limit  # только первые N
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from src.db.session import async_session_factory
from src.db.models.city import City
from src.db.models.event import Event, EventCityAssignment
from src.common.logging import logger


async def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Recalc event cities from address")
    parser.add_argument("--limit", "-l", type=int, default=None)
    args = parser.parse_args()

    async with async_session_factory() as session:
        # Все города для сопоставления
        cities = list((await session.execute(select(City))).scalars().all())
        city_by_name = {c.name_ru.lower(): c for c in cities}

        # Все события, ожидающие публикации (будущие)
        stmt = select(Event).where(
            Event.status == "published",
        ).options(selectinload(Event.source))
        if args.limit:
            stmt = stmt.limit(args.limit)
        events = list((await session.execute(stmt)).scalars().all())

        # Классификатор для событий без адреса (пересчитать город из текста)
        from src.aggregator.classifiers.city_classifier import CityClassifier
        clf = CityClassifier(session)
        await clf.build_index(cities)

        updated = 0
        for event in events:
            # 1. Приоритет: город из адреса места
            city = None
            method = "venue_address"
            if event.venue_address:
                parts = [p.strip() for p in event.venue_address.split(",")]
                candidate = parts[-1].strip() if parts else ""
                candidate = candidate.replace("г ", "").replace("г. ", "").strip()
                if candidate and len(candidate) >= 3:
                    city = city_by_name.get(candidate.lower())

            # 2. Иначе — классификатор (с default_city источника)
            if not city and event.source:
                classified = clf.extract(
                    event.title, event.description,
                    default_city_id=event.source.default_city_id,
                )
                if classified:
                    city = next(
                        (c for c in cities if c.id == classified[0][0]), None
                    )
                    method = classified[0][2]

            if not city:
                continue

            # Удалить старые назначения города, поставить верный
            await session.execute(
                delete(EventCityAssignment).where(
                    EventCityAssignment.event_id == event.id
                )
            )
            session.add(EventCityAssignment(
                event_id=event.id,
                city_id=city.id,
                confidence=1.0,
                method=method,
            ))
            updated += 1

        await session.commit()
        print(f"✅ Пересчитано городов: {updated} из {len(events)} PUBLISHED событий")


if __name__ == "__main__":
    asyncio.run(main())
