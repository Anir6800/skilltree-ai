/**
 * SkillTree AI - Skills API
 * @module api/skillApi
 */

import api from './api';
import { API_ENDPOINTS, PAGINATION } from '../constants';

/**
 * Get paginated list of skills
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @param {string} params.category - Filter by category
 * @param {string} params.status - Filter by status
 * @returns {Promise<Object>} Paginated skills list
 */
export async function getSkills(params = {}) {
  const { page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE, category, status } = params;
  
  const queryParams = {
    page,
    page_size: pageSize,
  };
  
  if (category) queryParams.category = category;
  if (status) queryParams.status = status;
  
  const response = await api.get(API_ENDPOINTS.SKILLS_LIST, { params: queryParams });
  return response.data;
}

/**
 * Get single skill by ID
 * @param {number|string} id - Skill ID
 * @returns {Promise<Object>} Skill data
 */
export async function getSkill(id) {
  if (!id) {
    throw new Error('Skill ID is required');
  }
  
  const url = API_ENDPOINTS.SKILLS_DETAIL.replace('{id}', id);
  const response = await api.get(url);
  return response.data;
}

/**
 * Get full skill tree for current user
 * @returns {Promise<Object>} Skill tree data
 */
export async function getSkillTree() {
  const response = await api.get(API_ENDPOINTS.SKILLS_TREE);
  return response.data;
}

/**
 * Unlock a skill node
 * @param {number|string} skillId - Skill ID to unlock
 * @returns {Promise<Object>} Updated skill data
 */
export async function unlockSkill(skillId) {
  if (!skillId) {
    throw new Error('Skill ID is required');
  }
  
  const url = `${API_ENDPOINTS.SKILLS_DETAIL.replace('{id}', skillId)}/unlock/`;
  const response = await api.post(url);
  return response.data;
}

/**
 * Start learning a skill
 * @param {number|string} skillId - Skill ID
 * @returns {Promise<Object>} Updated skill data
 */
export async function startLearning(skillId) {
  if (!skillId) {
    throw new Error('Skill ID is required');
  }
  
  const url = `${API_ENDPOINTS.SKILLS_DETAIL.replace('{id}', skillId)}/start/`;
  const response = await api.post(url);
  return response.data;
}

/**
 * Complete a skill node
 * @param {number|string} skillId - Skill ID
 * @param {Object} completionData - Completion data
 * @returns {Promise<Object>} Updated skill data
 */
export async function completeSkill(skillId, completionData = {}) {
  if (!skillId) {
    throw new Error('Skill ID is required');
  }
  
  const url = `${API_ENDPOINTS.SKILLS_DETAIL.replace('{id}', skillId)}/complete/`;
  const response = await api.post(url, completionData);
  return response.data;
}

/**
 * Get skill progress for current user
 * @returns {Promise<Object>} Skill progress data
 */
export async function getSkillProgress() {
  const response = await api.get(`${API_ENDPOINTS.SKILLS_LIST}progress/`);
  return response.data;
}

/**
 * Search skills
 * @param {string} query - Search query
 * @param {Object} filters - Additional filters
 * @returns {Promise<Object>} Search results
 */
export async function searchSkills(query, filters = {}) {
  if (!query) {
    throw new Error('Search query is required');
  }
  
  const params = { q: query, ...filters };
  const response = await api.get(`${API_ENDPOINTS.SKILLS_LIST}search/`, { params });
  return response.data;
}

/**
 * Get skill categories
 * @returns {Promise<Array>} List of categories
 */
export async function getSkillCategories() {
  const response = await api.get(`${API_ENDPOINTS.SKILLS_LIST}categories/`);
  return response.data;
}

/**
 * Get recommended skills for user
 * @returns {Promise<Array>} Recommended skills
 */
export async function getRecommendedSkills() {
  const response = await api.get(`${API_ENDPOINTS.SKILLS_LIST}recommended/`);
  return response.data;
}

export default {
  getSkills,
  getSkill,
  getSkillTree,
  unlockSkill,
  startLearning,
  completeSkill,
  getSkillProgress,
  searchSkills,
  getSkillCategories,
  getRecommendedSkills,
};