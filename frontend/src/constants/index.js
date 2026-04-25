/**
 * SkillTree AI - Shared Shape Constants
 * Defines default objects, API configuration, and XP thresholds
 * @module constants
 */

/**
 * Default user object shape for SkillTree AI
 * @typedef {Object} DefaultUser
 * @property {number} id - User ID
 * @property {string} username - Username
 * @property {string} email - Email address
 * @property {string} avatar - Avatar URL
 * @property {number} level - Current level
 * @property {number} xp - Current XP points
 * @property {number} xpToNextLevel - XP needed for next level
 * @property {string} rank - Current rank
 * @property {number} totalSkills - Total skills unlocked
 * @property {number} totalQuests - Total quests completed
 * @property {string} createdAt - Account creation date
 */

/**
 * Default user object
 * @type {DefaultUser}
 */
export const DEFAULT_USER = {
  id: 0,
  username: '',
  email: '',
  avatar: '',
  level: 1,
  xp: 0,
  xpToNextLevel: 100,
  rank: 'Novice',
  totalSkills: 0,
  totalQuests: 0,
  createdAt: new Date().toISOString(),
};

/**
 * API Base URL configuration
 * @type {string}
 */
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * WebSocket URL configuration
 * @type {string}
 */
export const WS_URL = import.meta.env.VITE_WS_URL || '';

/**
 * XP thresholds for each level
 * @type {number[]}
 */
export const XP_THRESHOLDS = [
  0, 100, 250, 500, 850, 1250, 1750, 2350, 3050, 3850,
  4750, 5750, 6850, 8050, 9350, 10750, 12250, 13850, 15550, 17350,
];

/**
 * Rank names based on level ranges
 * @type {Object.<string, [number, number]>}
 */
export const RANK_TIERS = {
  Novice: [1, 5],
  Apprentice: [6, 10],
  Journeyman: [11, 15],
  Expert: [16, 20],
  Master: [21, 25],
  Grandmaster: [26, 30],
  Legend: [31, Infinity],
};

/**
 * Skill node types
 * @type {Object.<string, string>}
 */
export const SKILL_NODE_TYPES = {
  CORE: 'core',
  ADVANCED: 'advanced',
  ELITE: 'elite',
  LEGENDARY: 'legendary',
};

/**
 * Skill node status
 * @type {Object.<string, string>}
 */
export const SKILL_STATUS = {
  LOCKED: 'locked',
  AVAILABLE: 'available',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
};

/**
 * Quest difficulty levels
 * @type {Object.<string, string>}
 */
export const QUEST_DIFFICULTY = {
  EASY: 'easy',
  MEDIUM: 'medium',
  HARD: 'hard',
  EXPERT: 'expert',
};

/**
 * Quest status
 * @type {Object.<string, string>}
 */
export const QUEST_STATUS = {
  AVAILABLE: 'available',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
};

/**
 * Match game modes
 * @type {Object.<string, string>}
 */
export const MATCH_MODES = {
  RANKED: 'ranked',
  CASUAL: 'casual',
  TOURNAMENT: 'tournament',
  PRACTICE: 'practice',
};

/**
 * Match status
 * @type {Object.<string, string>}
 */
export const MATCH_STATUS = {
  WAITING: 'waiting',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
};

/**
 * Leaderboard time periods
 * @type {Object.<string, string>}
 */
export const LEADERBOARD_PERIODS = {
  DAILY: 'daily',
  WEEKLY: 'weekly',
  MONTHLY: 'monthly',
  ALL_TIME: 'all_time',
};

/**
 * Pagination defaults
 * @type {Object.<string, number>}
 */
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
};

/**
 * Animation durations in milliseconds
 * @type {Object.<string, number>}
 */
export const ANIMATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  EXTRA_SLOW: 800,
};

/**
 * Local storage keys
 * @type {Object.<string, string>}
 */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'skilltree_access_token',
  REFRESH_TOKEN: 'skilltree_refresh_token',
  USER_PREFERENCES: 'skilltree_preferences',
  THEME: 'skilltree_theme',
};

/**
 * API endpoints
 * @type {Object.<string, string>}
 */
export const API_ENDPOINTS = {
  AUTH_LOGIN: '/api/token/',
  AUTH_REFRESH: '/api/token/refresh/',
  AUTH_REGISTER: '/api/auth/register/',
  AUTH_LOGOUT: '/api/auth/logout/',
  USERS_ME: '/api/users/me/',
  SKILLS_LIST: '/api/skills/',
  SKILLS_DETAIL: '/api/skills/{id}/',
  SKILLS_TREE: '/api/skills/tree/',
  QUESTS_LIST: '/api/quests/',
  QUESTS_DETAIL: '/api/quests/{id}/',
  QUESTS_ACCEPT: '/api/quests/{id}/accept/',
  QUESTS_COMPLETE: '/api/quests/{id}/complete/',
  EXECUTE_CODE: '/api/executor/execute/',
  EXECUTE_STATUS: '/api/executor/status/{id}/',
  MATCH_CREATE: '/api/multiplayer/create/',
  MATCH_JOIN: '/api/multiplayer/join/',
  MATCH_DETAIL: '/api/multiplayer/{id}/',
  LEADERBOARD: '/api/leaderboard/',
  MENTOR_LIST: '/api/mentor/',
  MENTOR_DETAIL: '/api/mentor/{id}/',
};

/**
 * Error messages
 * @type {Object.<string, string>}
 */
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  UNAUTHORIZED: 'Session expired. Please log in again.',
  FORBIDDEN: 'You do not have permission to perform this action.',
  NOT_FOUND: 'The requested resource was not found.',
  SERVER_ERROR: 'Server error. Please try again later.',
  VALIDATION_ERROR: 'Please check your input and try again.',
  TOKEN_EXPIRED: 'Your session has expired. Please log in again.',
  UNKNOWN_ERROR: 'An unexpected error occurred.',
};

/**
 * Success messages
 * @type {Object.<string, string>}
 */
export const SUCCESS_MESSAGES = {
  LOGIN: 'Welcome back!',
  REGISTER: 'Account created successfully!',
  LOGOUT: 'Logged out successfully.',
  SKILL_UNLOCKED: 'New skill unlocked!',
  QUEST_COMPLETED: 'Quest completed! XP earned.',
  MATCH_WON: 'Victory! Match won.',
  MATCH_LOST: 'Match ended. Better luck next time!',
};

/**
 * Calculate level from XP
 * @param {number} xp - Current XP
 * @returns {number} Current level
 */
export function getLevelFromXP(xp) {
  for (let i = XP_THRESHOLDS.length - 1; i >= 0; i--) {
    if (xp >= XP_THRESHOLDS[i]) {
      return i + 1;
    }
  }
  return 1;
}

/**
 * Calculate XP needed for next level
 * @param {number} level - Current level
 * @returns {number} XP needed for next level
 */
export function getXPForNextLevel(level) {
  if (level >= XP_THRESHOLDS.length) {
    return XP_THRESHOLDS[XP_THRESHOLDS.length - 1] * 1.5;
  }
  return XP_THRESHOLDS[level];
}

/**
 * Get rank based on level
 * @param {number} level - Current level
 * @returns {string} Rank name
 */
export function getRankFromLevel(level) {
  for (const [rank, [min, max]] of Object.entries(RANK_TIERS)) {
    if (level >= min && level <= max) {
      return rank;
    }
  }
  return 'Novice';
}

/**
 * Format percentage
 * @param {number} value - Current value
 * @param {number} total - Total value
 * @returns {string} Formatted percentage
 */
export function formatPercentage(value, total) {
  if (total === 0) return '0%';
  return `${Math.round((value / total) * 100)}%`;
}