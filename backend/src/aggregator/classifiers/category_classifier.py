"""
Seeker Bot — Category classifier.

Uses keyword matching with pymorphy3 lemmatization for Russian text.
Classifies events into cultural categories (exhibition, theatre, cinema, etc.).
"""

import pymorphy3
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.category import Category
from src.common.logging import logger


class CategoryClassifier:
    """Classifies text into cultural categories using keyword matching."""

    def __init__(self, session: AsyncSession | None):
        self.session = session
        self.categories: list[Category] = []
        self._lemmatizer: pymorphy3.MorphAnalyzer | None = None

    @property
    def lemmatizer(self) -> pymorphy3.MorphAnalyzer:
        if self._lemmatizer is None:
            self._lemmatizer = pymorphy3.MorphAnalyzer(lang="ru")
        return self._lemmatizer

    async def load_categories(self) -> None:
        """Load active categories from the database."""
        if self.session is None:
            logger.warning("category_classifier_no_session")
            return

        stmt = select(Category).where(Category.is_active == True)  # noqa: E712
        result = await self.session.execute(stmt)
        self.categories = list(result.scalars().all())
        logger.debug("categories_loaded", count=len(self.categories))

    def classify(self, title: str, description: str | None = None) -> list[tuple[int, float, str]]:
        """Classify event text into categories.

        Args:
            title: Event title.
            description: Event description (optional).

        Returns:
            List of (category_id, confidence, method) tuples,
            sorted by confidence descending.
        """
        if not self.categories:
            logger.warning("category_classifier_no_categories")
            return []

        text = f"{title} {description or ''}".lower()

        tokens = self._tokenize_and_lemmatize(text)

        scores: dict[int, float] = {}
        for cat in self.categories:
            matches = sum(1 for kw in cat.keywords if kw in tokens)
            if matches > 0:
                # Normalize: matches / max expected keywords
                score = min(1.0, matches / 3.0)
                scores[cat.id] = score

        if not scores:
            return []

        # Sort by confidence descending
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [(cat_id, conf, "keyword") for cat_id, conf in sorted_cats]

    def _tokenize_and_lemmatize(self, text: str) -> str:
        """Tokenize text and return space-joined lemmatized forms."""
        # Simple split by whitespace and punctuation
        import re

        words = re.findall(r"[а-яёa-z]+", text.lower())
        lemmatized = []
        for word in words:
            parsed = self.lemmatizer.parse(word)[0]
            lemmatized.append(parsed.normal_form)

        return " ".join(lemmatized)
