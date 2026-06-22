from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions.base import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    MailPulseError,
    NotFoundError,
    ValidationError,
)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code=exc.code,
            message=exc.message,
        )

    @app.exception_handler(ConflictError)
    async def conflict_handler(_: Request, exc: ConflictError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_409_CONFLICT,
            code=exc.code,
            message=exc.message,
        )

    @app.exception_handler(AuthenticationError)
    async def auth_handler(_: Request, exc: AuthenticationError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=exc.code,
            message=exc.message,
        )

    @app.exception_handler(AuthorizationError)
    async def authorization_handler(
        _: Request,
        exc: AuthorizationError,
    ) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code=exc.code,
            message=exc.message,
        )

    @app.exception_handler(ValidationError)
    async def validation_handler(_: Request, exc: ValidationError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code=exc.code,
            message=exc.message,
        )

    @app.exception_handler(MailPulseError)
    async def mailpulse_handler(_: Request, exc: MailPulseError) -> JSONResponse:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code=exc.code,
            message=exc.message,
        )
