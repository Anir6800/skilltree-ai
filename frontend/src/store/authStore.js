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
          await authApi.register(userData);
          
          // Auto-login after registration
          await authApi.login(userData.username, userData.password);
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
            'Registration failed. Please try again.';
          
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
        
        if (accessToken) {
          set({ isAuthenticated: true });
          get().fetchUser();
        }
      },
    }),
    {
      name: STORAGE_KEYS.USER_PREFERENCES,
      partialize: (state) => ({
        // Only persist these fields
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
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