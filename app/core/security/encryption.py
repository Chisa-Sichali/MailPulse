import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings
from app.core.exceptions import MailPulseError


def _build_fernet() -> Fernet:
    settings = get_settings()
    source = settings.credential_encryption_key or settings.jwt_secret_key
    digest = hashlib.sha256(source.encode()).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return _build_fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    try:
        return _build_fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise MailPulseError(
            "Failed to decrypt mailbox credentials",
            code="credential_error",
        ) from exc
