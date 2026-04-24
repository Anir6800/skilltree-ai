import { create } from 'zustand';

/**
 * SkillTree AI - User Profile Interface
 */
export interface User {
  id: number;
  username: string;
  email: string;
  avatar_url: string | null;
  xp: number;
  level: number;
  role: 'user' | 'admin';
  streak: number;
  rank?: string;
}

/**
 * Auth Store State and Actions
 */
interface AuthState {
  // State
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Sync Actions (As requested)
  /**
   * Sets authentication state and persists to localStorage
   */
  login: (user: User, accessToken: string, refreshToken: string) => void;
  
  /**
   * Clears state and localStorage, calls logout API
   */
  logout: () => Promise<void>;
  
  /**
   * Exchanges refresh token for a new access token
   */
  refreshTokens: () => Promise<string | null>;
  
  /**
   * Restores state from localStorage
   */
  rehydrate: () => void;
  
  /**
   * Merges partial update into user state
   */
  updateUser: (partial: Partial<User>) => void;

  // Helper Actions for UI (Ensuring full functionality)
  /**
   * Clears the current error state
   */
  clearError: () => void;
}

/**
 * Zustand Auth Store
 * Handles JWT lifecycle and user progression state
 */
const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: (user, accessToken, refreshToken) => {
    set({
      user,
      accessToken,
      refreshToken,
      isAuthenticated: true,
      error: null
    });

    localStorage.setItem('auth_user', JSON.stringify(user));
    localStorage.setItem('auth_access', accessToken);
    localStorage.setItem('auth_refresh', refreshToken);
  },

  logout: async () => {
    const { refreshToken } = get();
    set({ isLoading: true });
    
    try {
      if (refreshToken) {
        const api = (await import('../api/api')).default;
        await api.post('/api/auth/logout/', { refresh: refreshToken });
      }
    } catch (error) {
      console.error('AuthStore: Logout API failed', error);
    } finally {
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null
      });

      localStorage.removeItem('auth_user');
      localStorage.removeItem('auth_access');
      localStorage.removeItem('auth_refresh');
    }
  },

  refreshTokens: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return null;

    try {
      const api = (await import('../api/api')).default;
      const response = await api.post('/api/auth/refresh/', { refresh: refreshToken });
      const { access } = response.data;

      set({ accessToken: access });
      localStorage.setItem('auth_access', access);
      
      return access;
    } catch (error) {
      console.error('AuthStore: Refresh failed', error);
      get().logout();
      return null;
    }
  },

  rehydrate: () => {
    try {
      const userStr = localStorage.getItem('auth_user');
      const access = localStorage.getItem('auth_access');
      const refresh = localStorage.getItem('auth_refresh');

      if (userStr && access && refresh) {
        set({
          user: JSON.parse(userStr),
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
        });
      }
    } catch (error) {
      console.error('AuthStore: Rehydration failed', error);
      localStorage.clear();
    }
  },

  updateUser: (partial) => {
    set((state) => {
      if (!state.user) return state;
      const updatedUser = { ...state.user, ...partial };
      localStorage.setItem('auth_user', JSON.stringify(updatedUser));
      return { user: updatedUser };
    });
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
