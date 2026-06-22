import { FormEvent, useEffect, useState } from "react";
import { PageHeader, StatusBadge } from "../components/ui";
import { apiFetch } from "../lib/api";

type Mailbox = {
  id: string;
  email_address: string;
  imap_host: string;
  is_enabled: boolean;
  health_status: string;
  last_sync_at: string | null;
};

export function MailboxesPage() {
  const [items, setItems] = useState<Mailbox[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    email_address: "",
    password: "",
    imap_host: "imap.gmail.com",
  });

  async function load() {
    setItems(await apiFetch<Mailbox[]>("/api/v1/mailboxes"));
  }

  useEffect(() => {
    load();
  }, []);

  async function onCreate(e: FormEvent) {
    e.preventDefault();
    await apiFetch("/api/v1/mailboxes", {
      method: "POST",
      body: JSON.stringify({ ...form, imap_port: 993 }),
    });
    setShowForm(false);
    setForm({ email_address: "", password: "", imap_host: "imap.gmail.com" });
    load();
  }

  async function testConnection(id: string) {
    await apiFetch(`/api/v1/mailboxes/${id}/test-connection`, { method: "POST" });
    load();
  }

  return (
    <div>
      <PageHeader
        title="Mailboxes"
        description="Manage IMAP inboxes monitored by MailPulse."
        action={
          <button type="button" className="btn-primary" onClick={() => setShowForm(!showForm)}>
            Add mailbox
          </button>
        }
      />
      {showForm ? (
        <form className="card mb-4 grid gap-3 md:grid-cols-3" onSubmit={onCreate}>
          <div>
            <label className="label">Email</label>
            <input
              className="input"
              required
              value={form.email_address}
              onChange={(e) => setForm({ ...form, email_address: e.target.value })}
            />
          </div>
          <div>
            <label className="label">IMAP host</label>
            <input
              className="input"
              required
              value={form.imap_host}
              onChange={(e) => setForm({ ...form, imap_host: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>
          <div className="md:col-span-3">
            <button type="submit" className="btn-primary">
              Save mailbox
            </button>
          </div>
        </form>
      ) : null}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Host</th>
              <th>Status</th>
              <th>Last sync</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {items.map((m) => (
              <tr key={m.id}>
                <td className="font-medium">{m.email_address}</td>
                <td className="text-ink-muted">{m.imap_host}</td>
                <td>
                  <StatusBadge status={m.health_status} />
                </td>
                <td className="text-ink-muted">
                  {m.last_sync_at ? new Date(m.last_sync_at).toLocaleString() : "-"}
                </td>
                <td>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => testConnection(m.id)}
                  >
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
