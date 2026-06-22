from fastapi import APIRouter

from app.api.v1.analytics.routes import router as analytics_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.events.routes import router as events_router
from app.api.v1.mailboxes.routes import router as mailboxes_router
from app.api.v1.webhooks.routes import router as webhooks_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(mailboxes_router)
router.include_router(webhooks_router)
router.include_router(events_router)
router.include_router(analytics_router)
