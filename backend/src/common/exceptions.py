"""
Seeker Bot — Domain exceptions.
"""


class SeekerBotError(Exception):
    """Base exception for all Seeker Bot errors."""
    pass


class SourceError(SeekerBotError):
    """Error related to content source fetching or parsing."""
    pass


class FetchError(SourceError):
    """Failed to fetch data from a source."""
    pass


class ParseError(SourceError):
    """Failed to parse source data."""
    pass


class ClassificationError(SeekerBotError):
    """Error during content classification."""
    pass


class TicketError(SeekerBotError):
    """Error during ticket information retrieval."""
    pass


class UserNotFoundError(SeekerBotError):
    """User not found in database."""
    pass


class EventNotFoundError(SeekerBotError):
    """Event not found in database."""
    pass
