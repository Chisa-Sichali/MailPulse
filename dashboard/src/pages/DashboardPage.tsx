import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader, StatCard } from "../components/ui";
import { apiFetch } from "../lib/api";

type Overview = {
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
};

type VolumePoint = { date: string; count: number };

export function DashboardPage() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [volume, setVolume] = useState<VolumePoint[]>([]);
  const [resources, setResources] = useState<{
    mailboxes: number;
    enabled_mailboxes: number;
    webhooks: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setErrors([]);

    const overviewPromise = apiFetch<Overview>("/api/v1/analytics/overview?days=7");
    const volumePromise = apiFetch<VolumePoint[]>("/api/v1/analytics/volume?days=14");
    const resourcesPromise = apiFetch<{
      mailboxes: number;
      enabled_mailboxes: number;
      webhooks: number;
    }>("/api/v1/analytics/resources");

    Promise.allSettled([overviewPromise, volumePromise, resourcesPromise])
      .then((results) => {
        if (!active) return;

        const nextErrors: string[] = [];

        const [overviewResult, volumeResult, resourcesResult] = results;

        if (overviewResult.status === "fulfilled") {
          setOverview(overviewResult.value);
        } else {
          nextErrors.push(overviewResult.reason instanceof Error ? overviewResult.reason.message : "Overview failed");
        }

        if (volumeResult.status === "fulfilled") {
          setVolume(volumeResult.value);
        } else {
          nextErrors.push(volumeResult.reason instanceof Error ? volumeResult.reason.message : "Volume failed");
        }

        if (resourcesResult.status === "fulfilled") {
          setResources(resourcesResult.value);
        } else {
          nextErrors.push(resourcesResult.reason instanceof Error ? resourcesResult.reason.message : "Resources failed");
        }

        setErrors(nextErrors);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const hasData = Boolean(overview || volume.length || resources);

  return (
    <div>
      <PageHeader
        title="Overview"
        description="Monitor email processing and webhook delivery at a glance."
      />
      {errors.length > 0 ? (
        <div className="card mb-4 border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-100">
          <p className="text-sm font-semibold">Some dashboard data could not load</p>
          <ul className="mt-2 space-y-1 text-xs">
            {errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {!hasData && !loading ? (
        <div className="card mb-4 border-red-200 bg-red-50 text-red-900 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-100">
          <p className="text-sm font-semibold">Dashboard data is unavailable</p>
          <p className="mt-1 text-xs">The analytics API is not returning any data yet.</p>
        </div>
      ) : null}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Emails (7d)"
          value={overview?.emails_processed_period ?? (loading ? "Loading" : "-")}
          hint={`${overview?.emails_processed_total ?? 0} all time`}
        />
        <StatCard
          label="Delivery success"
          value={overview ? `${overview.success_rate}%` : loading ? "Loading" : "-"}
          tone="success"
        />
        <StatCard
          label="Delivery failures"
          value={overview ? `${overview.failure_rate}%` : loading ? "Loading" : "-"}
          tone={overview && overview.failure_rate > 0 ? "danger" : "default"}
        />
        <StatCard
          label="Avg latency"
          value={
            overview?.avg_processing_latency_ms != null
              ? `${overview.avg_processing_latency_ms} ms`
              : loading
                ? "Loading"
                : "-"
          }
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="card lg:col-span-2">
          <p className="label mb-3">Email volume (14 days)</p>
          {volume.length === 0 && loading ? (
            <p className="text-xs text-ink-muted">Loading chart data...</p>
          ) : volume.length === 0 ? (
            <p className="text-xs text-ink-muted">No volume data yet.</p>
          ) : (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={volume}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#cbd5e1" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} width={28} />
                  <Tooltip contentStyle={{ fontSize: 11 }} />
                  <Bar dataKey="count" fill="#2563eb" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
        <div className="card space-y-3">
          <p className="label">Resources</p>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-muted">Mailboxes</span>
            <span className="font-medium">{resources?.mailboxes ?? (loading ? "Loading" : "-")}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-muted">Enabled mailboxes</span>
            <span className="font-medium">
              {resources?.enabled_mailboxes ?? (loading ? "Loading" : "-")}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-muted">Webhooks</span>
            <span className="font-medium">{resources?.webhooks ?? (loading ? "Loading" : "-")}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-muted">Failed events (7d)</span>
            <span className={`font-medium ${overview && overview.events_failed > 0 ? 'text-red-500' : ''}`}>{overview?.events_failed ?? (loading ? "Loading" : "-")}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-muted">Pending deliveries</span>
            <span className={`font-medium ${overview && overview.webhook_deliveries_pending > 0 ? 'text-amber-500' : ''}`}>{overview?.webhook_deliveries_pending ?? (loading ? "Loading" : "-")}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-ink-muted">Failed deliveries</span>
            <span className={`font-medium ${overview && overview.webhook_deliveries_failed > 0 ? 'text-red-500' : ''}`}>{overview?.webhook_deliveries_failed ?? (loading ? "Loading" : "-")}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
