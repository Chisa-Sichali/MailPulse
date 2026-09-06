'use client';
import { useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { healthService } from '@/services/health';
import { EmptyPanel, ErrorPanel, TableSkeleton } from '@/features/infrastructure/shared';
const ranges = [7, 14, 30, 90];
export default function AnalyticsPage() {
  const [days, setDays] = useState(30);
  const [overview, volume, senders, webhooks, resources] = useQueries({
    queries: [
      {
        queryKey: ['analyticsOverview', days],
        queryFn: () => healthService.getAnalyticsOverview(days),
      },
      { queryKey: ['analyticsVolume', days], queryFn: () => healthService.getVolume(days) },
      { queryKey: ['analyticsTopSenders', days], queryFn: () => healthService.getTopSenders(days) },
      {
        queryKey: ['analyticsWebhooks', days],
        queryFn: () => healthService.getWebhookPerformance(days),
      },
      { queryKey: ['analyticsResources'], queryFn: () => healthService.getResources() },
    ],
  });
  const failed = [overview, volume, senders, webhooks, resources].some((query) => query.isError);
  const loading = [overview, volume, senders, webhooks, resources].some((query) => query.isPending);
  return (
    <main className="bg-background flex flex-1 flex-col px-4 py-4 md:px-6 md:py-5">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <p className="text-primary text-xs font-semibold tracking-[.14em] uppercase">
              Delivery intelligence
            </p>
            <h1 className="text-xl font-semibold tracking-tight">Analytics</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Operational throughput, delivery quality, and traffic composition.
            </p>
          </div>
          <Select
            value={days}
            onValueChange={(value) => value !== null && setDays(value)}
            items={ranges.map((value) => ({ value, label: `${value} days` }))}
          >
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ranges.map((value) => (
                <SelectItem key={value} value={value}>
                  {value} days
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </header>
        {failed && (
          <ErrorPanel message="Some analytics signals are unavailable. Available data is still shown below." />
        )}
        {loading ? (
          <TableSkeleton rows={7} />
        ) : (
          <>
            <section className="bg-border grid gap-px overflow-hidden rounded-lg border sm:grid-cols-2 lg:grid-cols-4">
              <Metric
                label="Processed in period"
                value={overview.data?.emails_processed_period.toLocaleString() ?? '—'}
                detail={`${overview.data?.emails_processed_total.toLocaleString() ?? '—'} total`}
              />
              <Metric
                label="Delivery success"
                value={overview.data ? `${overview.data.success_rate.toFixed(1)}%` : '—'}
                detail={`${overview.data?.webhook_deliveries_success ?? '—'} successful`}
              />
              <Metric
                label="Failures"
                value={overview.data?.webhook_deliveries_failed.toLocaleString() ?? '—'}
                detail={`${overview.data?.events_failed ?? '—'} event failures`}
                danger
              />
              <Metric
                label="Mean latency"
                value={
                  overview.data?.avg_processing_latency_ms == null
                    ? '—'
                    : `${overview.data.avg_processing_latency_ms.toFixed(0)} ms`
                }
                detail={`${overview.data?.webhook_deliveries_pending ?? '—'} pending deliveries`}
              />
            </section>
            <section className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
              <Card>
                <CardHeader className="border-b pb-4">
                  <CardTitle className="text-sm">Processing volume</CardTitle>
                  <CardDescription>
                    Daily messages received across the selected period.
                  </CardDescription>
                </CardHeader>
                <CardContent className="h-72 px-3 py-5">
                  {volume.data?.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={volume.data} margin={{ top: 8, right: 8, left: -20 }}>
                        <defs>
                          <linearGradient id="analyticsFill" x1="0" x2="0" y1="0" y2="1">
                            <stop offset="0" stopColor="var(--chart-1)" stopOpacity=".32" />
                            <stop offset="1" stopColor="var(--chart-1)" stopOpacity=".02" />
                          </linearGradient>
                        </defs>
                        <CartesianGrid
                          vertical={false}
                          stroke="var(--border)"
                          strokeDasharray="3 3"
                        />
                        <XAxis
                          dataKey="date"
                          tickFormatter={(value) =>
                            new Intl.DateTimeFormat(undefined, {
                              month: 'short',
                              day: 'numeric',
                            }).format(new Date(`${value}T00:00:00`))
                          }
                          tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <YAxis
                          allowDecimals={false}
                          tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
                          tickLine={false}
                          axisLine={false}
                        />
                        <Tooltip
                          contentStyle={{
                            background: 'var(--popover)',
                            border: '1px solid var(--border)',
                            borderRadius: 8,
                            color: 'var(--popover-foreground)',
                          }}
                        />
                        <Area
                          dataKey="count"
                          name="Emails"
                          stroke="var(--chart-1)"
                          fill="url(#analyticsFill)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyPanel
                      title="No volume in this period"
                      detail="Daily activity will appear as email events are processed."
                    />
                  )}
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="border-b pb-4">
                  <CardTitle className="text-sm">Resource footprint</CardTitle>
                  <CardDescription>Active infrastructure under this account.</CardDescription>
                </CardHeader>
                <CardContent className="divide-y py-2">
                  {[
                    ['Mailboxes', resources.data?.mailboxes],
                    ['Enabled monitors', resources.data?.enabled_mailboxes],
                    ['Webhook destinations', resources.data?.webhooks],
                  ].map(([label, value]) => (
                    <div className="flex items-center justify-between py-4" key={String(label)}>
                      <span className="text-muted-foreground text-sm">{label}</span>
                      <span className="font-mono text-lg font-semibold">{value ?? '—'}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </section>
            <section className="grid gap-5 xl:grid-cols-2">
              <DataList
                title="Traffic concentration"
                description="Most frequent senders by processed event count."
                empty="No sender activity in this period."
              >
                {senders.data?.map((item) => (
                  <div className="flex items-center gap-3 py-3" key={item.sender_email}>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {item.sender_name || item.sender_email}
                      </p>
                      <p className="text-muted-foreground truncate text-xs">{item.sender_email}</p>
                    </div>
                    <span className="font-mono text-sm">{item.count.toLocaleString()}</span>
                  </div>
                ))}
              </DataList>
              <DataList
                title="Destination reliability"
                description="Webhook delivery performance during the selected period."
                empty="No webhook deliveries in this period."
              >
                {webhooks.data?.map((item) => (
                  <div className="flex items-center gap-3 py-3" key={item.webhook_id}>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {item.name || new URL(item.url).hostname}
                      </p>
                      <p className="text-muted-foreground text-xs">
                        {item.delivered.toLocaleString()} delivered · {item.failed.toLocaleString()}{' '}
                        failed
                      </p>
                    </div>
                    <span className="font-mono text-sm">{item.success_rate.toFixed(1)}%</span>
                  </div>
                ))}
              </DataList>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
function Metric({
  label,
  value,
  detail,
  danger,
}: {
  label: string;
  value: string;
  detail: string;
  danger?: boolean;
}) {
  return (
    <div className="bg-card p-4">
      <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">{label}</p>
      <p className={`mt-2 text-2xl font-semibold tabular-nums ${danger ? 'text-destructive' : ''}`}>
        {value}
      </p>
      <p className="text-muted-foreground mt-1 text-xs">{detail}</p>
    </div>
  );
}
function DataList({
  title,
  description,
  empty,
  children,
}: {
  title: string;
  description: string;
  empty: string;
  children: React.ReactNode;
}) {
  const hasChildren = Array.isArray(children) && children.length > 0;
  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <CardTitle className="text-sm">{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="divide-y">
        {hasChildren ? children : <EmptyPanel title={empty} detail="" />}
      </CardContent>
    </Card>
  );
}
