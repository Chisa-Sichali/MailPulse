import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self._analytics = AnalyticsRepository(session)

    async def overview(self, *, user_id: uuid.UUID, days: int = 7):
        return await self._analytics.get_overview(user_id=user_id, days=days)

    async def top_senders(self, *, user_id: uuid.UUID, days: int = 7, limit: int = 10):
        return await self._analytics.get_top_senders(
            user_id=user_id,
            days=days,
            limit=limit,
        )

    async def volume(self, *, user_id: uuid.UUID, days: int = 30):
        return await self._analytics.get_volume(user_id=user_id, days=days)

    async def webhook_performance(self, *, user_id: uuid.UUID, days: int = 7):
        return await self._analytics.get_webhook_performance(user_id=user_id, days=days)

    async def resource_counts(self, *, user_id: uuid.UUID):
        return await self._analytics.count_resources(user_id=user_id)
