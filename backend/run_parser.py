#!/usr/bin/env python3
"""
Seeker Bot — Run Parser.

Однократный запуск парсера по всем или выбранным источникам.
Не требует Celery — запускает пайплайн напрямую.

Использование:
    python run_parser.py                        # все активные источники
    python run_parser.py --source moscow-museums # конкретный источник
    python run_parser.py --limit 5              # первые 5 источников
    python run_parser.py --dry-run              # без сохранения в БД
    python run_parser.py --stats                # показать статистику и выйти
"""

import argparse
import sys
import asyncio
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.common.logging import logger
from src.db.session import async_session_factory
from src.db.models.source import ContentSource, SourceStatus
from src.aggregator.pipeline import AggregationPipeline
from sqlalchemy import select, func


async def show_stats(session):
    """Показать статистику по источникам и событиям."""
    from src.db.models.event import Event

    total_sources = await session.scalar(select(func.count(ContentSource.id)))
    active_sources = await session.scalar(
        select(func.count(ContentSource.id)).where(ContentSource.status == SourceStatus.ACTIVE)
    )
    total_events = await session.scalar(select(func.count(Event.id)))
    published_events = await session.scalar(
        select(func.count(Event.id)).where(Event.status == "published")
    )

    print(f"\n📊 Статистика:")
    print(f"  📡 Источников:      {total_sources or 0} (активно: {active_sources or 0})")
    print(f"  📰 Событий всего:    {total_events or 0} (опубликовано: {published_events or 0})")
    print()

    result = await session.execute(
        select(ContentSource).where(ContentSource.status == SourceStatus.ACTIVE).order_by(ContentSource.priority.desc())
    )
    sources = result.scalars().all()

    if sources:
        print(f"  {'Источник':<30} {'Приоритет':<10} {'Последний':<20} {'Ошибки':<8}")
        print(f"  {'─'*30} {'─'*10} {'─'*20} {'─'*8}")
        for s in sources:
            last = s.last_fetched_at.strftime("%d.%m %H:%M") if s.last_fetched_at else "никогда"
            errors = str(s.consecutive_errors) if s.consecutive_errors > 0 else "—"
            print(f"  {s.name:<30} {s.priority:<10} {last:<20} {errors:<8}")


async def run_source(session, source, dry_run: bool = False) -> dict:
    """Запустить пайплайн для одного источника."""
    logger.info("parsing_source", slug=source.slug, name=source.name)

    pipeline = AggregationPipeline(session, source)
    start = time.time()
    result = await pipeline.execute()
    elapsed = time.time() - start

    if result.skipped:
        logger.info("pipeline_skipped", source=source.slug, reason=result.reason)
        return {"slug": source.slug, "skipped": True, "reason": result.reason, "elapsed": elapsed}

    if result.error:
        logger.error("pipeline_error", source=source.slug, error=str(result.error))
        return {"slug": source.slug, "error": str(result.error), "elapsed": elapsed}

    if dry_run:
        await session.rollback()
        logger.info("pipeline_dry_run (rolled back)", source=source.slug, events=len(result.created))
    else:
        await session.commit()

    return {
        "slug": source.slug,
        "events": len(result.created),
        "elapsed": round(elapsed, 2),
        "dry_run": dry_run,
    }


async def main():
    parser = argparse.ArgumentParser(description="Seeker Bot — Run Parser")
    parser.add_argument("--source", "-s", type=str, help="Slug источника (опция: все активные)")
    parser.add_argument("--limit", "-l", type=int, default=0, help="Ограничить количество источников")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Без сохранения (сухой прогон)")
    parser.add_argument("--stats", "-st", action="store_true", help="Показать статистику и выйти")
    args = parser.parse_args()

    async with async_session_factory() as session:
        if args.stats:
            await show_stats(session)
            return

        if args.source:
            result = await session.execute(
                select(ContentSource).where(ContentSource.slug == args.source)
            )
            sources = [result.scalar_one_or_none()]
            if not sources[0]:
                logger.error("source_not_found", slug=args.source)
                return
        else:
            query = (
                select(ContentSource)
                .where(ContentSource.status == SourceStatus.ACTIVE)
                .order_by(ContentSource.priority.desc())
            )
            if args.limit:
                query = query.limit(args.limit)
            result = await session.execute(query)
            sources = list(result.scalars().all())

        if not sources:
            logger.info("no_sources_to_parse")
            return

        logger.info("parse_start", count=len(sources), dry_run=args.dry_run)

        results = []
        total_events = 0
        total_errors = 0

        for source in sources:
            if source is None:
                continue
            res = await run_source(session, source, dry_run=args.dry_run)
            results.append(res)
            if "events" in res:
                total_events += res["events"]
            if "error" in res:
                total_errors += 1

        # Итог
        print(f"\n{'='*50}")
        print(f"📋 РЕЗУЛЬТАТЫ ПАРСИНГА")
        print(f"{'='*50}")
        print(f"  {'Источник':<30} {'Событий':<10} {'Время':<10}")
        print(f"  {'─'*30} {'─'*10} {'─'*10}")
        for r in results:
            name = r["slug"]
            if "events" in r:
                print(f"  {name:<30} {r['events']:<10} {r['elapsed']}с")
            elif "error" in r:
                print(f"  {name:<30} {'❌':<10} {r['elapsed']}с")
            elif r.get("skipped"):
                print(f"  {name:<30} {'⏭':<10} {r['elapsed']}с")
        print(f"  {'─'*50}")
        print(f"  {'ИТОГО':<30} {total_events:<10} (ошибок: {total_errors})")
        print()

        if args.dry_run:
            print("⚠️  Dry-run: изменения откачены.\n")


if __name__ == "__main__":
    asyncio.run(main())
