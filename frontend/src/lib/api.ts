const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

function getAuthToken() {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem('mydesk-auth-token');
}

function getErrorMessage(response: Response, fallback: string) {
  return response.text().then((text) => {
    if (!text) return fallback;
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed === 'string') return parsed;
      if (parsed?.detail) return parsed.detail;
      if (parsed?.message) return parsed.message;
    } catch {
      // ignore and fall back to raw text
    }
    return text;
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
    credentials: 'include',
    ...init,
  });

  if (!response.ok) {
    const message = await getErrorMessage(response, 'Request failed');
    throw new Error(message);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json() as Promise<T>;
  }
  return response.text() as unknown as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>('/health'),
  logout: () => request<{ status: string }>('/auth/logout', { method: 'POST' }),
  chat: (payload: { message: string; user_id?: string }) => request<{ reply: string; intent: string; result?: Record<string, unknown> | null }>('/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  getCalendarEvents: () => request<any[]>('/calendar'),
  createCalendarEvent: (payload: any) => request<any>('/calendar', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  updateCalendarEvent: (id: string, payload: any) => request<any>(`/calendar/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  }),
  deleteCalendarEvent: (id: string) => request<any>(`/calendar/${id}`, {
    method: 'DELETE',
  }),
  getTasks: () => request<any[]>('/tasks'),
  startGoogleOAuth: (next?: string) => request<{ authorization_url?: string; status?: string; state?: string }>(`/oauth/google${next ? `?next=${encodeURIComponent(next)}` : ''}`),
  getGoogleStatus: () => request<{ connected?: boolean; configured?: boolean; email?: string }>('/oauth/google/status'),
  createTask: (payload: any) => request<any>('/tasks', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  updateTask: (id: string, payload: any) => request<any>(`/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  }),
  deleteTask: (id: string) => request<any>(`/tasks/${id}`, {
    method: 'DELETE',
  }),
};
