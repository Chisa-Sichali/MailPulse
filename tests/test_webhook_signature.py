import json

from app.core.security.webhook_signature import sign_webhook_payload, verify_webhook_signature


def test_sign_and_verify_webhook_payload():
    secret = "whsec_test_secret"
    payload = {"id": "evt_123", "type": "email.received", "data": {"subject": "Hi"}}

    signature_header, body = sign_webhook_payload(secret=secret, payload=payload)

    assert signature_header.startswith("t=")
    assert ",v1=" in signature_header
    assert verify_webhook_signature(
        secret=secret,
        payload_body=body,
        signature_header=signature_header,
    )


def test_verify_rejects_tampered_payload():
    secret = "whsec_test_secret"
    payload = {"id": "evt_123", "type": "email.received"}
    signature_header, body = sign_webhook_payload(secret=secret, payload=payload)

    tampered = json.loads(body)
    tampered["id"] = "evt_tampered"
    tampered_body = json.dumps(tampered, separators=(",", ":"), sort_keys=True)

    assert not verify_webhook_signature(
        secret=secret,
        payload_body=tampered_body,
        signature_header=signature_header,
    )
