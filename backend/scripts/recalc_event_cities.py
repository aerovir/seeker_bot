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

        # События с адресом
        stmt = select(Event).where(
            Event.venue_address.isnot(None),
            Event.venue_address != "",
        )
        if args.limit:
            stmt = stmt.limit(args.limit)
        events = list((await session.execute(stmt)).scalars().all())

        updated = 0
        for event in events:
            parts = [p.strip() for p in event.venue_address.split(",")]
            candidate = parts[-1].strip() if parts else ""
            candidate = candidate.replace("г ", "").replace("г. ", "").strip()
            if not candidate or len(candidate) < 3:
                continue

            city = city_by_name.get(candidate.lower())
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
                method="venue_address",
            ))
            updated += 1

        await session.commit()
        print(f"✅ Пересчитано городов: {updated} из {len(events)} событий с адресом")


if __name__ == "__main__":
    asyncio.run(main())
