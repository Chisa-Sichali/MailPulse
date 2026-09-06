'use client';

import { AlertCircle, CheckCircle2, Clock3, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

export function StatusPill({ status }: { status: string }) {
  const value = status.toLowerCase();
  const good = ['healthy', 'delivered', 'processed', 'enabled'].includes(value);
  const bad = ['failed', 'error', 'dead_lettered', 'disabled'].includes(value);
  const Icon = good ? CheckCircle2 : bad ? XCircle : value === 'degraded' ? AlertCircle : Clock3;
  return <span className={cn('inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-medium', good && 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400', bad && 'bg-destructive/10 text-destructive', !good && !bad && 'bg-amber-500/10 text-amber-700 dark:text-amber-400')}><Icon className="size-3" />{status.replace('_', ' ')}</span>;
}
export function ErrorPanel({ message, retry }: { message: string; retry?: () => void }) { return <div className="flex flex-col items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive"><span>{message}</span>{retry && <Button size="sm" variant="outline" onClick={retry}>Try again</Button>}</div>; }
export function EmptyPanel({ title, detail }: { title: string; detail: string }) { return <div className="flex min-h-48 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-muted/20 p-6 text-center"><p className="font-medium">{title}</p><p className="mt-1 max-w-sm text-sm text-muted-foreground">{detail}</p></div>; }
export function TableSkeleton({ rows = 6 }: { rows?: number }) { return <div className="space-y-3 rounded-lg border p-4">{Array.from({ length: rows }, (_, index) => <Skeleton key={index} className="h-10 w-full" />)}</div>; }
export function formatDate(value: string | null) { return value ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value)) : '—'; }
