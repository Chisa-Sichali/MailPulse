from dataclasses import dataclass
from datetime import datetime, timezone
from email import message_from_bytes
from email.message import Message
from email.utils import getaddresses, parsedate_to_datetime

from app.services.email_processing.attachment_extractor import (
    AttachmentMetadata,
    extract_attachments,
)
from app.services.email_processing.parsers.body import clean_email_body
from app.services.email_processing.parsers.reply import is_reply
from app.services.email_processing.parsers.sender import parse_sender
from app.services.email_processing.parsers.signatures import remove_digital_signatures
from app.services.email_processing.parsers.subject import clean_subject


@dataclass(frozen=True)
class ParsedEmail:
    message_id: str
    sender_email: str
    sender_name: str
    recipients: list[str]
    subject: str
    text_body: str
    html_body: str
    attachments: list[AttachmentMetadata]
    in_reply_to: str | None
    received_at: datetime | None


def _decode_part_payload(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if payload is None:
        return ""

    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _extract_bodies(msg: Message) -> tuple[str, str]:
    text_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain" and not text_body:
                text_body = _decode_part_payload(part)
            elif content_type == "text/html" and not html_body:
                html_body = _decode_part_payload(part)
    else:
        content_type = msg.get_content_type()
        body = _decode_part_payload(msg)
        if content_type == "text/html":
            html_body = body
        else:
            text_body = body

    if text_body:
        text_body = remove_digital_signatures(text_body)
        text_body = clean_email_body(text_body)

    return text_body, html_body


def _extract_recipients(msg: Message) -> list[str]:
    header_values = []
    for header in ("To", "Cc", "Delivered-To"):
        value = msg.get(header)
        if value:
            header_values.append(value)

    addresses = getaddresses(header_values)
    return [address for _, address in addresses if address]


def _parse_received_at(msg: Message) -> datetime | None:
    date_header = msg.get("Date")
    if not date_header:
        return None

    try:
        parsed = parsedate_to_datetime(date_header)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError, IndexError):
        return None


def parse_email_message(raw_email: bytes) -> ParsedEmail:
    msg = message_from_bytes(raw_email)

    raw_message_id = (msg.get("Message-ID") or msg.get("Message-Id") or "").strip()
    message_id = raw_message_id or f"generated-{hash(raw_email)}"

    sender_name, sender_email = parse_sender(msg.get("From") or "")
    subject = clean_subject(msg.get("Subject"))
    text_body, html_body = _extract_bodies(msg)
    attachments = extract_attachments(msg)
    recipients = _extract_recipients(msg)
    in_reply_to = msg.get("In-Reply-To") if is_reply(msg) else None
    received_at = _parse_received_at(msg)

    return ParsedEmail(
        message_id=message_id,
        sender_email=sender_email,
        sender_name=sender_name,
        recipients=recipients,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        attachments=attachments,
        in_reply_to=in_reply_to,
        received_at=received_at,
    )
