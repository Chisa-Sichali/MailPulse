from pydantic import BaseModel, Field


class AnalyticsOverviewResponse(BaseModel):
    emails_processed_total: int
    emails_processed_period: int
    events_failed: int
    webhook_deliveries_total: int
    webhook_deliveries_success: int
    webhook_deliveries_failed: int
    webhook_deliveries_pending: int
    success_rate: float
    failure_rate: float
    avg_processing_latency_ms: float | None
    period_days: int


class TopSenderItem(BaseModel):
    sender_email: str
    sender_name: str
    count: int


class VolumePoint(BaseModel):
    date: str
    count: int


class WebhookPerformanceItem(BaseModel):
    webhook_id: str
    name: str | None
    url: str
    total_deliveries: int
    delivered: int
    failed: int
    success_rate: float


class ResourceCountsResponse(BaseModel):
    mailboxes: int
    enabled_mailboxes: int
    webhooks: int
