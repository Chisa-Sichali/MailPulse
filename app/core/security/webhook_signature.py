import hashlib
import hmac
import json
import time
from typing import Any


def sign_webhook_payload(*, secret: str, payload: dict[str, Any]) -> tuple[str, str]:
    timestamp = str(int(time.time()))
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signed_content = f"{timestamp}.{body}"
    digest = hmac.new(
        secret.encode(),
        signed_content.encode(),
        hashlib.sha256,
    ).hexdigest()
    signature_header = f"t={timestamp},v1={digest}"
    return signature_header, body


def verify_webhook_signature(
    *,
    secret: str,
    payload_body: str,
    signature_header: str,
    tolerance_seconds: int = 300,
) -> bool:
    parts = {}
    for item in signature_header.split(","):
        key, _, value = item.partition("=")
        parts[key.strip()] = value.strip()

    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False

    if abs(int(time.time()) - int(timestamp)) > tolerance_seconds:
        return False

    signed_content = f"{timestamp}.{payload_body}"
    expected = hmac.new(
        secret.encode(),
        signed_content.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
