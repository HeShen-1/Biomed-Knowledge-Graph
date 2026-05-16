import { client } from './client';

export interface SearchResult {
  id: string;
  type: string;
  label: string;
  description?: string;
  relevance: number;
}

export interface Suggestion {
  id: string;
  type: string;
  label: string;
}

export async function searchEntities(q: string, type?: string, limit = 20): Promise<SearchResult[]> {
  const { data } = await client.get('/search', { params: { q, type, limit } });
  return data;
}

export async function getSuggestions(q: string): Promise<Suggestion[]> {
  const { data } = await client.get('/search/suggest', { params: { q } });
  return data;
}
