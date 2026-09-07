'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Loader2, Plus, PlugZap, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { infrastructureService } from '@/services/infrastructure';
import type { MailboxInput } from '@/services/Types';
import { toast } from '@/components/ui/toast';
import {
  EmptyPanel,
  ErrorPanel,
  formatDate,
  StatusPill,
  TableSkeleton,
} from '@/features/infrastructure/shared';

const initial: MailboxInput = {
  email_address: '',
  password: '',
  imap_host: '',
  imap_port: 993,
  imap_username: null,
  is_enabled: true,
};
export default function MailboxesPage() {
  const client = useQueryClient();
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState(initial);
  const query = useQuery({ queryKey: ['mailboxes'], queryFn: infrastructureService.listMailboxes });
  const invalidate = () => client.invalidateQueries({ queryKey: ['mailboxes'] });
  const create = useMutation({
    mutationFn: infrastructureService.createMailbox,
    onSuccess: () => {
      invalidate();
      setAdding(false);
      setForm(initial);
      toast.add({ title: 'Mailbox registered', type: 'success' });
    },
    onError: (error) =>
      toast.add({ title: 'Could not register mailbox', description: error.message, type: 'error' }),
  });
  const update = useMutation({
    mutationFn: ({ id, is_enabled }: { id: string; is_enabled: boolean }) =>
      infrastructureService.updateMailbox(id, { is_enabled }),
    onSuccess: invalidate,
    onError: (error) =>
      toast.add({ title: 'Mailbox update failed', description: error.message, type: 'error' }),
  });
  const remove = useMutation({
    mutationFn: infrastructureService.deleteMailbox,
    onSuccess: () => {
      invalidate();
      toast.add({ title: 'Mailbox removed', type: 'success' });
    },
    onError: (error) =>
      toast.add({ title: 'Mailbox removal failed', description: error.message, type: 'error' }),
  });
  const test = useMutation({
    mutationFn: infrastructureService.testMailbox,
    onSuccess: (data) => {
      invalidate();
      toast.add({
        title: data.success ? 'Connection successful' : 'Connection failed',
        description: data.message,
        type: data.success ? 'success' : 'error',
      });
    },
    onError: (error) =>
      toast.add({ title: 'Connection test failed', description: error.message, type: 'error' }),
  });
  return (
    <main className="bg-background flex flex-1 flex-col px-4 py-4 md:px-6 md:py-5">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-5">
        <header className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <p className="text-primary text-xs font-semibold tracking-[.14em] uppercase">
              Ingestion endpoints
            </p>
            <h1 className="text-xl font-semibold tracking-tight">Mailboxes</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              IMAP sources monitored by the processing pipeline.
            </p>
          </div>
          <Button onClick={() => setAdding((value) => !value)}>
            <Plus />
            {adding ? 'Close setup' : 'Register mailbox'}
          </Button>
        </header>
        {adding && (
          <Card>
            <CardContent className="p-4">
              <form
                className="grid gap-3 md:grid-cols-2 xl:grid-cols-3"
                onSubmit={(event) => {
                  event.preventDefault();
                  create.mutate({ ...form, imap_username: form.imap_username || null });
                }}
              >
                <FormField label="Mailbox address">
                  <Input
                    required
                    type="email"
                    value={form.email_address}
                    onChange={(e) => setForm({ ...form, email_address: e.target.value })}
                  />
                </FormField>
                <FormField label="IMAP host">
                  <Input
                    required
                    placeholder="imap.example.com"
                    value={form.imap_host}
                    onChange={(e) => setForm({ ...form, imap_host: e.target.value })}
                  />
                </FormField>
                <FormField label="IMAP port">
                  <Input
                    required
                    min="1"
                    max="65535"
                    type="number"
                    value={form.imap_port}
                    onChange={(e) => setForm({ ...form, imap_port: Number(e.target.value) })}
                  />
                </FormField>
                <FormField label="IMAP username (optional)">
                  <Input
                    type="email"
                    value={form.imap_username ?? ''}
                    onChange={(e) => setForm({ ...form, imap_username: e.target.value })}
                  />
                </FormField>
                <FormField label="Password">
                  <Input
                    required
                    type="password"
                    autoComplete="new-password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                  />
                </FormField>
                <label className="flex items-center gap-2 self-end pb-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.is_enabled}
                    onChange={(e) => setForm({ ...form, is_enabled: e.target.checked })}
                  />{' '}
                  Enable monitoring
                </label>
                <div className="md:col-span-2 xl:col-span-3">
                  <Button disabled={create.isPending} type="submit">
                    {create.isPending && <Loader2 className="animate-spin" />}Register mailbox
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
        {query.isPending ? (
          <TableSkeleton />
        ) : query.isError ? (
          <ErrorPanel
            message="Mailbox inventory could not be loaded."
            retry={() => query.refetch()}
          />
        ) : !query.data?.length ? (
          <EmptyPanel
            title="No mailboxes connected"
            detail="Register an IMAP mailbox to begin ingesting email events."
          />
        ) : (
          <div className="border-border bg-card overflow-hidden rounded-lg border">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead className="bg-muted/30 text-muted-foreground border-b text-xs tracking-wide uppercase">
                  <tr>
                    <th className="px-4 py-3 font-medium">Mailbox</th>
                    <th className="px-4 py-3 font-medium">Endpoint</th>
                    <th className="px-4 py-3 font-medium">Health</th>
                    <th className="px-4 py-3 font-medium">Last sync</th>
                    <th className="px-4 py-3 text-right font-medium">Controls</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.map((mailbox) => (
                    <tr className="border-border/70 border-b last:border-0" key={mailbox.id}>
                      <td className="px-4 py-3">
                        <p className="font-medium">{mailbox.email_address}</p>
                        <p className="text-muted-foreground font-mono text-xs">
                          {mailbox.imap_username}
                        </p>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs">
                        {mailbox.imap_host}:{mailbox.imap_port}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col items-start gap-1">
                          <StatusPill status={mailbox.health_status} />
                          {mailbox.last_error_message && (
                            <span
                              className="text-destructive max-w-44 truncate text-xs"
                              title={mailbox.last_error_message}
                            >
                              {mailbox.last_error_message}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-muted-foreground px-4 py-3 text-xs">
                        {formatDate(mailbox.last_sync_at)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex justify-end gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={test.isPending}
                            onClick={() => test.mutate(mailbox.id)}
                          >
                            <PlugZap />
                            Test
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={update.isPending}
                            onClick={() =>
                              update.mutate({ id: mailbox.id, is_enabled: !mailbox.is_enabled })
                            }
                          >
                            {mailbox.is_enabled ? 'Pause' : 'Enable'}
                          </Button>
                          <Button
                            size="icon-sm"
                            variant="destructive"
                            aria-label="Remove mailbox"
                            disabled={remove.isPending}
                            onClick={() => remove.mutate(mailbox.id)}
                          >
                            <Trash2 />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
function FormField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Field>
      <FieldLabel>{label}</FieldLabel>
      {children}
    </Field>
  );
}
