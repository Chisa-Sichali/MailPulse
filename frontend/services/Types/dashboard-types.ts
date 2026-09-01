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
