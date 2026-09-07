'use client';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { infrastructureService } from '@/services/infrastructure';
import { toast } from '@/components/ui/toast';
import {
  EmptyPanel,
  ErrorPanel,
  formatDate,
  StatusPill,
  TableSkeleton,
} from '@/features/infrastructure/shared';

const limit = 10;
const statuses = ['', 'pending', 'delivered', 'failed', 'dead_lettered'];
const POLL_INTERVAL = 60_000;

export default function EventsPage() {
  const [mailboxId, setMailboxId] = useState('');
  const [status, setStatus] = useState('');
  const [offset, setOffset] = useState(0);

  const mailboxes = useQuery({
    queryKey: ['mailboxes'],
    queryFn: infrastructureService.listMailboxes,
    refetchInterval: POLL_INTERVAL,
  });
  const events = useQuery({
    queryKey: ['events', mailboxId, status, offset],
    queryFn: () =>
      infrastructureService.listEvents({
        mailboxId: mailboxId || undefined,
        status: status || undefined,
        limit,
        offset,
      }),
    refetchInterval: POLL_INTERVAL,
  });
  const retry = useMutation({
    mutationFn: infrastructureService.retryEvent,
    onSuccess: () => {
      events.refetch();
      toast.add({ title: 'Event queued for retry', type: 'success' });
    },
    onError: (error) =>
      toast.add({ title: 'Could not queue retry', description: error.message, type: 'error' }),
  });
  const updateFilter = (setter: (value: string) => void, value: string | null) => {
    setter(value ?? '');
    setOffset(0);
  };
  return (
    <main className="bg-background flex flex-1 flex-col px-4 py-4 md:px-6 md:py-5">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header>
          <p className="text-primary text-xs font-semibold tracking-[.14em] uppercase">
            Processing ledger
          </p>
          <h1 className="text-xl font-semibold tracking-tight">Events</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            A paged operational stream of email processing outcomes.
          </p>
        </header>
        <section className="bg-card flex flex-col gap-2 rounded-lg border p-3 sm:flex-row sm:items-center">
          <Select
            value={mailboxId || null}
            onValueChange={(value) => updateFilter(setMailboxId, value)}
            items={[
              { value: '', label: 'All mailboxes' },
              ...(mailboxes.data ?? []).map((mailbox) => ({
                value: mailbox.id,
                label: mailbox.email_address,
              })),
            ]}
          >
            <SelectTrigger className="w-full sm:w-64">
              <SelectValue placeholder="All mailboxes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All mailboxes</SelectItem>
              {mailboxes.data?.map((mailbox) => (
                <SelectItem key={mailbox.id} value={mailbox.id}>
                  {mailbox.email_address}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select
            value={status || null}
            onValueChange={(value) => updateFilter(setStatus, value)}
            items={statuses.map((item) => ({ value: item, label: item || 'All statuses' }))}
          >
            <SelectTrigger className="w-full sm:w-48">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              {statuses.map((item) => (
                <SelectItem key={item} value={item}>
                  {item ? item.replace('_', ' ') : 'All statuses'}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-muted-foreground text-xs sm:ml-auto">
            {events.data ? `${events.data.total} total records` : 'Loading stream…'}
          </span>
        </section>
        {events.isPending ? (
          <TableSkeleton rows={10} />
        ) : events.isError ? (
          <ErrorPanel message="Event stream could not be loaded." retry={() => events.refetch()} />
        ) : !events.data?.items.length ? (
          <EmptyPanel
            title="No events match this view"
            detail="Adjust the filters or connect a mailbox to begin processing messages."
          />
        ) : (
          <div className="border-border bg-card overflow-hidden rounded-lg border">
            <div className="overflow-x-auto">
              <table className="w-full min-w-240 text-left text-sm">
                <thead className="bg-muted/30 text-muted-foreground border-b text-xs tracking-wide uppercase">
                  <tr>
                    <th className="px-4 py-3">Message</th>
                    <th className="px-4 py-3">Sender → recipients</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Timing</th>
                    <th className="px-4 py-3">Attempts</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {events.data.items.map((event) => (
                    <tr
                      className="border-border/70 border-b align-top last:border-0"
                      key={event.id}
                    >
                      <td className="max-w-80 px-4 py-3">
                        <p className="truncate font-medium">{event.subject || '(no subject)'}</p>
                        <p
                          className="text-muted-foreground truncate font-mono text-xs"
                          title={event.message_id}
                        >
                          {event.message_id}
                        </p>
                      </td>
                      <td className="max-w-72 px-4 py-3">
                        <p className="truncate">{event.sender_name || event.sender_email}</p>
                        <p className="text-muted-foreground truncate text-xs">
                          {event.sender_email} → {event.recipients.join(', ') || '—'}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <StatusPill status={event.status} />
                        {event.error_message && (
                          <p
                            className="text-destructive mt-1 max-w-44 truncate text-xs"
                            title={event.error_message}
                          >
                            {event.error_message}
                          </p>
                        )}
                      </td>
                      <td className="text-muted-foreground px-4 py-3 text-xs">
                        <p>Received {formatDate(event.received_at)}</p>
                        <p>Processed {formatDate(event.processed_at)}</p>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">{event.attempt_count}</td>
                      <td className="px-4 py-3 text-right">
                        {['failed', 'pending'].includes(event.status) && (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={retry.isPending}
                            onClick={() => retry.mutate(event.id)}
                          >
                            <RotateCcw
                              className={
                                retry.isPending && retry.variables === event.id
                                  ? 'animate-spin'
                                  : ''
                              }
                            />
                            {retry.isPending && retry.variables === event.id
                              ? 'Retrying...'
                              : 'Retry'}
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="bg-muted/20 flex items-center justify-between border-t px-4 py-3">
              <span className="text-muted-foreground text-xs">Offset {offset}</span>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={offset === 0}
                  onClick={() => setOffset((value) => Math.max(0, value - limit))}
                >
                  <ChevronLeft />
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={offset + limit >= events.data.total}
                  onClick={() => setOffset((value) => value + limit)}
                >
                  Next
                  <ChevronRight />
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
