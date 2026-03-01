import { create } from 'zustand';
import type { Game, GameSession, User } from '../types';

interface AppState {
  // Auth
  user: User | null;
  token: string | null;
  setAuth: (user: User, token: string) => void;
  clearAuth: () => void;

  // Games
  games: Game[];
  currentGame: Game | null;
  setGames: (games: Game[]) => void;
  setCurrentGame: (game: Game | null) => void;
  addGame: (game: Game) => void;
  removeGame: (id: string) => void;

  // Session
  currentSession: GameSession | null;
  setCurrentSession: (session: GameSession | null) => void;

  // UI
  loading: boolean;
  error: string | null;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Auth
  user: null,
  token: localStorage.getItem('bg_token'),
  setAuth: (user, token) => {
    localStorage.setItem('bg_token', token);
    set({ user, token });
  },
  clearAuth: () => {
    localStorage.removeItem('bg_token');
    set({ user: null, token: null });
  },

  // Games
  games: [],
  currentGame: null,
  setGames: (games) => set({ games }),
  setCurrentGame: (game) => set({ currentGame: game }),
  addGame: (game) => set((s) => ({ games: [game, ...s.games] })),
  removeGame: (id) => set((s) => ({ games: s.games.filter((g) => g.id !== id) })),

  // Session
  currentSession: null,
  setCurrentSession: (session) => set({ currentSession: session }),

  // UI
  loading: false,
  error: null,
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));
