from email.message import EmailMessage

from app.services.email_processing.attachment_extractor import extract_attachments
from app.services.email_processing.email_parser import parse_email_message


def _build_sample_message() -> bytes:
    msg = EmailMessage()
    msg["From"] = "Jane Doe <jane@example.com>"
    msg["To"] = "inbox@example.com"
    msg["Subject"] = "Hello MailPulse"
    msg["Message-ID"] = "<sample-123@example.com>"
    msg.set_content("Hello from the test suite.")
    msg.add_attachment(
        b"file-bytes",
        maintype="application",
        subtype="pdf",
        filename="report.pdf",
    )
    return msg.as_bytes()


def test_parse_email_message_extracts_core_fields():
    parsed = parse_email_message(_build_sample_message())

    assert parsed.message_id == "<sample-123@example.com>"
    assert parsed.sender_email == "jane@example.com"
    assert parsed.sender_name == "Jane Doe"
    assert parsed.subject == "Hello MailPulse"
    assert "Hello from the test suite" in parsed.text_body
    assert parsed.recipients == ["inbox@example.com"]


def test_extract_attachments_metadata():
    msg = EmailMessage()
    msg.add_attachment(
        b"12345",
        maintype="text",
        subtype="plain",
        filename="notes.txt",
    )

    attachments = extract_attachments(msg)
    assert len(attachments) == 1
    assert attachments[0].filename == "notes.txt"
    assert attachments[0].size == 5
