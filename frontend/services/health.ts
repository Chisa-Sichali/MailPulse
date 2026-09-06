import { config } from '@/config/config';
import { apiFetch } from '@/services/api-client';
import type { AnalyticsOverview, EmailEventList, TopSender, VolumePoint, WebhookPerformance } from '@/services/Types/dashboard-types';

class HealthService {
  private static healthBaseUrl = config.fastapi_backend_url;

  async getSystemHealth() {
    try {
      const response = await fetch(`${HealthService.healthBaseUrl}/health/system`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching system health:', error);
      throw error;
    }
  }

  async getAnalyticsOverview(days?: number): Promise<AnalyticsOverview> {
    try {
      const response = await apiFetch(`/analytics/overview?days=${days}`, {
        method: 'GET',
      });
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    } catch (error) {
      console.error('Error fetching analytics overview:', error);
      throw error;
    }
  }

  async getVolume(days: number): Promise<VolumePoint[]> {
    return this.getAnalytics(`/analytics/volume?days=${days}`);
  }

  async getTopSenders(days: number): Promise<TopSender[]> {
    return this.getAnalytics(`/analytics/top-senders?days=${days}&limit=6`);
  }

  async getWebhookPerformance(days: number): Promise<WebhookPerformance[]> {
    return this.getAnalytics(`/analytics/webhooks?days=${days}`);
  }

  async getRecentEvents(): Promise<EmailEventList> {
    return this.getAnalytics('/events?limit=8');
  }

  private async getAnalytics<T>(path: string): Promise<T> {
    const response = await apiFetch(path, { method: 'GET' });
    if (!response.ok) throw new Error('Unable to load dashboard data');
    return response.json() as Promise<T>;
  }
}

export const healthService = new HealthService();
