export interface Mailbox {
  id: string; email_address: string; imap_username: string; imap_host: string; imap_port: number;
  is_enabled: boolean; health_status: string; last_sync_at: string | null; last_error_at: string | null;
  last_error_message: string | null; created_at: string; updated_at: string;
}
export interface MailboxList { items: Mailbox[]; limit: number; offset: number; }
export interface MailboxInput { email_address: string; password: string; imap_host: string; imap_port: number; imap_username?: string | null; is_enabled: boolean; }
export type MailboxUpdate = Partial<MailboxInput>;
export interface ConnectionTest { success: boolean; message: string; health_status: string; mailbox: Mailbox; }

export interface Webhook { id: string; url: string; name: string | null; secret_prefix: string; is_enabled: boolean; event_types: string[]; created_at: string; updated_at: string; }
export interface WebhookList { items: Webhook[]; limit: number; offset: number; }
export interface WebhookInput { url: string; name?: string | null; event_types: string[]; is_enabled: boolean; }
export type WebhookUpdate = Partial<WebhookInput>;
export interface WebhookCreated extends Webhook { secret: string; }
export interface WebhookSecret { secret: string; secret_prefix: string; }
export interface WebhookTest { success: boolean; http_status_code: number; response_body: string; }
export interface WebhookDelivery { id: string; webhook_id: string; email_event_id: string; status: string; attempt_count: number; http_status_code: number | null; response_body: string | null; next_retry_at: string | null; delivered_at: string | null; last_error: string | null; created_at: string; updated_at: string; }
export interface WebhookDeliveryList { items: WebhookDelivery[]; limit: number; offset: number; }

export interface EmailEvent { id: string; mailbox_id: string; message_id: string; imap_uid: string | null; sender_email: string; sender_name: string; recipients: string[]; subject: string; text_body: string; html_body: string; attachments_metadata: Record<string, unknown>[]; in_reply_to: string | null; status: string; error_message: string | null; attempt_count: number; received_at: string | null; processed_at: string | null; created_at: string; updated_at: string; }
export interface EmailEventList { items: EmailEvent[]; limit: number; offset: number; total: number; }
export interface ResourceCounts { mailboxes: number; enabled_mailboxes: number; webhooks: number; }
