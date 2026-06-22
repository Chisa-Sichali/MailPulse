from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    refresh_token_expires_at,
    verify_password,
)
from app.database.models.user import User
from app.database.repositories import RefreshTokenRepository, UserRepository


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
    ) -> None:
        self._users = user_repo
        self._refresh_tokens = refresh_token_repo

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> tuple[User, str, str]:
        existing = await self._users.get_by_email(email)
        if existing:
            raise ConflictError("A user with this email already exists")

        user = await self._users.create(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
        access_token, refresh_token = await self._issue_tokens(user.id)
        return user, access_token, refresh_token

    async def login(self, *, email: str, password: str) -> tuple[User, str, str]:
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is inactive")

        access_token, refresh_token = await self._issue_tokens(user.id)
        return user, access_token, refresh_token

    async def refresh(self, *, refresh_token: str) -> tuple[User, str, str]:
        token_hash = hash_token(refresh_token)
        stored = await self._refresh_tokens.get_by_hash(token_hash)

        if stored is None or stored.is_revoked:
            raise AuthenticationError("Invalid refresh token")

        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            raise AuthenticationError("Refresh token has expired")

        user = await self._users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Account is inactive")

        await self._refresh_tokens.revoke(stored)
        access_token, new_refresh_token = await self._issue_tokens(user.id)
        return user, access_token, new_refresh_token

    async def logout(self, *, refresh_token: str) -> None:
        token_hash = hash_token(refresh_token)
        stored = await self._refresh_tokens.get_by_hash(token_hash)
        if stored and not stored.is_revoked:
            await self._refresh_tokens.revoke(stored)

    async def logout_all(self, user_id: UUID) -> None:
        await self._refresh_tokens.revoke_all_for_user(user_id)

    async def _issue_tokens(self, user_id: UUID) -> tuple[str, str]:
        access_token = create_access_token(subject=user_id)
        refresh_token = generate_refresh_token()
        await self._refresh_tokens.create(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=refresh_token_expires_at(),
        )
        return access_token, refresh_token
