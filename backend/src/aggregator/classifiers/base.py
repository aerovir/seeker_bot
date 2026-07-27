"""
Seeker Bot — Abstract base classifier.
"""

from abc import ABC, abstractmethod


class BaseClassifier(ABC):
    """Abstract base for all classifiers."""

    @abstractmethod
    async def load_data(self) -> None:
        """Load reference data (categories, cities, etc.)."""
        ...

    @abstractmethod
    def classify(self, *args, **kwargs) -> list[tuple[int, float, str]]:
        """Classify input and return (id, confidence, method) tuples."""
        ...
