import redis.asyncio as redis
from fastapi import APIRouter
from sqlalchemy import func, select

from app.core.config import get_settings
from app.database.models.webhook import WebhookDelivery, WebhookDeliveryStatus
from app.database.session import get_session_factory

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/system")
async def system_health() -> dict:
    settings = get_settings()
    checks: dict[str, str] = {}

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await session.execute(select(1))
        checks["database"] = "connected"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    try:
        client = redis.from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
        checks["redis"] = "connected"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            pending = await session.execute(
                select(func.count(WebhookDelivery.id)).where(
                    WebhookDelivery.status == WebhookDeliveryStatus.PENDING.value
                )
            )
            failed = await session.execute(
                select(func.count(WebhookDelivery.id)).where(
                    WebhookDelivery.status == WebhookDeliveryStatus.FAILED.value
                )
            )
        checks["queue"] = "ok"
        delivery_stats = {
            "pending": pending.scalar_one() or 0,
            "failed": failed.scalar_one() or 0,
            "dead_lettered": 0,
        }
    except Exception as exc:
        checks["queue"] = f"error: {exc}"
        delivery_stats = {}

    status = "healthy" if all(v == "connected" or v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status,
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": checks,
        "deliveries": delivery_stats,
    }
