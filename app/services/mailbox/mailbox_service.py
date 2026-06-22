import asyncio
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security.encryption import decrypt_secret, encrypt_secret
from app.database.models.mailbox import Mailbox, MailboxHealthStatus
from app.database.models.user import User
from app.database.repositories.mailbox_repository import MailboxRepository
from app.services.mailbox.imap_connection import test_imap_connection


class MailboxService:
    def __init__(self, mailbox_repo: MailboxRepository) -> None:
        self._mailboxes = mailbox_repo

    async def create_mailbox(
        self,
        *,
        user: User,
        email_address: str,
        password: str,
        imap_host: str,
        imap_port: int,
        imap_username: str | None = None,
        is_enabled: bool = True,
    ) -> Mailbox:
        existing = await self._mailboxes.get_by_email_for_user(
            user_id=user.id,
            email_address=email_address,
        )
        if existing:
            raise ConflictError("A mailbox with this email address already exists")

        username = imap_username or email_address
        encrypted_password = encrypt_secret(password)

        return await self._mailboxes.create(
            user_id=user.id,
            email_address=email_address,
            imap_username=username,
            imap_host=imap_host,
            imap_port=imap_port,
            encrypted_password=encrypted_password,
            is_enabled=is_enabled,
        )

    async def list_mailboxes(self, *, user: User) -> list[Mailbox]:
        return await self._mailboxes.list_for_user(user.id)

    async def get_mailbox(self, *, user: User, mailbox_id: UUID) -> Mailbox:
        mailbox = await self._mailboxes.get_by_id_for_user(mailbox_id, user.id)
        if mailbox is None:
            raise NotFoundError("Mailbox not found")
        return mailbox

    async def update_mailbox(
        self,
        *,
        user: User,
        mailbox_id: UUID,
        email_address: str | None = None,
        password: str | None = None,
        imap_host: str | None = None,
        imap_port: int | None = None,
        imap_username: str | None = None,
        is_enabled: bool | None = None,
    ) -> Mailbox:
        mailbox = await self.get_mailbox(user=user, mailbox_id=mailbox_id)

        if email_address and email_address.strip().lower() != mailbox.email_address:
            duplicate = await self._mailboxes.get_by_email_for_user(
                user_id=user.id,
                email_address=email_address,
            )
            if duplicate and duplicate.id != mailbox.id:
                raise ConflictError("A mailbox with this email address already exists")
            mailbox.email_address = email_address.strip().lower()

        if imap_username is not None:
            mailbox.imap_username = imap_username.strip()
        if imap_host is not None:
            mailbox.imap_host = imap_host.strip()
        if imap_port is not None:
            mailbox.imap_port = imap_port
        if password is not None:
            mailbox.encrypted_password = encrypt_secret(password)
        if is_enabled is not None:
            mailbox.is_enabled = is_enabled

        return await self._mailboxes.save(mailbox)

    async def delete_mailbox(self, *, user: User, mailbox_id: UUID) -> None:
        mailbox = await self.get_mailbox(user=user, mailbox_id=mailbox_id)
        await self._mailboxes.soft_delete(mailbox)

    async def test_connection(self, *, user: User, mailbox_id: UUID) -> Mailbox:
        mailbox = await self.get_mailbox(user=user, mailbox_id=mailbox_id)
        password = decrypt_secret(mailbox.encrypted_password)

        result = await asyncio.to_thread(
            test_imap_connection,
            host=mailbox.imap_host,
            port=mailbox.imap_port,
            username=mailbox.imap_username,
            password=password,
        )

        if result.success:
            return await self._mailboxes.record_health(
                mailbox,
                health_status=MailboxHealthStatus.HEALTHY.value,
                synced=False,
            )

        return await self._mailboxes.record_health(
            mailbox,
            health_status=MailboxHealthStatus.ERROR.value,
            error_message=result.message,
        )

    def get_decrypted_password(self, mailbox: Mailbox) -> str:
        return decrypt_secret(mailbox.encrypted_password)
