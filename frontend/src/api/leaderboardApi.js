/**
 * SkillTree AI - Leaderboard API
 * @module api/leaderboardApi
 */

import api from './api';
import { API_ENDPOINTS, LEADERBOARD_PERIODS, PAGINATION } from '../constants';

/**
 * Get leaderboard entries
 * @param {Object} params - Query parameters
 * @param {string} params.period - Time period (daily, weekly, monthly, all_time)
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @param {string} params.skillId - Optional filter by skill
 * @returns {Promise<Object>} Leaderboard data
 */
export async function getLeaderboard(params = {}) {
  const { 
    period = LEADERBOARD_PERIODS.WEEKLY, 
    page = PAGINATION.DEFAULT_PAGE, 
    pageSize = PAGINATION.DEFAULT_PAGE_SIZE,
    skillId 
  } = params;
  
  const queryParams = {
    period,
    page,
    page_size: pageSize,
  };
  
  if (skillId) queryParams.skill_id = skillId;
  
  const response = await api.get(API_ENDPOINTS.LEADERBOARD, { params: queryParams });
  return response.data;
}

/**
 * Get user's rank on leaderboard
 * @param {Object} params - Query parameters
 * @param {string} params.period - Time period
 * @param {string} params.skillId - Optional filter by skill
 * @returns {Promise<Object>} User's rank data
 */
export async function getUserRank(params = {}) {
  const { period = LEADERBOARD_PERIODS.WEEKLY, skillId } = params;
  
  const queryParams = { period };
  if (skillId) queryParams.skill_id = skillId;
  
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}rank/`, { params: queryParams });
  return response.data;
}

/**
 * Get top players for a specific period
 * @param {string} period - Time period
 * @param {number} limit - Number of top players to return
 * @returns {Promise<Array>} Top players
 */
export async function getTopPlayers(period = LEADERBOARD_PERIODS.WEEKLY, limit = 10) {
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}top/`, {
    params: { period, limit },
  });
  return response.data;
}

/**
 * Get leaderboard around a specific user
 * @param {number} userId - User ID
 * @param {number} range - Number of players above and below
 * @returns {Promise<Object>} Leaderboard around user
 */
export async function getLeaderboardAroundUser(userId, range = 5) {
  if (!userId) {
    throw new Error('User ID is required');
  }
  
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}around/`, {
    params: { user_id: userId, range },
  });
  return response.data;
}

/**
 * Get skill-specific leaderboard
 * @param {string} skillId - Skill ID
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Skill leaderboard
 */
export async function getSkillLeaderboard(skillId, params = {}) {
  if (!skillId) {
    throw new Error('Skill ID is required');
  }
  
  const { period = LEADERBOARD_PERIODS.WEEKLY, page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE } = params;
  
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}skill/${skillId}/`, {
    params: { period, page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get quest completion leaderboard
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Quest leaderboard
 */
export async function getQuestLeaderboard(params = {}) {
  const { period = LEADERBOARD_PERIODS.WEEKLY, page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE } = params;
  
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}quests/`, {
    params: { period, page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get match win rate leaderboard
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Match leaderboard
 */
export async function getMatchLeaderboard(params = {}) {
  const { period = LEADERBOARD_PERIODS.WEEKLY, page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE } = params;
  
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}matches/`, {
    params: { period, page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get global statistics
 * @returns {Promise<Object>} Global stats
 */
export async function getGlobalStats() {
  const response = await api.get(`${API_ENDPOINTS.LEADERBOARD}stats/`);
  return response.data;
}

export default {
  getLeaderboard,
  getUserRank,
  getTopPlayers,
  getLeaderboardAroundUser,
  getSkillLeaderboard,
  getQuestLeaderboard,
  getMatchLeaderboard,
  getGlobalStats,
};