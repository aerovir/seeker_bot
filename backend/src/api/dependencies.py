"""
Seeker Bot — FastAPI dependencies.

Shared dependencies for TMA API endpoints.
"""

from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.api.auth import verify_init_data, get_user_from_init_data
from src.services.user_service import UserService
from src.common.logging import logger


async def get_current_user(
    authorization: str | None = Header(None),
    session: AsyncSession = Depends(get_session),
):
    """Dependency to get authenticated user from TMA initData.

    Expects Authorization header: "tma {init_data}"

    Args:
        authorization: Authorization header value.
        session: Database session.

    Returns:
        User DB model instance.

    Raises:
        HTTPException: 401 if auth is invalid.
    """
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header. Use: Authorization: tma {init_data}",
        )

    init_data = authorization[4:]  # Remove "tma " prefix

    from src.config import settings

    if not verify_init_data(init_data, settings.bot_token):
        logger.warning("tma_auth_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid initData signature",
        )

    user_data = get_user_from_init_data(init_data)
    if not user_data or not user_data.get("telegram_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not extract user from initData",
        )

    user_service = UserService(session)
    user = await user_service.get_or_create(**user_data)

    return user
