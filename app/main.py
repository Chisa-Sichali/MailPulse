from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.health.routes import router as health_router
from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware.request_logging import request_logging_middleware
from app.core.queue import close_arq_pool
from app.database.session import dispose_engine, get_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info("Starting %s v%s (%s)", settings.app_name, settings.app_version, settings.environment)
    yield
    await close_arq_pool()
    await dispose_engine()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(request_logging_middleware)

    @app.get("/")
    async def health_check():
        return {"status": "healthy", "service": settings.app_name}

    @app.get("/health/ready")
    async def readiness_check():
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}

    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
