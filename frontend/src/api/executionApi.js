/**
 * SkillTree AI - Execution API
 * @module api/executionApi
 */

import api from './api';
import { API_ENDPOINTS } from '../constants';

/**
 * Execute code in sandbox
 * @param {Object} executionData - Code execution data
 * @param {string} executionData.code - Code to execute
 * @param {string} executionData.language - Programming language
 * @param {string} executionData.input - Optional input
 * @param {string} executionData.skillId - Optional skill ID
 * @param {string} executionData.questId - Optional quest ID
 * @returns {Promise<Object>} Execution result
 */
export async function executeCode(executionData) {
  const { code, language, input, skillId, questId } = executionData;
  
  if (!code) {
    throw new Error('Code is required');
  }
  
  if (!language) {
    throw new Error('Language is required');
  }
  
  const payload = {
    code,
    language,
  };
  
  if (input) payload.input = input;
  if (skillId) payload.skill_id = skillId;
  if (questId) payload.quest_id = questId;
  
  const response = await api.post(API_ENDPOINTS.EXECUTE_CODE, payload);
  return response.data;
}

/**
 * Get execution status by ID
 * @param {string} executionId - Execution ID
 * @returns {Promise<Object>} Execution status
 */
export async function getExecutionStatus(executionId) {
  if (!executionId) {
    throw new Error('Execution ID is required');
  }
  
  const url = API_ENDPOINTS.EXECUTE_STATUS.replace('{id}', executionId);
  const response = await api.get(url);
  return response.data;
}

/**
 * Get execution history for current user
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @param {string} params.language - Filter by language
 * @returns {Promise<Object>} Execution history
 */
export async function getExecutionHistory(params = {}) {
  const { page = 1, pageSize = 20, language } = params;
  
  const queryParams = { page, page_size: pageSize };
  if (language) queryParams.language = language;
  
  const response = await api.get(`${API_ENDPOINTS.EXECUTE_CODE}history/`, { params: queryParams });
  return response.data;
}

/**
 * Get supported languages
 * @returns {Promise<Array>} List of supported languages
 */
export async function getSupportedLanguages() {
  const response = await api.get(`${API_ENDPOINTS.EXECUTE_CODE}languages/`);
  return response.data;
}

/**
 * Get execution statistics
 * @returns {Promise<Object>} Execution stats
 */
export async function getExecutionStats() {
  const response = await api.get(`${API_ENDPOINTS.EXECUTE_CODE}stats/`);
  return response.data;
}

/**
 * Cancel a running execution
 * @param {string} executionId - Execution ID
 * @returns {Promise<void>}
 */
export async function cancelExecution(executionId) {
  if (!executionId) {
    throw new Error('Execution ID is required');
  }
  
  const url = `${API_ENDPOINTS.EXECUTE_STATUS.replace('{id}', executionId)}/cancel/`;
  await api.post(url);
}

/**
 * Submit code for AI evaluation
 * @param {Object} evaluationData - Evaluation data
 * @param {string} evaluationData.code - Code to evaluate
 * @param {string} evaluationData.language - Programming language
 * @param {string} evaluationData.skillId - Skill ID
 * @returns {Promise<Object>} AI evaluation result
 */
export async function evaluateCode(evaluationData) {
  const { code, language, skillId } = evaluationData;
  
  if (!code) {
    throw new Error('Code is required');
  }
  
  const payload = { code, language };
  if (skillId) payload.skill_id = skillId;
  
  const response = await api.post('/api/ai_evaluation/evaluate/', payload);
  return response.data;
}

/**
 * Get AI detection results for code
 * @param {string} code - Code to analyze
 * @returns {Promise<Object>} Detection results
 */
export async function detectAI(code) {
  if (!code) {
    throw new Error('Code is required');
  }
  
  const response = await api.post('/api/ai_detection/detect/', { code });
  return response.data;
}

export default {
  executeCode,
  getExecutionStatus,
  getExecutionHistory,
  getSupportedLanguages,
  getExecutionStats,
  cancelExecution,
  evaluateCode,
  detectAI,
};