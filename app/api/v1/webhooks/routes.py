from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_webhook_service
from app.database.models.user import User
from app.schemas.webhooks import (
    WebhookCreatedResponse,
    WebhookCreateRequest,
    WebhookDeliveryListResponse,
    WebhookDeliveryResponse,
    WebhookResponse,
    WebhookSecretResponse,
    WebhookTestResponse,
    WebhookUpdateRequest,
)
from app.services.webhook.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _webhook_response(webhook) -> WebhookResponse:
    return WebhookResponse.model_validate(webhook)


@router.post("", response_model=WebhookCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    body: WebhookCreateRequest,
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookCreatedResponse:
    webhook, secret = await webhook_service.create_webhook(
        user=current_user,
        url=str(body.url),
        name=body.name,
        event_types=body.event_types,
        is_enabled=body.is_enabled,
    )
    return WebhookCreatedResponse(
        **WebhookResponse.model_validate(webhook).model_dump(),
        secret=secret,
    )


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> list[WebhookResponse]:
    webhooks = await webhook_service.list_webhooks(user=current_user)
    return [_webhook_response(item) for item in webhooks]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    webhook = await webhook_service.get_webhook(user=current_user, webhook_id=webhook_id)
    return _webhook_response(webhook)


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: UUID,
    body: WebhookUpdateRequest,
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse:
    webhook = await webhook_service.update_webhook(
        user=current_user,
        webhook_id=webhook_id,
        url=str(body.url) if body.url else None,
        name=body.name,
        event_types=body.event_types,
        is_enabled=body.is_enabled,
    )
    return _webhook_response(webhook)


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> None:
    await webhook_service.delete_webhook(user=current_user, webhook_id=webhook_id)


@router.post("/{webhook_id}/rotate-secret", response_model=WebhookSecretResponse)
async def rotate_webhook_secret(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookSecretResponse:
    webhook, secret = await webhook_service.rotate_secret(
        user=current_user,
        webhook_id=webhook_id,
    )
    return WebhookSecretResponse(secret=secret, secret_prefix=webhook.secret_prefix)


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: UUID,
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookTestResponse:
    http_status, response_body = await webhook_service.test_webhook(
        user=current_user,
        webhook_id=webhook_id,
    )
    return WebhookTestResponse(
        success=200 <= http_status < 300,
        http_status_code=http_status,
        response_body=response_body,
    )


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    webhook_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookDeliveryListResponse:
    deliveries = await webhook_service.list_deliveries(
        user=current_user,
        webhook_id=webhook_id,
        limit=limit,
        offset=offset,
    )
    return WebhookDeliveryListResponse(
        items=[WebhookDeliveryResponse.model_validate(item) for item in deliveries],
        limit=limit,
        offset=offset,
    )
