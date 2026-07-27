"""
Seeker Bot — City classifier.

Uses a gazetteer approach with morphological forms to extract
city mentions from Russian text.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.city import City
from src.common.logging import logger


class CityClassifier:
    """Extracts city mentions from event text using gazetteer matching."""

    def __init__(self, session: AsyncSession | None):
        self.session = session
        # Maps normalized form -> city_id
        self.city_forms: dict[str, int] = {}
        self.cities: list[City] = []

    async def build_index(self, cities: list[City] | None = None) -> None:
        """Build the gazetteer index from cities.

        Args:
            cities: Optional pre-loaded list of cities.
                    If None, loads from DB.
        """
        if cities is not None:
            self.cities = cities
        elif self.session is not None:
            stmt = select(City).where(City.is_active == True)  # noqa: E712
            result = await self.session.execute(stmt)
            self.cities = list(result.scalars().all())
        else:
            logger.warning("city_classifier_no_data")
            return

        self.city_forms = {}
        for city in self.cities:
            # Index all morphological forms and aliases
            for form in [
                city.name_ru,
                city.name_ru_prepositional,
                city.name_ru_genitive,
                *city.aliases,
            ]:
                if form and form.strip():
                    self.city_forms[form.lower().strip()] = city.id

        logger.debug(
            "city_index_built",
            cities=len(self.cities),
            forms=len(self.city_forms),
        )

    def extract(
        self,
        title: str,
        description: str | None,
        default_city_id: int | None = None,
    ) -> list[tuple[int, float, str]]:
        """Extract city mentions from event text.

        Args:
            title: Event title.
            description: Event description (optional).
            default_city_id: Optional fallback city if none found.

        Returns:
            List of (city_id, confidence, method) tuples.
        """
        if not self.city_forms:
            logger.warning("city_classifier_no_index")
            if default_city_id:
                return [(default_city_id, 0.5, "source_default")]
            return []

        text = f"{title} {description or ''}".lower()

        found: dict[int, float] = {}
        for form, city_id in self.city_forms.items():
            if form in text:
                # Confidence based on match type
                if form.startswith("в "):
                    confidence = 1.0  # prepositional form is strong signal
                else:
                    confidence = 0.9
                found[city_id] = max(found.get(city_id, 0), confidence)

        if not found and default_city_id:
            return [(default_city_id, 0.5, "source_default")]

        return [(cid, conf, "gazetteer") for cid, conf in sorted(found.items())]
