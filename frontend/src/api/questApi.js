/**
 * SkillTree AI - Quests API
 * @module api/questApi
 */

import api from './api';
import { API_ENDPOINTS, PAGINATION } from '../constants';

/**
 * Get paginated list of quests
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @param {string} params.difficulty - Filter by difficulty
 * @param {string} params.status - Filter by status
 * @returns {Promise<Object>} Paginated quests list
 */
export async function getQuests(params = {}) {
  const { page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE, difficulty, status } = params;
  
  const queryParams = {
    page,
    page_size: pageSize,
  };
  
  if (difficulty) queryParams.difficulty = difficulty;
  if (status) queryParams.status = status;
  
  const response = await api.get(API_ENDPOINTS.QUESTS_LIST, { params: queryParams });
  return response.data;
}

/**
 * Get single quest by ID
 * @param {number|string} id - Quest ID
 * @returns {Promise<Object>} Quest data
 */
export async function getQuest(id) {
  if (!id) {
    throw new Error('Quest ID is required');
  }
  
  const url = API_ENDPOINTS.QUESTS_DETAIL.replace('{id}', id);
  const response = await api.get(url);
  return response.data;
}

/**
 * Accept a quest
 * @param {number|string} questId - Quest ID to accept
 * @returns {Promise<Object>} Updated quest data
 */
export async function acceptQuest(questId) {
  if (!questId) {
    throw new Error('Quest ID is required');
  }
  
  const url = API_ENDPOINTS.QUESTS_ACCEPT.replace('{id}', questId);
  const response = await api.post(url);
  return response.data;
}

/**
 * Complete a quest
 * @param {number|string} questId - Quest ID
 * @param {Object} completionData - Completion data (code, output, etc.)
 * @returns {Promise<Object>} Completion result with XP reward
 */
export async function completeQuest(questId, completionData = {}) {
  if (!questId) {
    throw new Error('Quest ID is required');
  }
  
  const url = API_ENDPOINTS.QUESTS_COMPLETE.replace('{id}', questId);
  const response = await api.post(url, completionData);
  return response.data;
}

/**
 * Abandon a quest
 * @param {number|string} questId - Quest ID
 * @returns {Promise<void>}
 */
export async function abandonQuest(questId) {
  if (!questId) {
    throw new Error('Quest ID is required');
  }
  
  const url = `${API_ENDPOINTS.QUESTS_DETAIL.replace('{id}', questId)}/abandon/`;
  await api.post(url);
}

/**
 * Get user's active quests — uses status filter on the main quests endpoint
 * @returns {Promise<Array>} Active quests
 */
export async function getActiveQuests() {
  const response = await api.get(API_ENDPOINTS.QUESTS_LIST, {
    params: { status: 'in_progress' },
  });
  const data = response.data;
  return data.results ?? data;
}

/**
 * Get user's completed quests — uses status filter on the main quests endpoint
 * @param {Object} params - Pagination params
 * @returns {Promise<Object>} Completed quests
 */
export async function getCompletedQuests(params = {}) {
  const response = await api.get(API_ENDPOINTS.QUESTS_LIST, {
    params: { status: 'passed' },
  });
  return response.data;
}

/**
 * Get available quests for user
 * @returns {Promise<Array>} Available quests
 */
export async function getAvailableQuests() {
  const response = await api.get(API_ENDPOINTS.QUESTS_LIST, {
    params: { status: 'not_started' },
  });
  const data = response.data;
  return data.results ?? data;
}

/**
 * Get quest categories
 * @returns {Promise<Array>} List of categories
 */
export async function getQuestCategories() {
  const response = await api.get(`${API_ENDPOINTS.QUESTS_LIST}categories/`);
  return response.data;
}

/**
 * Search quests
 * @param {string} query - Search query
 * @param {Object} filters - Additional filters
 * @returns {Promise<Object>} Search results
 */
export async function searchQuests(query, filters = {}) {
  if (!query) {
    throw new Error('Search query is required');
  }
  
  const params = { q: query, ...filters };
  const response = await api.get(`${API_ENDPOINTS.QUESTS_LIST}search/`, { params });
  return response.data;
}

export default {
  getQuests,
  getQuest,
  acceptQuest,
  completeQuest,
  abandonQuest,
  getActiveQuests,
  getCompletedQuests,
  getAvailableQuests,
  getQuestCategories,
  searchQuests,
};