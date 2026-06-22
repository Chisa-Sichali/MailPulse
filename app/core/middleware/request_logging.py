import secrets
import time

from fastapi import Request

from app.core.logging import get_logger

logger = get_logger(__name__)


async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID", "-")

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_id=%s method=%s path=%s error duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - start) * 1000
    client_host = request.client.host if request.client else "-"
    logger.info(
        "request_id=%s client=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        client_host,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    response.headers.setdefault("X-Request-ID", request_id)
    return response
