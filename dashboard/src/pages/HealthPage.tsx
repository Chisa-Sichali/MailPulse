import { useEffect, useState } from "react";
import { PageHeader, StatusBadge } from "../components/ui";
import { API_URL } from "../lib/api";

type SystemHealth = {
  status: string;
  version: string;
  environment: string;
  checks: Record<string, string>;
  deliveries: Record<string, number>;
};

export function HealthPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health/system`)
      .then((r) => r.json())
      .then(setHealth);
  }, []);

  return (
    <div>
      <PageHeader title="System health" description="Infrastructure and queue status." />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <p className="label">Overall</p>
          <div className="mt-2">
            <StatusBadge status={health?.status || "unknown"} />
          </div>
        </div>
        <div className="card">
          <p className="label">Version</p>
          <p className="mt-2 text-xs font-medium">{health?.version ?? "-"}</p>
        </div>
        <div className="card">
          <p className="label">Environment</p>
          <p className="mt-2 text-xs font-medium">{health?.environment ?? "-"}</p>
        </div>
        <div className="card">
          <p className="label">Pending deliveries</p>
          <p className="mt-2 text-xs font-medium">{health?.deliveries?.pending ?? "-"}</p>
        </div>
      </div>
      <div className="card mt-4">
        <p className="label mb-3">Service checks</p>
        <div className="space-y-2">
          {health
            ? Object.entries(health.checks).map(([name, value]) => (
                <div key={name} className="flex items-center justify-between text-xs">
                  <span className="capitalize text-ink-muted">{name}</span>
                  <StatusBadge
                    status={value === "connected" || value === "ok" ? "healthy" : "error"}
                  />
                </div>
              ))
            : null}
        </div>
      </div>
    </div>
  );
}
