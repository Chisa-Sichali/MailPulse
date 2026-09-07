import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { healthService } from '@/services/health';
import { useDashboardStore } from '@/stores/dashboard.store';
import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import DashboardHeaderLoader from '@/components/skeleton/DashboardHeaderLoader';

export default function DashboardHeader() {
  const dashboardStats = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: () => healthService.getSystemHealth(),
    staleTime: 1000 * 60 * 5,
    retry: 1,
    refetchInterval: 60_000,
  });

  const setOverviewData = useDashboardStore((state) => state.setOverviewData);

  useEffect(() => {
    if (dashboardStats.data) {
      setOverviewData(dashboardStats.data);
    }
  }, [dashboardStats.data, setOverviewData]);

  const system = dashboardStats.data;
  const checks = system?.checks ?? {};
  const isHealthy = system ? system.status === 'healthy' : true;
  const isConnected = Object.values(checks).every((c) => c === 'connected' || c === 'ok');

  if (dashboardStats.isPending) return <DashboardHeaderLoader />;
  if (dashboardStats.isError) return <Card className="border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-800 dark:text-amber-300">System health is currently unavailable. Dashboard data will continue to refresh.</Card>;
  return (
    <Card className="w-full overflow-hidden border-0 bg-linear-to-r from-indigo-600 to-violet-600 text-white shadow-lg">
      <div className="flex flex-col gap-4 p-4 md:flex-row md:items-center md:gap-6 md:p-6">
        {/* Status */}
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <span
            className={cn(
              'size-2.5 shrink-0 rounded-full',
              isHealthy
                ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.9)]'
                : 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.9)]',
            )}
          />
          <div className="min-w-0">
            <p className="text-sm font-semibold">
              {isHealthy ? 'All systems operational' : 'System degraded'}
            </p>
            <p className="truncate text-xs text-white/70">
              {system?.service} v{system?.version} · {system?.environment} environment
            </p>
          </div>
        </div>

        {/* More info */}
        <Link
          href="/system"
          className="group inline-flex shrink-0 items-center gap-1.5 self-start text-sm font-medium text-white/80 transition-colors hover:text-white md:self-center"
        >
          {isHealthy ? 'View system status' : 'View details'}
          <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
        </Link>

        {/* Connection state */}
        <div className="inline-flex shrink-0 items-center gap-2 self-start rounded-full border border-white/20 bg-white/10 px-3 py-1.5 backdrop-blur-sm md:self-center">
          <span
            className={cn('size-2 rounded-full', isConnected ? 'bg-emerald-400' : 'bg-red-400')}
          />
          <span className="text-xs font-medium">{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </Card>
  );
}
