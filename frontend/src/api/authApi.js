/**
 * SkillTree AI - Authentication API
 * @module api/authApi
 */

import api, { setAuthTokens, clearAuthTokens } from './api';
import { API_ENDPOINTS } from '../constants';

/**
 * Login user with credentials
 * @param {string} username - Username
 * @param {string} password - Password
 * @returns {Promise<Object>} User data and tokens
 */
export async function login(username, password) {
  if (!username || !password) {
    throw new Error('Username and password are required');
  }
  
  const response = await api.post(API_ENDPOINTS.AUTH_LOGIN, {
    username,
    password,
  });
  
  const { access, refresh } = response.data;
  setAuthTokens(access, refresh);
  
  return response.data;
}

/**
 * Register new user
 * @param {Object} userData - User registration data
 * @param {string} userData.username - Username
 * @param {string} userData.email - Email
 * @param {string} userData.password - Password
 * @param {string} userData.passwordConfirm - Password confirmation
 * @returns {Promise<Object>} User data
 */
export async function register(userData) {
  const { username, email, password, passwordConfirm } = userData;
  
  if (!username || !email || !password) {
    throw new Error('Username, email, and password are required');
  }
  
  if (password !== passwordConfirm) {
    throw new Error('Passwords do not match');
  }
  
  if (password.length < 8) {
    throw new Error('Password must be at least 8 characters');
  }
  
  const response = await api.post(API_ENDPOINTS.AUTH_REGISTER, {
    username,
    email,
    password,
    password_confirm: passwordConfirm,
  });
  
  return response.data;
}

/**
 * Logout user
 * @returns {Promise<void>}
 */
export async function logout() {
  const refreshToken = localStorage.getItem('skilltree_refresh_token');
  try {
    if (refreshToken) {
      await api.post('/api/auth/logout/', { refresh: refreshToken });
    }
  } catch (e) {
    // Ignore logout API errors — always clear tokens
  } finally {
    clearAuthTokens();
  }
}

/**
 * Get current user profile
 * @returns {Promise<Object>} User profile data
 */
export async function getCurrentUser() {
  const response = await api.get(API_ENDPOINTS.USERS_ME);
  return response.data;
}

/**
 * Update current user profile
 * @param {Object} userData - Updated user data
 * @returns {Promise<Object>} Updated user data
 */
export async function updateProfile(userData) {
  const response = await api.patch(API_ENDPOINTS.USERS_ME, userData);
  return response.data;
}

/**
 * Change user password
 * @param {string} currentPassword - Current password
 * @param {string} newPassword - New password
 * @param {string} newPasswordConfirm - New password confirmation
 * @returns {Promise<void>}
 */
export async function changePassword(currentPassword, newPassword, newPasswordConfirm) {
  if (newPassword !== newPasswordConfirm) {
    throw new Error('Passwords do not match');
  }
  
  if (newPassword.length < 8) {
    throw new Error('Password must be at least 8 characters');
  }
  
  await api.post('/api/auth/password/', {
    current_password: currentPassword,
    new_password: newPassword,
    new_password_confirm: newPasswordConfirm,
  });
}

/**
 * Request password reset email
 * @param {string} email - User email
 * @returns {Promise<void>}
 */
export async function requestPasswordReset(email) {
  if (!email) {
    throw new Error('Email is required');
  }
  
  await api.post('/api/auth/password/reset/', { email });
}

/**
 * Reset password with token
 * @param {string} token - Reset token from email
 * @param {string} newPassword - New password
 * @returns {Promise<void>}
 */
export async function resetPassword(token, newPassword) {
  if (!token || !newPassword) {
    throw new Error('Token and new password are required');
  }
  
  await api.post('/api/auth/password/reset/confirm/', {
    token,
    new_password: newPassword,
  });
}

/**
 * Verify user email
 * @param {string} token - Verification token
 * @returns {Promise<void>}
 */
export async function verifyEmail(token) {
  if (!token) {
    throw new Error('Verification token is required');
  }
  
  await api.post('/api/auth/verify/', { token });
}

/**
 * Resend verification email
 * @returns {Promise<void>}
 */
export async function resendVerificationEmail() {
  await api.post('/api/auth/verify/resend/');
}

export default {
  login,
  register,
  logout,
  getCurrentUser,
  updateProfile,
  changePassword,
  requestPasswordReset,
  resetPassword,
  verifyEmail,
  resendVerificationEmail,
};