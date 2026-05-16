import { client } from './client';

export interface SyncStatus {
  source: string;
  last_sync_at: string | null;
  status: string;
  records_added: number;
  records_updated: number;
  records_failed: number;
}

export async function getSyncStatus(): Promise<SyncStatus[]> {
  const { data } = await client.get('/ingest/status');
  return data;
}
