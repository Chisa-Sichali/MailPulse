from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token
from app.database.models.user import User
from app.database.repositories import (
    EmailEventRepository,
    MailboxRepository,
    RefreshTokenRepository,
    UserRepository,
)
from app.database.session import get_db_session
from app.services.analytics import AnalyticsService
from app.services.auth import AuthService
from app.services.email_processing.event_service import EmailEventService
from app.services.mailbox import MailboxService
from app.services.webhook import WebhookService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session)


async def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


async def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> AuthService:
    return AuthService(user_repo, refresh_token_repo)


async def get_mailbox_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MailboxRepository:
    return MailboxRepository(session)


async def get_mailbox_service(
    mailbox_repo: MailboxRepository = Depends(get_mailbox_repository),
) -> MailboxService:
    return MailboxService(mailbox_repo)


async def get_email_event_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EmailEventRepository:
    return EmailEventRepository(session)


async def get_email_event_service(
    session: AsyncSession = Depends(get_db_session),
) -> EmailEventService:
    return EmailEventService(session)


async def get_webhook_service(
    session: AsyncSession = Depends(get_db_session),
) -> WebhookService:
    return WebhookService(session)


async def get_analytics_service(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsService:
    return AnalyticsService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise AuthenticationError("Invalid or expired access token") from exc

    user = await user_repo.get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")

    return user
