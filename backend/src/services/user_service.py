"""
Seeker Bot — User service.

Business logic for user management and preferences.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.user import User, UserCityPreference, UserCategoryPreference
from src.common.logging import logger


class UserService:
    """Business logic for user management."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str = "ru",
    ) -> User:
        """Get existing user or create a new one.

        Args:
            telegram_id: Telegram user ID.
            username: Telegram username.
            first_name: User's first name.
            last_name: User's last name.
            language_code: User's language code.

        Returns:
            User instance.
        """
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update user info if changed
            changed = False
            if username and user.username != username:
                user.username = username
                changed = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                changed = True
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                changed = True
            if changed:
                await self.session.flush()
                logger.debug("user_updated", user_id=user.id)
            return user

        # Create new user
        user = User(
            id=telegram_id,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )
        self.session.add(user)
        await self.session.flush()
        logger.info("user_created", user_id=user.id, username=username)
        return user

    async def set_city_preferences(
        self,
        user: User,
        city_ids: list[int],
    ) -> User:
        """Replace user's city preferences.

        Args:
            user: User to update.
            city_ids: New list of city IDs.

        Returns:
            Updated user.
        """
        # Clear existing preferences
        user.city_preferences.clear()
        await self.session.flush()

        # Add new preferences
        for city_id in city_ids:
            pref = UserCityPreference(user_id=user.id, city_id=city_id)
            user.city_preferences.append(pref)

        await self.session.flush()
        logger.debug("city_preferences_updated", user_id=user.id, cities=city_ids)
        return user

    async def set_category_preferences(
        self,
        user: User,
        category_ids: list[int],
    ) -> User:
        """Replace user's category preferences.

        Args:
            user: User to update.
            category_ids: New list of category IDs.

        Returns:
            Updated user.
        """
        user.category_preferences.clear()
        await self.session.flush()

        for cat_id in category_ids:
            pref = UserCategoryPreference(user_id=user.id, category_id=cat_id)
            user.category_preferences.append(pref)

        await self.session.flush()
        logger.debug("category_preferences_updated", user_id=user.id, categories=category_ids)
        return user

    async def get_user_preferences(self, user: User) -> dict:
        """Get user's current preferences.

        Args:
            user: User with loaded city_preferences and category_preferences.

        Returns:
            Dict with city_ids, city_names, category_ids, category_names.
        """
        city_ids = [p.city_id for p in user.city_preferences if p.is_active]
        category_ids = [p.category_id for p in user.category_preferences if p.is_active]

        # Get city names
        city_names = []
        if city_ids:
            from src.db.models.city import City
            stmt = select(City).where(City.id.in_(city_ids))
            result = await self.session.execute(stmt)
            city_names = [c.name_ru for c in result.scalars().all()]

        # Get category names with emojis
        category_names = []
        if category_ids:
            from src.db.models.category import Category
            stmt = select(Category).where(Category.id.in_(category_ids))
            result = await self.session.execute(stmt)
            category_names = [
                f"{c.emoji or '📌'} {c.name_ru}" if c.emoji else c.name_ru
                for c in result.scalars().all()
            ]

        return {
            "city_ids": city_ids,
            "city_names": city_names,
            "category_ids": category_ids,
            "category_names": category_names,
            "notification_frequency": user.notification_frequency.value if hasattr(user.notification_frequency, "value") else user.notification_frequency,
        }
