import imaplib
from dataclasses import dataclass


@dataclass(frozen=True)
class ImapConnectionResult:
    success: bool
    message: str


def test_imap_connection(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    mailbox: str = "INBOX",
) -> ImapConnectionResult:
    mail = None
    try:
        if port == 993:
            mail = imaplib.IMAP4_SSL(host, port)
        else:
            mail = imaplib.IMAP4(host, port)

        mail.login(username, password)
        status, _ = mail.select(mailbox)
        if status != "OK":
            return ImapConnectionResult(
                success=False,
                message=f"Failed to select mailbox '{mailbox}'",
            )

        return ImapConnectionResult(success=True, message="Connection successful")
    except imaplib.IMAP4.error as exc:
        return ImapConnectionResult(success=False, message=str(exc))
    except OSError as exc:
        return ImapConnectionResult(success=False, message=str(exc))
    finally:
        if mail is not None:
            try:
                mail.logout()
            except Exception:
                pass
