"""
Seeker Bot — User preferences API endpoints (authenticated).

Requires Telegram WebApp initData for authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.db.models.user import User
from src.api.schemas import PreferencesUpdate, PreferencesOut
from src.api.dependencies import get_current_user
from src.services.user_service import UserService
from src.common.logging import logger

router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])


@router.get("/", response_model=PreferencesOut)
async def get_preferences(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Get current user preferences."""
    user_service = UserService(session)
    prefs = await user_service.get_user_preferences(user)
    return PreferencesOut(**prefs)


@router.put("/", response_model=PreferencesOut)
async def update_preferences(
    prefs: PreferencesUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update user preferences (cities and categories)."""
    user_service = UserService(session)

    # Update city preferences
    user = await user_service.set_city_preferences(user, prefs.city_ids)

    # Update category preferences
    user = await user_service.set_category_preferences(user, prefs.category_ids)

    await session.commit()

    logger.info(
        "preferences_updated",
        user_id=user.id,
        cities=prefs.city_ids,
        categories=prefs.category_ids,
    )

    result = await user_service.get_user_preferences(user)
    return PreferencesOut(**result)


@router.get("/cities", response_model=list[int])
async def get_city_preferences(
    user: User = Depends(get_current_user),
):
    """Get user's selected city IDs."""
    return [p.city_id for p in user.city_preferences if p.is_active]


@router.get("/categories", response_model=list[int])
async def get_category_preferences(
    user: User = Depends(get_current_user),
):
    """Get user's selected category IDs."""
    return [p.category_id for p in user.category_preferences if p.is_active]
