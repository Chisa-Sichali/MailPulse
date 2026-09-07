import { apiFetch } from '@/services/api-client';
import { extractErrorMessage } from '@/utils/auth-utils';
import type {
  ConnectionTest,
  EmailEvent,
  EmailEventList,
  Mailbox,
  MailboxInput,
  MailboxList,
  MailboxUpdate,
  Webhook,
  WebhookCreated,
  WebhookDeliveryList,
  WebhookInput,
  WebhookList,
  WebhookSecret,
  WebhookTest,
  WebhookUpdate,
} from '@/services/Types/infrastructure-types';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) throw new Error(await extractErrorMessage(response));
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
}
const json = (method: string, body?: unknown): RequestInit => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
});

export const infrastructureService = {
  listMailboxes: async () => {
    const response = await request<MailboxList | Mailbox[]>('/mailboxes?limit=100&offset=0');
    return Array.isArray(response) ? response : response.items;
  },
  listMailboxesPage: (limit = 50, offset = 0) =>
    request<MailboxList>(`/mailboxes?limit=${limit}&offset=${offset}`),
  createMailbox: (body: MailboxInput) => request<Mailbox>('/mailboxes', json('POST', body)),
  updateMailbox: (id: string, body: MailboxUpdate) =>
    request<Mailbox>(`/mailboxes/${id}`, json('PATCH', body)),
  deleteMailbox: (id: string) => request<void>(`/mailboxes/${id}`, json('DELETE')),
  testMailbox: (id: string) =>
    request<ConnectionTest>(`/mailboxes/${id}/test-connection`, json('POST')),
  listWebhooks: async () => {
    const response = await request<WebhookList | Webhook[]>('/webhooks?limit=100&offset=0');
    return Array.isArray(response) ? response : response.items;
  },
  listWebhooksPage: (limit = 50, offset = 0) =>
    request<WebhookList>(`/webhooks?limit=${limit}&offset=${offset}`),
  createWebhook: (body: WebhookInput) => request<WebhookCreated>('/webhooks', json('POST', body)),
  updateWebhook: (id: string, body: WebhookUpdate) =>
    request<Webhook>(`/webhooks/${id}`, json('PATCH', body)),
  deleteWebhook: (id: string) => request<void>(`/webhooks/${id}`, json('DELETE')),
  rotateWebhookSecret: (id: string) =>
    request<WebhookSecret>(`/webhooks/${id}/rotate-secret`, json('POST')),
  testWebhook: (id: string) => request<WebhookTest>(`/webhooks/${id}/test`, json('POST')),
  listDeliveries: (id: string, limit: number, offset: number) =>
    request<WebhookDeliveryList>(`/webhooks/${id}/deliveries?limit=${limit}&offset=${offset}`),
  listEvents: (params: { mailboxId?: string; status?: string; limit: number; offset: number }) => {
    const query = new URLSearchParams({
      limit: String(params.limit),
      offset: String(params.offset),
    });
    if (params.mailboxId) query.set('mailbox_id', params.mailboxId);
    if (params.status) query.set('status', params.status);
    return request<EmailEventList>(`/events?${query}`);
  },
  getEvent: (id: string) => request<EmailEvent>(`/events/${id}`),
  retryEvent: (id: string) => request<{ status: string }>(`/events/${id}/retry`, json('POST')),
};
