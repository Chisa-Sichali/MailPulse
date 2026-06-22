from fastapi import APIRouter, Depends, status

from app.api.deps import get_auth_service, get_current_user
from app.database.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_response(
    *,
    access_token: str,
    refresh_token: str,
) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    _, access_token, refresh_token = await auth_service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return _token_response(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    _, access_token, refresh_token = await auth_service.login(
        email=body.email,
        password=body.password,
    )
    return _token_response(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    _, access_token, refresh_token = await auth_service.refresh(
        refresh_token=body.refresh_token,
    )
    return _token_response(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    await auth_service.logout(refresh_token=body.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
