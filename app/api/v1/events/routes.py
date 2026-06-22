from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_email_event_service
from app.database.models.user import User
from app.schemas.events import EmailEventListResponse, EmailEventResponse
from app.services.email_processing.event_service import EmailEventService

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EmailEventListResponse)
async def list_events(
    mailbox_id: UUID | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    event_service: EmailEventService = Depends(get_email_event_service),
) -> EmailEventListResponse:
    events = await event_service.list_events(
        user_id=current_user.id,
        mailbox_id=mailbox_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return EmailEventListResponse(
        items=[EmailEventResponse.model_validate(event) for event in events],
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=EmailEventResponse)
async def get_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EmailEventService = Depends(get_email_event_service),
) -> EmailEventResponse:
    event = await event_service.get_event(user_id=current_user.id, event_id=event_id)
    return EmailEventResponse.model_validate(event)


@router.post("/{event_id}/retry", status_code=status.HTTP_202_ACCEPTED)
async def retry_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    event_service: EmailEventService = Depends(get_email_event_service),
) -> dict[str, str]:
    await event_service.retry_event(user_id=current_user.id, event_id=event_id)
    return {"status": "queued"}
