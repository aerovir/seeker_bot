"""
Seeker Bot — Ticket data models.
"""

from dataclasses import dataclass, field


@dataclass
class TicketInfo:
    """Information about available tickets for an event."""
    url: str
    provider: str
    provider_name: str
    price_min: float | None = None
    price_max: float | None = None
    currency: str = "RUB"
    availability: str = "available"
    section: str | None = None
