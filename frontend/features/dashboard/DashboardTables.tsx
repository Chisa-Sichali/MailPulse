'use client';

import { useQuery } from '@tanstack/react-query';
import { CheckCircle2, CircleAlert, Clock3, Mail } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { healthService } from '@/services/health';
import { cn } from '@/lib/utils';

const POLL_INTERVAL = 60_000;

export function DashboardTables({ days }: { days: number }) {
  const topSenders = useQuery({
    queryKey: ['topSenders', days],
    queryFn: () => healthService.getTopSenders(days),
    staleTime: 30_000,
    refetchInterval: POLL_INTERVAL,
  });
  const webhooks = useQuery({
    queryKey: ['webhookPerformance', days],
    queryFn: () => healthService.getWebhookPerformance(days),
    staleTime: 30_000,
    refetchInterval: POLL_INTERVAL,
  });
  const events = useQuery({
    queryKey: ['recentEvents'],
    queryFn: () => healthService.getRecentEvents(),
    staleTime: 15_000,
    refetchInterval: 30_000,
  });

  return (
    <div className="grid gap-5 xl:grid-cols-2">
      <Panel
        title="Webhook delivery"
        description="Delivery performance for configured destinations."
      >
        {webhooks.isPending ? (
          <Rows />
        ) : webhooks.isError ? (
          <PanelMessage message="Webhook delivery data is unavailable." />
        ) : webhooks.data?.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-xs">
              <thead className="border-border text-muted-foreground border-b">
                <tr>
                  <th className="pb-3 font-medium">Destination</th>
                  <th className="pb-3 font-medium">Delivered</th>
                  <th className="pb-3 font-medium">Failed</th>
                  <th className="pb-3 text-right font-medium">Success</th>
                </tr>
              </thead>
              <tbody>
                {webhooks.data.map((item) => (
                  <tr key={item.webhook_id} className="border-border/60 border-b last:border-0">
                    <td className="max-w-52 py-3">
                      <p className="truncate font-medium">
                        {item.name || new URL(item.url).hostname}
                      </p>
                      <p className="text-muted-foreground truncate">{new URL(item.url).hostname}</p>
                    </td>
                    <td className="py-3 text-emerald-600 dark:text-emerald-400">
                      {item.delivered.toLocaleString()}
                    </td>
                    <td className="text-destructive py-3">{item.failed.toLocaleString()}</td>
                    <td className="py-3 text-right font-medium">{item.success_rate.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <PanelMessage message="No webhook deliveries in this period." />
        )}
      </Panel>
      <Panel title="Top senders" description="Most active senders from processed email events.">
        {topSenders.isPending ? (
          <Rows />
        ) : topSenders.isError ? (
          <PanelMessage message="Sender activity is unavailable." />
        ) : topSenders.data?.length ? (
          <div className="divide-border/60 divide-y">
            {topSenders.data.map((sender) => (
              <div key={sender.sender_email} className="flex items-center gap-3 py-3">
                <span className="bg-primary/10 text-primary flex size-8 shrink-0 items-center justify-center rounded-full">
                  <Mail className="size-4" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">
                    {sender.sender_name || sender.sender_email}
                  </p>
                  <p className="text-muted-foreground truncate text-xs">{sender.sender_email}</p>
                </div>
                <span className="text-sm font-semibold tabular-nums">
                  {sender.count.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <PanelMessage message="No sender activity in this period." />
        )}
      </Panel>
      <Panel
        title="Recent events"
        description="Latest email processing activity."
        className="xl:col-span-2"
      >
        {events.isPending ? (
          <Rows count={5} />
        ) : events.isError ? (
          <PanelMessage message="Recent events are unavailable." />
        ) : events.data?.items.length ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-xs">
              <thead className="border-border text-muted-foreground border-b">
                <tr>
                  <th className="pb-3 font-medium">Sender</th>
                  <th className="pb-3 font-medium">Subject</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 text-right font-medium">Received</th>
                </tr>
              </thead>
              <tbody>
                {events.data.items.map((event) => (
                  <tr key={event.id} className="border-border/60 border-b last:border-0">
                    <td className="max-w-48 py-3">
                      <p className="truncate font-medium">
                        {event.sender_name || event.sender_email}
                      </p>
                      <p className="text-muted-foreground truncate">{event.sender_email}</p>
                    </td>
                    <td className="text-muted-foreground max-w-72 truncate py-3">
                      {event.subject || '(no subject)'}
                    </td>
                    <td className="py-3">
                      <Status status={event.status} />
                    </td>
                    <td className="text-muted-foreground py-3 text-right">
                      {formatTime(event.received_at || event.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <PanelMessage message="No email events have been recorded yet." />
        )}
      </Panel>
    </div>
  );
}

function Panel({
  title,
  description,
  children,
  className,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn('border-border/80 shadow-sm', className)}>
      <CardHeader className="border-border/70 border-b pb-4">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="px-5 pb-4">{children}</CardContent>
    </Card>
  );
}
function Rows({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3 py-3">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} className="h-8 w-full" />
      ))}
    </div>
  );
}
function PanelMessage({ message }: { message: string }) {
  return (
    <div className="text-muted-foreground flex min-h-28 items-center justify-center py-5 text-center text-sm">
      {message}
    </div>
  );
}
function Status({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const Icon =
    normalized === 'processed' || normalized === 'delivered'
      ? CheckCircle2
      : normalized === 'failed'
        ? CircleAlert
        : Clock3;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-1 font-medium',
        normalized === 'failed'
          ? 'bg-destructive/10 text-destructive'
          : normalized === 'processed' || normalized === 'delivered'
            ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400'
            : 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
      )}
    >
      <Icon className="size-3" />
      {status}
    </span>
  );
}
function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}
