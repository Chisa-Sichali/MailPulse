import re
from email.header import decode_header, make_header
from typing import Union


def clean_subject(
    subject: Union[str, bytes],
    *,
    max_decode_passes: int = 2,
) -> str:
    if not subject:
        return ""

    if isinstance(subject, bytes):
        try:
            subject = subject.decode("utf-8", errors="replace")
        except Exception:
            subject = subject.decode("latin-1", errors="replace")

    value = subject

    for _ in range(max_decode_passes):
        decoded = str(make_header(decode_header(value)))

        if decoded == value or "=?UTF-" not in decoded and "=?utf-" not in decoded:
            value = decoded
            break

        value = decoded

    value = value.replace("_", " ")

    def qp_fix(match):
        try:
            return bytes.fromhex(match.group(1)).decode("utf-8")
        except Exception:
            return match.group(0)

    value = re.sub(r"=([0-9A-Fa-f]{2})", qp_fix, value)
    value = re.sub(r"\s+", " ", value).strip()

    return value
