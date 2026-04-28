/**
 * SkillTree AI - Skills API
 * @module api/skillApi
 */

import api from './api';
import { API_ENDPOINTS, PAGINATION } from '../constants';

/**
 * Get paginated list of skills — maps to the skill tree endpoint
 * @param {Object} params - Query parameters (ignored, tree returns all)
 * @returns {Promise<Object>} Skills list
 */
export async function getSkills(params = {}) {
  // The backend exposes skills via /api/skills/tree/ — use that and return nodes as a flat list
  const response = await api.get('/api/skills/tree/');
  const nodes = response.data?.nodes ?? response.data ?? [];
  return { results: nodes, count: nodes.length };
}

/**
 * Get single skill by ID — fetches the full tree and returns the matching node.
 * @param {number|string} id - Skill ID
 * @returns {Promise<Object>} Skill data
 */
export async function getSkill(id) {
  if (!id) {
    throw new Error('Skill ID is required');
  }

  // Backend has no single-skill endpoint — fetch the tree and find the node.
  const response = await api.get('/api/skills/tree/');
  const nodes = response.data?.nodes ?? [];
  const skill = nodes.find((n) => String(n.id) === String(id));
  if (!skill) {
    throw new Error(`Skill ${id} not found`);
  }
  return skill;
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
 * Unlock a skill node — maps to the start endpoint (backend combines unlock+start).
 * @param {number|string} skillId - Skill ID to unlock
 * @returns {Promise<Object>} Updated skill progress data
 */
export async function unlockSkill(skillId) {
  if (!skillId) {
    throw new Error('Skill ID is required');
  }
  // Backend has no separate unlock endpoint — /start/ handles both unlock and start.
  return startLearning(skillId);
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
 * Complete a skill node — backend auto-completes when all quests are passed.
 * This is a client-side optimistic update; the server drives actual completion.
 * @param {number|string} skillId - Skill ID
 * @param {Object} completionData - Completion data (unused, kept for API compat)
 * @returns {Promise<Object>} Synthetic completion response
 */
export async function completeSkill(skillId, completionData = {}) {
  if (!skillId) {
    throw new Error('Skill ID is required');
  }
  // Backend auto-completes skills via quest submission pipeline.
  // Return synthetic response so the store can update optimistically.
  return { id: skillId, status: 'completed' };
}

/**
 * Get skill progress for current user — derived from the tree endpoint.
 * @returns {Promise<Object>} Skill progress data
 */
export async function getSkillProgress() {
  const response = await api.get('/api/skills/tree/');
  const nodes = response.data?.nodes ?? [];
  const completed = nodes.filter((n) => n.status === 'completed').length;
  const in_progress = nodes.filter((n) => n.status === 'in_progress').length;
  return { total: nodes.length, completed, in_progress };
}

/**
 * Search skills — filters the tree nodes client-side.
 * @param {string} query - Search query
 * @param {Object} filters - Additional filters
 * @returns {Promise<Object>} Search results
 */
export async function searchSkills(query, filters = {}) {
  if (!query) {
    throw new Error('Search query is required');
  }
  const { results } = await getSkills();
  const q = query.toLowerCase();
  const filtered = results.filter(
    (s) => s.name?.toLowerCase().includes(q) || s.description?.toLowerCase().includes(q)
  );
  return { results: filtered, count: filtered.length };
}

/**
 * Get skill categories — derived from tree nodes.
 * @returns {Promise<Array>} List of categories
 */
export async function getSkillCategories() {
  const { results } = await getSkills();
  const cats = [...new Set(results.map((s) => s.category).filter(Boolean))];
  return cats;
}

/**
 * Get recommended skills — returns available (unlocked but not started) skills.
 * @returns {Promise<Array>} Recommended skills
 */
export async function getRecommendedSkills() {
  const { results } = await getSkills();
  return results.filter((s) => s.status === 'available').slice(0, 5);
}

/**
 * Get skill radar data for current user
 * @returns {Promise<Object>} Radar data with 5 categories and mastery percentages
 */
export async function getSkillRadar() {
  const response = await api.get(`${API_ENDPOINTS.SKILLS_LIST}radar/`);
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
  getSkillRadar,
};