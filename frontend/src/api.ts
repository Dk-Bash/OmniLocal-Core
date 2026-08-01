// Cliente de la API local de OmniLocal-Core.
// Todas las llamadas van a rutas relativas /api/... que resuelven contra el
// propio backend FastAPI (mismo origen en producción, proxy de Vite en dev).
// No hay ninguna llamada a un dominio externo en este archivo.

export interface Session {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationRow {
  id: number;
  user_input: string;
  assistant_response: string;
  created_at: string;
}

export interface AskResponse {
  answer: string;
  source: 'memoria_local' | 'modelo_ia' | 'sin_modelo' | 'vacio';
  used_model: boolean;
  conversation_id: number | null;
}

export interface Fact {
  id: number;
  category: string;
  detail: string;
  confidence: number;
}

export interface StatusResponse {
  engine: { name: string; version: string; running: boolean; status: string };
  ollama: { available: boolean; host: string; model: string; model_downloaded: boolean };
  memory_count: number;
  feedback: { useful: number; not_useful: number };
}

export interface SourceEntry {
  id: number;
  path: string;
  file_count: number;
  added_at: string;
  last_indexed_at: string | null;
}

export interface IngestionResult {
  path: string;
  files_found: number;
  files_indexed: number;
  errors: string[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Error ${res.status} en ${path}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getStatus: () => request<StatusResponse>('/api/status'),

  listSessions: () => request<Session[]>('/api/sessions'),
  createSession: (title?: string) =>
    request<Session>('/api/sessions', { method: 'POST', body: JSON.stringify({ title }) }),
  renameSession: (id: number, title: string) =>
    request<Session>(`/api/sessions/${id}`, { method: 'PATCH', body: JSON.stringify({ title }) }),
  deleteSession: (id: number) => request<{ deleted: boolean }>(`/api/sessions/${id}`, { method: 'DELETE' }),

  getMessages: (sessionId: number) => request<ConversationRow[]>(`/api/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: number, content: string) =>
    request<AskResponse>(`/api/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    }),

  listFacts: () => request<Fact[]>('/api/facts'),
  addFact: (content: string, importance = 0.7) =>
    request<Fact>('/api/facts', { method: 'POST', body: JSON.stringify({ content, importance }) }),

  sendFeedback: (conversationId: number, useful: boolean) =>
    request<{ ok: boolean }>('/api/feedback', {
      method: 'POST',
      body: JSON.stringify({ conversation_id: conversationId, useful }),
    }),

  listSources: () => request<SourceEntry[]>('/api/sources'),
  addSource: (path: string) =>
    request<IngestionResult>('/api/sources', { method: 'POST', body: JSON.stringify({ path }) }),
  deleteSource: (id: number) => request<{ deleted: boolean }>(`/api/sources/${id}`, { method: 'DELETE' }),
};
