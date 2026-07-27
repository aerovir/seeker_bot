"""
Tests for CityClassifier — gazetteer-based city extraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCityClassifier:
    @pytest.mark.asyncio
    async def test_extract_moscow(self):
        """Text mentioning Moscow should be classified as Moscow."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(None)
        await classifier.build_index(_mock_cities())

        result = classifier.extract("Выставка в Москве", None)

        assert len(result) == 1
        assert result[0][0] == 1  # Moscow
        assert result[0][1] >= 0.5

    @pytest.mark.asyncio
    async def test_extract_spb(self):
        """Text mentioning Saint Petersburg should be classified as SPB."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(None)
        await classifier.build_index(_mock_cities())

        result = classifier.extract("Концерт в Санкт-Петербурге", None)

        assert len(result) == 1
        assert result[0][0] == 2  # Saint Petersburg

    @pytest.mark.asyncio
    async def test_extract_multiple_cities(self):
        """Text mentioning multiple cities returns all of them."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(None)
        await classifier.build_index(_mock_cities())

        result = classifier.extract(
            "Гастроли театра: Москва и Казань", None
        )

        assert len(result) == 2
        city_ids = {r[0] for r in result}
        assert 1 in city_ids  # Moscow
        assert 3 in city_ids  # Kazan

    @pytest.mark.asyncio
    async def test_extract_no_city(self):
        """Text with no city mention returns empty list."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(None)
        await classifier.build_index(_mock_cities())

        result = classifier.extract(
            "Онлайн-лекция по истории искусства", None
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_extract_with_default_city(self):
        """Default city is used when no city found in text."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(None)
        await classifier.build_index(_mock_cities())

        result = classifier.extract(
            "Выставка открыта ежедневно", None,
            default_city_id=1
        )

        assert len(result) == 1
        assert result[0][0] == 1  # Moscow (default)
        assert result[0][1] == 0.5  # Lower confidence for default

    @pytest.mark.asyncio
    async def test_extract_aliases(self):
        """City aliases should also match."""
        from src.aggregator.classifiers.city_classifier import CityClassifier

        classifier = CityClassifier(None)
        await classifier.build_index(_mock_cities())

        result = classifier.extract("Событие в Питере", None)

        assert len(result) == 1
        assert result[0][0] == 2  # SPB


def _mock_cities():
    """Create mock cities with morphological forms."""
    from src.db.models.city import City

    return [
        City(
            id=1, slug="moscow", name_ru="Москва", name_en="Moscow",
            name_ru_prepositional="в Москве", name_ru_genitive="Москвы",
            aliases=["msk", "москва"],
            region="Москва",
            is_active=True,
        ),
        City(
            id=2, slug="saint-petersburg", name_ru="Санкт-Петербург", name_en="Saint Petersburg",
            name_ru_prepositional="в Санкт-Петербурге", name_ru_genitive="Санкт-Петербурга",
            aliases=["spb", "питер", "петербург"],
            region="Ленинградская область",
            is_active=True,
        ),
        City(
            id=3, slug="kazan", name_ru="Казань", name_en="Kazan",
            name_ru_prepositional="в Казани", name_ru_genitive="Казани",
            aliases=["казань"],
            region="Татарстан",
            is_active=True,
        ),
    ]
