from fastapi import APIRouter, Depends, Query

from app.api.deps import get_analytics_service, get_current_user
from app.database.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    ResourceCountsResponse,
    TopSenderItem,
    VolumePoint,
    WebhookPerformanceItem,
)
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
async def analytics_overview(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsOverviewResponse:
    stats = await analytics.overview(user_id=current_user.id, days=days)
    return AnalyticsOverviewResponse(period_days=days, **stats)


@router.get("/top-senders", response_model=list[TopSenderItem])
async def analytics_top_senders(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> list[TopSenderItem]:
    rows = await analytics.top_senders(
        user_id=current_user.id,
        days=days,
        limit=limit,
    )
    return [TopSenderItem(**row) for row in rows]


@router.get("/volume", response_model=list[VolumePoint])
async def analytics_volume(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> list[VolumePoint]:
    rows = await analytics.volume(user_id=current_user.id, days=days)
    return [VolumePoint(**row) for row in rows]


@router.get("/webhooks", response_model=list[WebhookPerformanceItem])
async def analytics_webhooks(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> list[WebhookPerformanceItem]:
    rows = await analytics.webhook_performance(user_id=current_user.id, days=days)
    return [WebhookPerformanceItem(**row) for row in rows]


@router.get("/resources", response_model=ResourceCountsResponse)
async def analytics_resources(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
) -> ResourceCountsResponse:
    counts = await analytics.resource_counts(user_id=current_user.id)
    return ResourceCountsResponse(**counts)
