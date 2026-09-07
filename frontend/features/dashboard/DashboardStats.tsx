'use client';

import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { CardContent } from '@/components/ui/card';
import { useDashboardStore } from '@/stores/dashboard.store';
import { healthService } from '@/services/health';
import DashboardStatsLoader from '@/components/skeleton/DashboardStatsLoader';

interface StatConfig {
  label: string;
  format?: (value: number) => string;
}

const STAT_CONFIGS: Record<string, StatConfig> = {
  emails_processed_period: {
    label: 'Emails Processed',
    format: (value) => value.toLocaleString(),
  },
  success_rate: {
    label: 'Success Rate',
    format: (value) => `${value.toFixed(1)}%`,
  },
  avg_processing_latency_ms: {
    label: 'Avg Processing Latency',
    format: (value) => `${value.toFixed(2)}ms`,
  },
  webhook_deliveries_total: {
    label: 'Webhook Deliveries Total',
    format: (value) => `${value.toLocaleString()}`,
  },
};
export default function DashboardStats() {
  const queryDays = useDashboardStore((data) => data.daysFilter);
  const dashboardAnalytics = useQuery({
    queryKey: ['analyticsOverview', queryDays],
    queryFn: () => healthService.getAnalyticsOverview(queryDays),
    staleTime: 1000 * 60 * 5,
    retry: 1,
    refetchInterval: 30_000,
  });

  const stats = dashboardAnalytics.data;

  if (dashboardAnalytics.isPending) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <DashboardStatsLoader />
      </div>
    );
  }

  if (dashboardAnalytics.isError || !stats) {
    return <div className="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">Dashboard metrics could not be loaded. They will retry automatically.</div>;
  }

  const displayStats = [
    'emails_processed_period',
    'success_rate',
    'avg_processing_latency_ms',
    'webhook_deliveries_total',
  ] as const;

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
      {displayStats.map((key) => {
        const config = STAT_CONFIGS[key];
        const rawValue = stats[key as keyof typeof stats];

        const displayValue =
          config?.format && typeof rawValue === 'number' ? config.format(rawValue) : rawValue;

        return (
          <Card key={key} className="border-border/80 bg-card text-card-foreground shadow-sm">
            <CardContent className="flex flex-col gap-1.5 p-4">
              <span className="text-muted-foreground text-xs font-semibold tracking-wider">
                {config?.label.toUpperCase() ?? key}
              </span>
              <span
                className={cn(
                  'text-foreground text-2xl font-bold tracking-tight',
                  key === 'success_rate' &&
                    parseFloat(displayValue as string) > 50 &&
                    'text-green-500',
                  key === 'success_rate' &&
                    parseFloat(displayValue as string) <= 50 &&
                    'text-red-500',
                  key === 'emails_processed_period' && 'text-blue-500',
                  key === 'avg_processing_latency_ms' && 'text-yellow-500',
                  key === 'webhook_deliveries_total' && 'text-purple-500',
                )}
              >
                {displayValue ?? '-'}
              </span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
