export interface OverviewData {
  status: 'healthy' | 'degraded';
  service: string;
  version: string;
  environment: 'development' | 'production';
  checks: {
    database: string;
    redis: 'connected' | 'disconnected';
    queue: string;
  };
  deliveries: {
    pending: number;
    failed: number;
    dead_lettered: number;
  };
}

export interface AnalyticsOverview {
  emails_processed_total: number;
  emails_processed_period: number;
  events_failed: number;
  webhook_deliveries_total: number;
  webhook_deliveries_success: number;
  webhook_deliveries_failed: number;
  webhook_deliveries_pending: number;
  success_rate: number;
  failure_rate: number;
  avg_processing_latency_ms: number | null;
  period_days: number;
}

export interface VolumePoint { date: string; count: number; }
export interface TopSender { sender_email: string; sender_name: string; count: number; }
export interface WebhookPerformance { webhook_id: string; name: string | null; url: string; total_deliveries: number; delivered: number; failed: number; success_rate: number; }
export interface EmailEvent { id: string; sender_email: string; sender_name: string; subject: string; status: string; received_at: string | null; processed_at: string | null; created_at: string; attempt_count: number; }
export interface EmailEventList { items: EmailEvent[]; limit: number; offset: number; }
