import imaplib
from dataclasses import dataclass


@dataclass(frozen=True)
class ImapCredentials:
    host: str
    port: int
    username: str
    password: str


class ImapClient:
    def __init__(self, credentials: ImapCredentials) -> None:
        self._credentials = credentials
        self._mail: imaplib.IMAP4 | None = None

    def connect(self) -> None:
        if self._credentials.port == 993:
            self._mail = imaplib.IMAP4_SSL(
                self._credentials.host,
                self._credentials.port,
            )
        else:
            self._mail = imaplib.IMAP4(
                self._credentials.host,
                self._credentials.port,
            )
        self._mail.login(self._credentials.username, self._credentials.password)
        self._mail.select("INBOX")

    def search_unseen_uids(self) -> list[str]:
        if self._mail is None:
            raise RuntimeError("IMAP client is not connected")

        status, messages = self._mail.search(None, "UNSEEN")
        if status != "OK":
            raise RuntimeError(f"IMAP search failed with status: {status}")

        raw_ids = messages[0].split()
        return [uid.decode() for uid in raw_ids if uid]

    def fetch_rfc822(self, uid: str) -> bytes:
        if self._mail is None:
            raise RuntimeError("IMAP client is not connected")

        status, msg_data = self._mail.fetch(uid.encode(), "(RFC822)")
        if status != "OK" or not msg_data or not msg_data[0]:
            raise RuntimeError(f"Failed to fetch message UID {uid}")

        return msg_data[0][1]

    def mark_as_seen(self, uid: str) -> None:
        if self._mail is None:
            raise RuntimeError("IMAP client is not connected")

        self._mail.store(uid.encode(), "+FLAGS", "\\Seen")

    def logout(self) -> None:
        if self._mail is not None:
            try:
                self._mail.logout()
            finally:
                self._mail = None

    def __enter__(self) -> "ImapClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.logout()
