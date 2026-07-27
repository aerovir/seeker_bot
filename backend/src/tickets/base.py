"""
Seeker Bot — Abstract base ticket adapter.

All ticket providers must implement search() and get_event_url().
"""

from abc import ABC, abstractmethod
from datetime import datetime


class BaseTicketAdapter(ABC):
    """Abstract adapter for ticket sales platforms."""

    @abstractmethod
    async def search(
        self,
        event_title: str,
        venue: str | None,
        date: datetime | None,
    ) -> list:
        """Search for tickets matching the event.

        Args:
            event_title: Title of the event to search for.
            venue: Venue name (optional, improves accuracy).
            date: Event date (optional).

        Returns:
            List of TicketInfo objects. Empty list if no tickets found.

        Raises:
            TicketError: On unrecoverable errors (logged, not propagated).
        """
        ...

    @abstractmethod
    async def get_event_url(
        self,
        event_title: str,
        venue: str | None,
    ) -> str | None:
        """Get a direct URL to the event's ticket page.

        Args:
            event_title: Title of the event.
            venue: Venue name (optional).

        Returns:
            URL string, or None if not available.
        """
        ...
