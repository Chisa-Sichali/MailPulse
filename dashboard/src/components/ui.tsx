type StatCardProps = {
  label: string;
  value: string | number;
  hint?: string;
  tone?: "default" | "success" | "danger";
};

export function StatCard({ label, value, hint, tone = "default" }: StatCardProps) {
  const toneClass =
    tone === "success"
      ? "text-emerald-600 dark:text-emerald-400"
      : tone === "danger"
        ? "text-red-600 dark:text-red-400"
        : "text-ink";

  return (
    <div className="card">
      <p className="label">{label}</p>
      <p className={`mt-1 text-lg font-semibold tracking-tight ${toneClass}`}>{value}</p>
      {hint ? <p className="mt-1 text-2xs text-ink-faint">{hint}</p> : null}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-5 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-sm font-semibold tracking-tight text-ink">{title}</h1>
        {description ? (
          <p className="mt-0.5 text-xs text-ink-muted">{description}</p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  let classes = "badge bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300";
  if (["healthy", "processed", "delivered", "connected", "ok"].includes(normalized)) {
    classes = "badge bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300";
  } else if (["failed", "error", "dead_lettered"].includes(normalized)) {
    classes = "badge bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-300";
  } else if (["pending", "processing", "unknown", "degraded"].includes(normalized)) {
    classes = "badge bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300";
  }
  return <span className={classes}>{status}</span>;
}
