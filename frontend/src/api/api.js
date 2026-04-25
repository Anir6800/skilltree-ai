/**
 * SkillTree AI - Axios API Client
 * Base axios instance with JWT interceptors and auto-refresh
 * @module api/api
 */

import axios from 'axios';
import { API_BASE_URL, STORAGE_KEYS, ERROR_MESSAGES } from '../constants';

/**
 * Create axios instance with default config
 * @type {import('axios').AxiosInstance}
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

/**
 * Get access token from storage
 * @returns {string|null} Access token
 */
function getAccessToken() {
  try {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  } catch {
    return null;
  }
}

/**
 * Get refresh token from storage
 * @returns {string|null} Refresh token
 */
function getRefreshToken() {
  try {
    return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch {
    return null;
  }
}

/**
 * Set access token in storage
 * @param {string} token - Access token
 */
function setAccessToken(token) {
  try {
    localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
  } catch (e) {
    console.error('Failed to store access token:', e);
  }
}

/**
 * Set refresh token in storage
 * @param {string} token - Refresh token
 */
function setRefreshToken(token) {
  try {
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token);
  } catch (e) {
    console.error('Failed to store refresh token:', e);
  }
}

/**
 * Clear all auth tokens
 */
function clearTokens() {
  try {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  } catch (e) {
    console.error('Failed to clear tokens:', e);
  }
}

/**
 * Refresh access token using refresh token
 * @returns {Promise<string>} New access token
 */
async function refreshAccessToken() {
  const refreshToken = getRefreshToken();
  
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await axios.post(`/api/token/refresh/`, {
    refresh: refreshToken,
  });
  
  const { access } = response.data;
  setAccessToken(access);
  
  return access;
}

/**
 * Flag to prevent multiple simultaneous refresh attempts
 * @type {Promise<string|null>}
 */
let refreshPromise = null;

/**
 * Request interceptor - attach JWT token
 * @param {import('axios').InternalAxiosRequestConfig} config
 * @returns {import('axios').InternalAxiosRequestConfig}
 */
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - handle 401 errors and token refresh
 * @param {import('axios').AxiosResponse} response
 * @returns {import('axios').AxiosResponse}
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If no response, return network error
    if (!error.response) {
      return Promise.reject({
        response: {
          data: { detail: ERROR_MESSAGES.NETWORK_ERROR },
        },
      });
    }
    
    // If 401 and haven't tried to refresh yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // If already refreshing, wait for that promise
      if (refreshPromise) {
        try {
          await refreshPromise;
          return api(originalRequest);
        } catch (refreshError) {
          clearTokens();
          window.dispatchEvent(new CustomEvent('auth:logout', { detail: { reason: 'token_expired' } }));
          return Promise.reject(refreshError);
        }
      }
      
      // Start refresh process
      refreshPromise = refreshAccessToken()
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        })
        .catch((refreshError) => {
          clearTokens();
          window.dispatchEvent(new CustomEvent('auth:logout', { detail: { reason: 'token_expired' } }));
          return Promise.reject(refreshError);
        })
        .finally(() => {
          refreshPromise = null;
        });
      
      return refreshPromise;
    }
    
    // Return error for other status codes
    return Promise.reject(error);
  }
);

/**
 * Set tokens after successful login
 * @param {string} access - Access token
 * @param {string} refresh - Refresh token
 */
export function setAuthTokens(access, refresh) {
  setAccessToken(access);
  setRefreshToken(refresh);
}

/**
 * Clear auth tokens (logout)
 */
export function clearAuthTokens() {
  clearTokens();
}

/**
 * Check if user is authenticated
 * @returns {boolean}
 */
export function isAuthenticated() {
  return !!getAccessToken();
}

export default api;