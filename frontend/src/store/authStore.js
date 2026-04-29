/**
 * SkillTree AI - Authentication Store
 * Zustand store for JWT auth state management
 * @module store/authStore
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { DEFAULT_USER, STORAGE_KEYS } from '../constants';
import * as authApi from '../api/authApi';

/**
 * @typedef {Object} AuthState
 * @property {Object} user - Current user data
 * @property {boolean} isAuthenticated - Whether user is logged in
 * @property {boolean} isLoading - Loading state
 * @property {string|null} error - Error message
 * @property {function} login - Login function
 * @property {function} register - Register function
 * @property {function} logout - Logout function
 * @property {function} fetchUser - Fetch current user
 * @property {function} updateUser - Update user data
 * @property {function} clearError - Clear error state
 */

/**
 * Create auth store with persist middleware
 * @type {import('zustand').UseStore<AuthState>}
 */
const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: DEFAULT_USER,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      _hasHydrated: false,

      // Login action
      login: async (username, password) => {
        set({ isLoading: true, error: null });
        
        try {
          await authApi.login(username, password);
          const user = await authApi.getCurrentUser();
          
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          
          return user;
        } catch (error) {
          const errorMessage = error.response?.data?.detail || 
            error.response?.data?.message || 
            'Login failed. Please check your credentials.';
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw new Error(errorMessage);
        }
      },

      // Register action
      register: async (userData) => {
        set({ isLoading: true, error: null });
        
        try {
          const result = await authApi.register(userData);
          
          // Register endpoint returns tokens directly — store them
          if (result.tokens) {
            const { setAuthTokens } = await import('../api/api');
            setAuthTokens(result.tokens.access, result.tokens.refresh);
          } else {
            // Fallback: login after registration
            await authApi.login(userData.username, userData.password);
          }

          const user = await authApi.getCurrentUser();
          
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          
          return user;
        } catch (error) {
          let errorMessage = 'Registration failed. Please try again.';
          
          if (error.response?.data) {
            const data = error.response.data;
            if (data.detail) {
              errorMessage = data.detail;
            } else if (data.message) {
              errorMessage = data.message;
            } else if (typeof data === 'object') {
              const firstField = Object.keys(data)[0];
              const firstError = data[firstField];
              if (Array.isArray(firstError)) {
                errorMessage = `${firstField}: ${firstError[0]}`;
              } else if (typeof firstError === 'string') {
                errorMessage = `${firstField}: ${firstError}`;
              }
            }
          }
          
          set({
            isLoading: false,
            error: errorMessage,
          });
          
          throw new Error(errorMessage);
        }
      },

      // Logout action
      logout: async () => {
        set({ isLoading: true });
        
        try {
          await authApi.logout();
        } catch (error) {
          console.warn('Logout API call failed:', error);
        } finally {
          set({
            user: DEFAULT_USER,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      // Fetch current user
      fetchUser: async () => {
        const { isAuthenticated } = get();
        
        if (!isAuthenticated) {
          return null;
        }
        
        set({ isLoading: true });
        
        try {
          const user = await authApi.getCurrentUser();
          
          set({
            user,
            isLoading: false,
          });
          
          return user;
        } catch (error) {
          // If token is invalid, logout
          if (error.response?.status === 401) {
            get().logout();
          }
          
          set({ isLoading: false });
          return null;
        }
      },

      // Update user data
      updateUser: (userData) => {
        set((state) => ({
          user: {
            ...state.user,
            ...userData,
          },
        }));
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },

      // Initialize from storage (called on app start)
      initialize: () => {
        const accessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
        const { isAuthenticated } = get();
        
        // If we have a token but state says not authenticated, sync them
        if (accessToken && !isAuthenticated) {
          set({ isAuthenticated: true });
        }
        
        // If state says authenticated, refresh user data
        if (get().isAuthenticated) {
          get().fetchUser();
        }
      },
      
      setHasHydrated: (state) => {
        set({ _hasHydrated: state });
      },
    }),
    {
      name: STORAGE_KEYS.USER_PREFERENCES,
      partialize: (state) => ({
        // Only persist these fields
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: (state) => {
        return () => state.setHasHydrated(true);
      }
    }
  )
);

// Listen for auth:logout event from API interceptor
if (typeof window !== 'undefined') {
  window.addEventListener('auth:logout', (event) => {
    const { logout } = useAuthStore.getState();
    logout();
  });
}

export default useAuthStore;