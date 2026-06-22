from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class WebhookCreateRequest(BaseModel):
    url: HttpUrl
    name: str | None = Field(default=None, max_length=255)
    event_types: list[str] = Field(default_factory=lambda: ["email.received"])
    is_enabled: bool = True


class WebhookUpdateRequest(BaseModel):
    url: HttpUrl | None = None
    name: str | None = Field(default=None, max_length=255)
    event_types: list[str] | None = None
    is_enabled: bool | None = None


class WebhookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    name: str | None
    secret_prefix: str
    is_enabled: bool
    event_types: list[str]
    created_at: datetime
    updated_at: datetime


class WebhookCreatedResponse(WebhookResponse):
    secret: str


class WebhookSecretResponse(BaseModel):
    secret: str
    secret_prefix: str


class WebhookTestResponse(BaseModel):
    success: bool
    http_status_code: int
    response_body: str


class WebhookDeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    webhook_id: UUID
    email_event_id: UUID
    status: str
    attempt_count: int
    http_status_code: int | None
    response_body: str | None
    next_retry_at: datetime | None
    delivered_at: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryListResponse(BaseModel):
    items: list[WebhookDeliveryResponse]
    limit: int
    offset: int
