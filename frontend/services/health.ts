import { config } from '@/config/config';
import { apiFetch } from '@/services/api-client';

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

  async getAnalyticsOverview(days?: number) {
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
}

export const healthService = new HealthService();
