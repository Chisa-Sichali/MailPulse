from dataclasses import dataclass
from email.message import Message


@dataclass(frozen=True)
class AttachmentMetadata:
    filename: str
    content_type: str
    size: int

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
        }


def extract_attachments(msg: Message) -> list[AttachmentMetadata]:
    attachments: list[AttachmentMetadata] = []

    for part in msg.walk():
        content_disposition = part.get("Content-Disposition", "")
        if "attachment" not in content_disposition.lower():
            continue

        filename = part.get_filename() or "unnamed"
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True) or b""
        attachments.append(
            AttachmentMetadata(
                filename=filename,
                content_type=content_type,
                size=len(payload),
            )
        )

    return attachments
