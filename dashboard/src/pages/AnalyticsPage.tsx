import { useEffect, useState } from "react";
import { PageHeader } from "../components/ui";
import { apiFetch } from "../lib/api";

type Sender = { sender_email: string; sender_name: string; count: number };
type WebhookPerf = {
  name: string | null;
  url: string;
  total_deliveries: number;
  success_rate: number;
};

export function AnalyticsPage() {
  const [senders, setSenders] = useState<Sender[]>([]);
  const [webhooks, setWebhooks] = useState<WebhookPerf[]>([]);
  const [loading, setLoading] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setErrors([]);

    Promise.allSettled([
      apiFetch<Sender[]>("/api/v1/analytics/top-senders?days=30&limit=10"),
      apiFetch<WebhookPerf[]>("/api/v1/analytics/webhooks?days=30"),
    ])
      .then(([sendersResult, webhooksResult]) => {
        if (!active) return;

        const nextErrors: string[] = [];

        if (sendersResult.status === "fulfilled") {
          setSenders(sendersResult.value);
        } else {
          nextErrors.push(
            sendersResult.reason instanceof Error ? sendersResult.reason.message : "Top senders failed",
          );
        }

        if (webhooksResult.status === "fulfilled") {
          setWebhooks(webhooksResult.value);
        } else {
          nextErrors.push(
            webhooksResult.reason instanceof Error
              ? webhooksResult.reason.message
              : "Webhook performance failed",
          );
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

  return (
    <div>
      <PageHeader title="Analytics" description="Sender trends and webhook performance." />
      {errors.length > 0 ? (
        <div className="card mb-4 border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-100">
          <p className="text-sm font-semibold">Some analytics data could not load</p>
          <ul className="mt-2 space-y-1 text-xs">
            {errors.map((message) => (
              <li key={message}>{message}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <p className="label mb-3">Top senders (30d)</p>
          <div className="space-y-2">
            {senders.length === 0 ? (
              <p className="text-xs text-ink-muted">
                {loading ? "Loading sender activity..." : "No data yet."}
              </p>
            ) : (
              senders.map((sender) => (
                <div key={sender.sender_email} className="flex items-center justify-between text-xs">
                  <div>
                    <p className="font-medium">{sender.sender_name || sender.sender_email}</p>
                    <p className="text-2xs text-ink-muted">{sender.sender_email}</p>
                  </div>
                  <span className="font-semibold tabular-nums">{sender.count}</span>
                </div>
              ))
            )}
          </div>
        </div>
        <div className="card">
          <p className="label mb-3">Webhook performance (30d)</p>
          <div className="space-y-2">
            {webhooks.length === 0 ? (
              <p className="text-xs text-ink-muted">
                {loading ? "Loading delivery activity..." : "No deliveries yet."}
              </p>
            ) : (
              webhooks.map((webhook) => (
                <div
                  key={webhook.url}
                  className="rounded-md border border-surface-border p-2.5 dark:border-slate-700"
                >
                  <p className="text-xs font-medium">{webhook.name || webhook.url}</p>
                  <div className="mt-1 flex items-center justify-between text-2xs text-ink-muted">
                    <span>{webhook.total_deliveries} deliveries</span>
                    <span className="font-semibold text-emerald-700 dark:text-emerald-300">
                      {webhook.success_rate}% success
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
