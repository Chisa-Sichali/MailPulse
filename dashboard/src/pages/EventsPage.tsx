import { useEffect, useState } from "react";
import { PageHeader, StatusBadge } from "../components/ui";
import { apiFetch } from "../lib/api";

type EmailEvent = {
  id: string;
  subject: string;
  sender_email: string;
  status: string;
  created_at: string;
};

type EventListResponse = {
  items: EmailEvent[];
  limit: number;
  offset: number;
};

const PAGE_SIZE = 20;

export function EventsPage() {
  const [items, setItems] = useState<EmailEvent[]>([]);
  const [totalOffset, setTotalOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");

    apiFetch<EventListResponse>(`/api/v1/events?limit=${PAGE_SIZE}&offset=${totalOffset}`)
      .then((res) => {
        if (!active) return;
        setItems(res.items);
        setHasMore(res.items.length === PAGE_SIZE);
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unable to load events");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [totalOffset]);

  return (
    <div>
      <PageHeader
        title="Events"
        description="Recent processed email events."
        action={
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setTotalOffset((current) => Math.max(0, current - PAGE_SIZE))}
              disabled={loading || totalOffset === 0}
            >
              Previous
            </button>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => setTotalOffset((current) => current + PAGE_SIZE)}
              disabled={loading || !hasMore}
            >
              Next
            </button>
          </div>
        }
      />
      {error ? (
        <div className="card mb-4 border-red-200 bg-red-50 text-red-900 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-100">
          <p className="text-sm font-semibold">Events could not be loaded</p>
          <p className="mt-1 text-xs">{error}</p>
        </div>
      ) : null}
      <div className="card mb-3 flex items-center justify-between text-xs text-ink-muted">
        <span>
          Showing events {totalOffset + 1} to {totalOffset + items.length}
        </span>
        <span>{loading ? "Loading..." : hasMore ? "More results available" : "End of results"}</span>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Subject</th>
              <th>Sender</th>
              <th>Status</th>
              <th>Received</th>
            </tr>
          </thead>
          <tbody>
            {items.map((event) => (
              <tr key={event.id}>
                <td className="max-w-xs truncate font-medium">{event.subject || "(no subject)"}</td>
                <td className="text-ink-muted">{event.sender_email}</td>
                <td>
                  <StatusBadge status={event.status} />
                </td>
                <td className="text-ink-muted">{new Date(event.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {items.length === 0 && !loading ? (
              <tr>
                <td className="py-6 text-center text-sm text-ink-muted" colSpan={4}>
                  No events found.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
