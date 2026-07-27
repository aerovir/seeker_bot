"""
Tests for CategoryClassifier — keyword matching with pymorphy3.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCategoryClassifier:
    @pytest.mark.asyncio
    async def test_classify_exhibition_keywords(self):
        """Text about exhibitions should be classified as such."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(mock_session())
        classifier.categories = _mock_categories()

        result = classifier.classify(
            "Открылась новая выставка в галерее",
            "На выставке представлены картины известных художников"
        )

        assert len(result) > 0
        best = result[0]
        # Should be exhibitions or museums (both have "выставк" keyword)
        assert best[0] in [1, 4]  # exhibitions or museums
        assert best[1] >= 0.5

    @pytest.mark.asyncio
    async def test_classify_theatre(self):
        """Text about theatre should be classified as theatre."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(mock_session())
        classifier.categories = _mock_categories()

        result = classifier.classify(
            "Премьера спектакля в Большом театре",
            "Новая постановка режиссёра"
        )

        assert len(result) > 0
        best = result[0]
        assert best[0] == 2  # theatre

    @pytest.mark.asyncio
    async def test_classify_cinema(self):
        """Text about cinema should be classified as cinema."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(mock_session())
        classifier.categories = _mock_categories()

        result = classifier.classify(
            "Премьера нового фильма",
            "Документальное кино о природе"
        )

        assert len(result) > 0
        best = result[0]
        assert best[0] == 3  # cinema

    @pytest.mark.asyncio
    async def test_classify_no_match(self):
        """Text with no keywords should return empty list."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(mock_session())
        classifier.categories = _mock_categories()

        result = classifier.classify(
            "Новости дня",
            "Прогноз погоды на завтра"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_load_categories_from_db(self):
        """Categories are loaded from DB."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier
        from src.common.constants import SourceType

        mock_db = mock_session()

        classifier = CategoryClassifier(mock_db)
        await classifier.load_categories()

        assert len(classifier.categories) > 0

    @pytest.mark.asyncio
    async def test_classify_concerts(self):
        """Text about concerts should be classified as concerts."""
        from src.aggregator.classifiers.category_classifier import CategoryClassifier

        classifier = CategoryClassifier(mock_session())
        classifier.categories = _mock_categories()

        result = classifier.classify(
            "Концерт симфонического оркестра",
            "Классическая музыка в исполнении"
        )

        assert len(result) > 0
        assert result[0][0] == 5  # concerts


def mock_session():
    """Create a mock session with pre-loaded categories."""
    mock = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = _mock_categories()
    mock.execute = AsyncMock(return_value=mock_result)
    return mock


def _mock_categories():
    """Create mock categories with keywords."""
    from src.db.models.category import Category

    return [
        Category(
            id=1, slug="exhibitions", name_ru="Выставки", name_en="Exhibitions",
            keywords=["выставк", "экспозици", "вернисаж", "галерея", "художник", "картин"],
            is_active=True,
        ),
        Category(
            id=2, slug="theatre", name_ru="Театр", name_en="Theatre",
            keywords=["спектакл", "театр", "пьес", "постановк", "премьер", "балет"],
            is_active=True,
        ),
        Category(
            id=3, slug="cinema", name_ru="Кино", name_en="Cinema",
            keywords=["фильм", "кинопремьер", "кинотеатр", "документальн", "анимаци"],
            is_active=True,
        ),
        Category(
            id=4, slug="museums", name_ru="Музеи", name_en="Museums",
            keywords=["музей", "экспонат", "экскурси", "выставк"],
            is_active=True,
        ),
        Category(
            id=5, slug="concerts", name_ru="Концерты", name_en="Concerts",
            keywords=["концерт", "симфони", "оркестр", "джаз", "классическ"],
            is_active=True,
        ),
        Category(
            id=6, slug="festivals", name_ru="Фестивали", name_en="Festivals",
            keywords=["фестивал", "форум", "биеннале", "праздник"],
            is_active=True,
        ),
        Category(
            id=7, slug="lectures", name_ru="Лекции", name_en="Lectures",
            keywords=["лекци", "семинар", "мастер-класс", "дискусси", "встреч"],
            is_active=True,
        ),
    ]
