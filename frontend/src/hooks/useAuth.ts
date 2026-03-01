import { useCallback, useEffect } from 'react';
import { api } from '../api/client';
import { useAppStore } from '../store/gameStore';

export function useAuth() {
  const { user, token, setAuth, clearAuth } = useAppStore();
  const allowDevTokenFallback = import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEV_TOKEN === 'true';

  const login = useCallback(async () => {
    try {
      const { url } = await api.auth.githubUrl();
      window.location.href = url;
    } catch (err) {
      if (!allowDevTokenFallback) {
        throw err;
      }

      // If explicitly enabled in development, use a dev token fallback.
      const auth = await api.auth.devToken();
      setAuth(auth.user, auth.access_token);
    }
  }, [allowDevTokenFallback, setAuth]);

  const logout = useCallback(() => {
    clearAuth();
  }, [clearAuth]);

  const handleOAuthCallback = useCallback(
    async (code: string, state?: string) => {
      const auth = await api.auth.callback(code, state);
      setAuth(auth.user, auth.access_token);
    },
    [setAuth],
  );

  // Check token validity on mount
  useEffect(() => {
    if (token && !user) {
      api.auth
        .me()
        .then((u) => useAppStore.setState({ user: u }))
        .catch(() => clearAuth());
    }
  }, [token, user, clearAuth]);

  return { user, token, login, logout, handleOAuthCallback, isAuthenticated: !!token };
}
