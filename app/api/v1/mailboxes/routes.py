from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_mailbox_service
from app.database.models.mailbox import MailboxHealthStatus
from app.database.models.user import User
from app.schemas.mailbox import (
    MailboxConnectionTestResponse,
    MailboxCreateRequest,
    MailboxResponse,
    MailboxListResponse,
    MailboxUpdateRequest,
)
from app.services.mailbox import MailboxService

router = APIRouter(prefix="/mailboxes", tags=["mailboxes"])


@router.post("", response_model=MailboxResponse, status_code=status.HTTP_201_CREATED)
async def create_mailbox(
    body: MailboxCreateRequest,
    current_user: User = Depends(get_current_user),
    mailbox_service: MailboxService = Depends(get_mailbox_service),
) -> MailboxResponse:
    mailbox = await mailbox_service.create_mailbox(
        user=current_user,
        email_address=body.email_address,
        password=body.password,
        imap_host=body.imap_host,
        imap_port=body.imap_port,
        imap_username=body.imap_username,
        is_enabled=body.is_enabled,
    )
    return MailboxResponse.model_validate(mailbox)


@router.get("", response_model=MailboxListResponse)
async def list_mailboxes(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    mailbox_service: MailboxService = Depends(get_mailbox_service),
) -> MailboxListResponse:
    mailboxes = await mailbox_service.list_mailboxes(user=current_user, limit=limit, offset=offset)
    return MailboxListResponse(items=[MailboxResponse.model_validate(item) for item in mailboxes], limit=limit, offset=offset)


@router.get("/{mailbox_id}", response_model=MailboxResponse)
async def get_mailbox(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    mailbox_service: MailboxService = Depends(get_mailbox_service),
) -> MailboxResponse:
    mailbox = await mailbox_service.get_mailbox(user=current_user, mailbox_id=mailbox_id)
    return MailboxResponse.model_validate(mailbox)


@router.patch("/{mailbox_id}", response_model=MailboxResponse)
async def update_mailbox(
    mailbox_id: UUID,
    body: MailboxUpdateRequest,
    current_user: User = Depends(get_current_user),
    mailbox_service: MailboxService = Depends(get_mailbox_service),
) -> MailboxResponse:
    mailbox = await mailbox_service.update_mailbox(
        user=current_user,
        mailbox_id=mailbox_id,
        email_address=body.email_address,
        password=body.password,
        imap_host=body.imap_host,
        imap_port=body.imap_port,
        imap_username=body.imap_username,
        is_enabled=body.is_enabled,
    )
    return MailboxResponse.model_validate(mailbox)


@router.delete("/{mailbox_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mailbox(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    mailbox_service: MailboxService = Depends(get_mailbox_service),
) -> None:
    await mailbox_service.delete_mailbox(user=current_user, mailbox_id=mailbox_id)


@router.post("/{mailbox_id}/test-connection", response_model=MailboxConnectionTestResponse)
async def test_mailbox_connection(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    mailbox_service: MailboxService = Depends(get_mailbox_service),
) -> MailboxConnectionTestResponse:
    mailbox = await mailbox_service.test_connection(
        user=current_user,
        mailbox_id=mailbox_id,
    )
    success = mailbox.health_status == MailboxHealthStatus.HEALTHY.value
    message = (
        "Connection successful"
        if success
        else mailbox.last_error_message or "Connection failed"
    )
    return MailboxConnectionTestResponse(
        success=success,
        message=message,
        health_status=mailbox.health_status,
        mailbox=MailboxResponse.model_validate(mailbox),
    )
