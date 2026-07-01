const BASE = '/api';
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (res.status === 204) return undefined as T;
  if (!res.ok) { const err = await res.text(); throw new Error(err || res.statusText); }
  return res.json();
}
export const api = {
  getProjects: () => request<import('../types').Project[]>('/projects'),
  createProject: (data: { name: string; source_lang: string; target_lang: string }) =>
    request<import('../types').Project>('/projects', { method: 'POST', body: JSON.stringify(data) }),
  deleteProject: (id: number) => request<void>('/projects/' + id, { method: 'DELETE' }),
  getDocuments: (projectId: number) => request<import('../types').Document[]>('/projects/' + projectId + '/documents'),
  uploadDocument: (projectId: number, file: File) => {
    const form = new FormData(); form.append('file', file);
    return fetch(BASE + '/projects/' + projectId + '/documents', { method: 'POST', body: form }).then(r => r.json()) as Promise<import('../types').Document>;
  },
  deleteDocument: (docId: number) => request<void>('/documents/' + docId, { method: 'DELETE' }),
  getSegments: (docId: number) => request<import('../types').Segment[]>('/documents/' + docId),
  updateSegment: (segId: number, data: { target_text?: string; status?: string }) =>
    request<import('../types').Segment>('/segments/' + segId, { method: 'PUT', body: JSON.stringify(data) }),
  getMatches: (segId: number) => request<{ matches: import('../types').TMMatch[] }>('/segments/' + segId + '/matches'),
  getTerms: (segId: number) => request<import('../types').GlossaryTerm[]>('/segments/' + segId + '/terms'),
  importTMX: (file: File) => {
    const form = new FormData(); form.append('file', file);
    return fetch(BASE + '/tm/import', { method: 'POST', body: form }).then(r => r.json());
  },
  exportTMX: () => fetch(BASE + '/tm/export').then(r => r.blob()),
  preTranslate: (projectId: number) =>
    request<{ translated: number; total_segments: number; input_tokens: number; output_tokens: number; total_tokens: number; duration_ms: number }>(
      '/projects/' + projectId + '/pre-translate', { method: 'POST' }
    ),
  getTokenStats: (projectId: number) =>
    request<{ project_id: number; total_calls: number; total_input_tokens: number; total_output_tokens: number; total_tokens: number; total_duration_ms: number }>(
      '/projects/' + projectId + '/token-stats'
    ),
  clearTM: () => request<void>('/tm', { method: 'DELETE' }),
  getGlossary: () => request<import('../types').GlossaryEntry[]>('/glossary'),
  createGlossaryEntry: (data: { source_lang: string; target_lang: string; source_term: string; target_term: string; note?: string | null }) =>
    request<import('../types').GlossaryEntry>('/glossary', { method: 'POST', body: JSON.stringify(data) }),
  updateGlossaryEntry: (id: number, data: { source_lang: string; target_lang: string; source_term: string; target_term: string; note?: string | null }) =>
    request<import('../types').GlossaryEntry>('/glossary/' + id, { method: 'PUT', body: JSON.stringify(data) }),
  deleteGlossaryEntry: (id: number) => request<void>('/glossary/' + id, { method: 'DELETE' }),
};
