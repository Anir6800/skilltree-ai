import axios from 'axios';
import useAuthStore from '../store/authStore';

/**
 * SkillTree AI - Central API Instance
 * Axios configuration with JWT injection and automatic token refresh
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor
 * Adds the JWT access token to every outgoing request
 */
api.interceptors.request.use(
  (config) => {
    const { accessToken } = useAuthStore.getState();
    
    if (accessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response Interceptor
 * Handles 401 Unauthorized errors by attempting a token refresh
 * Retries the original request once upon successful refresh
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized errors (excluding the refresh endpoint itself)
    if (
      error.response?.status === 401 && 
      !originalRequest._retry && 
      !originalRequest.url?.includes('/api/auth/refresh/')
    ) {
      originalRequest._retry = true;

      try {
        // Trigger token refresh action in authStore
        const newAccessToken = await useAuthStore.getState().refreshTokens();
        
        if (newAccessToken) {
          // Retry the original request with the new token
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh process failed significantly
        console.error('API Response Interceptor: Token refresh sequence failed', refreshError);
      }

      // If we reach here, refresh failed or was not possible
      useAuthStore.getState().logout();
      
      // Redirect to login page if we're in a browser environment
      if (typeof window !== 'undefined') {
        const currentPath = window.location.pathname;
        if (currentPath !== '/login' && currentPath !== '/auth') {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
