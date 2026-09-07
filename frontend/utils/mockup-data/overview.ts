export const healthCheck = [
  {
    status: 'healthy',
    service: 'MailPulse',
    version: '1.0.0',
    environment: 'development',
    checks: {
      database: 'connected',
      redis: 'connected',
      queue: 'ok',
    },
    deliveries: {
      pending: 0,
      failed: 0,
      dead_lettered: 0,
    },
  },
];

export const analyticsData = [
  {
    emails_processed_total: 1234,
    emails_processed_period: 56,
    events_failed: 2,
    webhook_deliveries_total: 112,
    webhook_deliveries_success: 110,
    webhook_deliveries_failed: 2,
    webhook_deliveries_pending: 0,
    success_rate: 98.21,
    failure_rate: 1.79,
    avg_processing_latency_ms: 450.25,
    period_days: 7,
  },
];
