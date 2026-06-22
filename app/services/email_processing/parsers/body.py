import re
from email_reply_parser import EmailReplyParser


def clean_email_body(raw_email: str) -> str:
    text = raw_email.replace("\r\n", "\n").strip()

    quote_patterns = [
        r"-+\s*From:.+?\n\n?",
        r"(?i)On\s.+?wrote:.*?\n\n?",
        r"On\s.+\s<[^>]+>\s+wrote:.*?\n\n?",
        r"-+\s*Original Message\s*-+.*?\n\n?",
        r"(?i)On\s.+?<[^>]+>\s+wrote:.*?\n\n?",
        r"(?i)\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}\s+[AP]M.*?\n\n?",
    ]

    for pattern in quote_patterns:
        text = re.sub(pattern, "\n", text, flags=re.DOTALL)

    text = EmailReplyParser.parse_reply(text)

    signature_patterns = [
        r"(?i)\bkind regards\b.*",
        r"(?i)\bregards\b.*",
        r"(?i)\bbest regards\b.*",
        r"(?i)\bsincerely\b.*",
        r"(?i)\bthank you\b.*\n.*",
    ]

    for pattern in signature_patterns:
        text = re.split(pattern, text, maxsplit=1)[0]

    text = re.sub(
        r"(?is)(from:|sent:|to:|cc:|subject:).*",
        "",
        text,
    )

    text = re.sub(r"<mailto:[^>]+>", "", text)
    text = re.sub(r"<https?://[^>]+>", "", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[cid:[^\]]+\]", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()
