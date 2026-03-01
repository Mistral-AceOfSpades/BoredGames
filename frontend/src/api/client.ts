/**
 * API client for the BoredGames backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api';

function getToken(): string | null {
  return localStorage.getItem('bg_token');
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (!headers.Accept) {
    headers.Accept = 'application/json';
  }

  // Only set JSON content type when a JSON string body is sent.
  // (Avoid forcing preflights for body-less GET requests.)
  const hasJsonStringBody = typeof options.body === 'string';
  if (hasJsonStringBody && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  const text = await res.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}

// ---------- Auth ----------

export const api = {
  auth: {
    githubUrl: () => request<{ url: string }>('/auth/github'),
    callback: (code: string, state?: string) => {
      const query = new URLSearchParams({ code });
      if (state) {
        query.set('state', state);
      }
      return request<import('../types').AuthResponse>(`/auth/github/callback?${query.toString()}`);
    },
    me: () => request<import('../types').User>('/auth/me'),
    devToken: () => request<import('../types').AuthResponse>('/auth/dev-token', { method: 'POST' }),
  },

  health: () => request<{ status: string; mistral_configured: boolean }>('/health'),

  // ---------- Games ----------
  games: {
    search: (name: string) =>
      request<import('../types').Game>('/games', {
        method: 'POST',
        body: JSON.stringify({ name }),
      }),
    list: () => request<import('../types').Game[]>('/games'),
    get: (id: string) => request<import('../types').Game>(`/games/${id}`),
    delete: (id: string) => request<{ status: string }>(`/games/${id}`, { method: 'DELETE' }),
    createSession: (gameId: string, players: string[]) =>
      request<import('../types').GameSession>(`/games/${gameId}/sessions`, {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, players }),
      }),
    getSession: (gameId: string, sessionId: string) =>
      request<import('../types').GameSession>(`/games/${gameId}/sessions/${sessionId}`),
  },

  // ---------- OCR ----------
  ocr: {
    upload: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return request<import('../types').Game>('/ocr/upload', {
        method: 'POST',
        body: formData,
      });
    },
    fromUrl: (url: string) =>
      request<import('../types').Game>('/ocr/url', {
        method: 'POST',
        body: JSON.stringify({ url }),
      }),
  },

  // ---------- Explain ----------
  explain: {
    get: (gameId: string, mode: import('../types').ExplanationMode) =>
      request<import('../types').ExplanationResponse>('/explain', {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, mode }),
      }),
    qa: (gameId: string, question: string) =>
      request<import('../types').QAResponse>('/explain/qa', {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, question }),
      }),
  },

  // ---------- House Rules ----------
  houseRules: {
    validate: (gameId: string, description: string) =>
      request<import('../types').HouseRuleValidation>('/houserules/validate', {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, description }),
      }),
    add: (gameId: string, description: string) =>
      request<{ house_rule: import('../types').HouseRule; validation: import('../types').HouseRuleValidation }>('/houserules/add', {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, description }),
      }),
    list: (gameId: string) =>
      request<{ game_id: string; house_rules: import('../types').HouseRule[] }>(`/houserules/${gameId}`),
    delete: (gameId: string, ruleId: string) =>
      request<{ status: string }>(`/houserules/${gameId}/${ruleId}`, { method: 'DELETE' }),
  },

  // ---------- Moderate ----------
  moderate: {
    validateMove: (sessionId: string, player: string, action: string) =>
      request<import('../types').MoveValidation>('/moderate/validate-move', {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId, player, action }),
      }),
    advanceTurn: (sessionId: string) =>
      request<{ session_id: string; current_turn: number; current_player: string; round: number; guidance: string }>(
        '/moderate/advance-turn',
        { method: 'POST', body: JSON.stringify({ session_id: sessionId }) },
      ),
    dispute: (gameId: string, sessionId: string, description: string) =>
      request<import('../types').DisputeResolution>('/moderate/dispute', {
        method: 'POST',
        body: JSON.stringify({ game_id: gameId, session_id: sessionId, description }),
      }),
    checkWin: (sessionId: string) =>
      request<{ session_id: string; game_over: boolean; winner: string | null }>(
        '/moderate/check-win',
        { method: 'POST', body: JSON.stringify({ session_id: sessionId }) },
      ),
  },

  // ---------- Voice ----------
  voice: {
    transcribe: (audioBlob: Blob) => {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      return request<{ text: string }>('/voice/transcribe', {
        method: 'POST',
        body: formData,
      });
    },
  },
};
