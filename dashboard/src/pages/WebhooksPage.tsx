import { FormEvent, useEffect, useState } from "react";
import { PageHeader, StatusBadge } from "../components/ui";
import { apiFetch } from "../lib/api";

type Webhook = {
  id: string;
  url: string;
  name: string | null;
  secret_prefix: string;
  is_enabled: boolean;
};

export function WebhooksPage() {
  const [items, setItems] = useState<Webhook[]>([]);
  const [secret, setSecret] = useState<string | null>(null);
  const [form, setForm] = useState({ url: "", name: "" });
  const [showForm, setShowForm] = useState(false);

  async function load() {
    setItems(await apiFetch<Webhook[]>("/api/v1/webhooks"));
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    const created = await apiFetch<Webhook & { secret: string }>("/api/v1/webhooks", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setSecret(created.secret);
    setShowForm(false);
    setForm({ url: "", name: "" });
    load();
  }

  async function testWebhook(id: string) {
    const result = await apiFetch<{ success: boolean; http_status_code: number }>(
      `/api/v1/webhooks/${id}/test`,
      { method: "POST" },
    );
    alert(result.success ? "Test delivery succeeded" : "Test delivery failed");
  }

  return (
    <div>
      <PageHeader
        title="Webhooks"
        description="Endpoints that receive signed email.received events."
        action={
          <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
            Add webhook
          </button>
        }
      />
      {secret ? (
        <div className="card mb-4 border-amber-200 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/30">
          <p className="text-xs font-medium text-amber-900 dark:text-amber-100">
            Signing secret (copy now)
          </p>
          <code className="mt-2 block break-all text-2xs text-amber-950 dark:text-amber-100">
            {secret}
          </code>
          <button type="button" className="btn-secondary mt-3" onClick={() => setSecret(null)}>
            Dismiss
          </button>
        </div>
      ) : null}
      {showForm ? (
        <form className="card mb-4 grid gap-3 md:grid-cols-2" onSubmit={onCreate}>
          <div>
            <label className="label">URL</label>
            <input
              className="input"
              required
              placeholder="https://example.com/webhooks/email"
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Name</label>
            <input
              className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div className="md:col-span-2">
            <button type="submit" className="btn-primary">
              Create webhook
            </button>
          </div>
        </form>
      ) : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>URL</th>
              <th>Secret</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((webhook) => (
              <tr key={webhook.id}>
                <td>{webhook.name || "-"}</td>
                <td className="max-w-xs truncate text-ink-muted">{webhook.url}</td>
                <td className="font-mono text-2xs">{webhook.secret_prefix}...</td>
                <td>
                  <StatusBadge status={webhook.is_enabled ? "healthy" : "disabled"} />
                </td>
                <td>
                  <button type="button" className="btn-secondary" onClick={() => testWebhook(webhook.id)}>
                    Test
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
