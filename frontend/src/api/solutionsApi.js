/**
 * SkillTree AI - Solutions API Client
 * Handles peer code review system API calls.
 */

import api from './api';
import { getAccessToken } from './api';

const SOLUTIONS_API = '/api/quests/solutions';

/**
 * Share a passed submission as a solution.
 * @param {number} submissionId - Submission ID
 * @param {boolean} isAnonymous - Whether to share anonymously
 * @returns {Promise<Object>} Shared solution data
 */
export async function shareSolution(submissionId, isAnonymous = false) {
  const response = await api.post(
    `${SOLUTIONS_API}/${submissionId}/share/`,
    { is_anonymous: isAnonymous }
  );
  return response.data;
}

/**
 * Get paginated list of shared solutions.
 * @param {Object} params - Query parameters
 * @param {number} params.questId - Filter by quest ID
 * @param {string} params.sort - Sort by 'top', 'new', or 'fastest'
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @returns {Promise<Object>} Paginated solutions list
 */
export async function getSolutions(params = {}) {
  const { questId, sort = 'new', page = 1, pageSize = 20 } = params;

  const queryParams = {
    page,
    page_size: pageSize,
    sort,
  };

  if (questId) {
    queryParams.quest_id = questId;
  }

  const response = await api.get(SOLUTIONS_API, { params: queryParams });
  return response.data;
}

/**
 * Get detailed view of a solution.
 * @param {number} solutionId - Solution ID
 * @returns {Promise<Object>} Solution data with comments
 */
export async function getSolutionDetail(solutionId) {
  const response = await api.get(`${SOLUTIONS_API}/${solutionId}/`);
  return response.data;
}

/**
 * Get diff between shared solution and model solution.
 * @param {number} solutionId - Solution ID
 * @returns {Promise<Object>} Diff data
 */
export async function getSolutionDiff(solutionId) {
  const response = await api.get(`${SOLUTIONS_API}/${solutionId}/diff/`);
  return response.data;
}

/**
 * Toggle upvote on a solution.
 * @param {number} solutionId - Solution ID
 * @returns {Promise<Object>} Updated upvote status
 */
export async function toggleUpvote(solutionId) {
  const response = await api.post(`${SOLUTIONS_API}/${solutionId}/upvote/`);
  return response.data;
}

/**
 * Add a comment to a solution.
 * @param {number} solutionId - Solution ID
 * @param {string} text - Comment text
 * @param {number} parentId - Parent comment ID (for replies)
 * @returns {Promise<Object>} Created comment data
 */
export async function addComment(solutionId, text, parentId = null) {
  const payload = { text };
  if (parentId) {
    payload.parent_id = parentId;
  }

  const response = await api.post(
    `${SOLUTIONS_API}/${solutionId}/comments/`,
    payload
  );
  return response.data;
}

/**
 * Get all comments for a solution.
 * @param {number} solutionId - Solution ID
 * @returns {Promise<Array>} Comments list (threaded)
 */
export async function getComments(solutionId) {
  const response = await api.get(`${SOLUTIONS_API}/${solutionId}/comments/list/`);
  return response.data;
}

/**
 * Delete a comment.
 * @param {number} commentId - Comment ID
 * @returns {Promise<Object>} Success message
 */
export async function deleteComment(commentId) {
  const response = await api.delete(`${SOLUTIONS_API}/comments/${commentId}/delete/`);
  return response.data;
}

/**
 * Get all solutions shared by the current user.
 * @param {Object} params - Pagination params
 * @returns {Promise<Object>} User's solutions
 */
export async function getUserSolutions(params = {}) {
  const { page = 1, pageSize = 20 } = params;

  const response = await api.get(`${SOLUTIONS_API}/user/`, {
    params: {
      page,
      page_size: pageSize,
    },
  });
  return response.data;
}

export default {
  shareSolution,
  getSolutions,
  getSolutionDetail,
  getSolutionDiff,
  toggleUpvote,
  addComment,
  getComments,
  deleteComment,
  getUserSolutions,
};
