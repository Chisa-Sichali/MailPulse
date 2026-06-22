import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

security = HTTPBearer()


def verify_cron_request(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    settings = get_settings()
    cron_secret = settings.cron_secret_key

    if not cron_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CRON_SECRET_KEY is not configured in the server environment.",
        )

    is_valid = secrets.compare_digest(credentials.credentials, cron_secret)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or unauthorized cron token.",
        )

    return credentials.credentials
