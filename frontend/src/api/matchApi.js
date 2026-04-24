/**
 * SkillTree AI - Match/Multiplayer API
 * @module api/matchApi
 */

import api from './api';
import { API_ENDPOINTS, MATCH_MODES, MATCH_STATUS, PAGINATION } from '../constants';

/**
 * Create a new match
 * @param {Object} matchData - Match creation data
 * @param {string} matchData.mode - Match mode (ranked, casual, tournament, practice)
 * @param {string} matchData.skillId - Optional skill ID to match on
 * @param {number} matchData.maxPlayers - Maximum players (2-8)
 * @returns {Promise<Object>} Created match data
 */
export async function createMatch(matchData) {
  const { mode, skillId, maxPlayers } = matchData;
  
  if (!mode || !Object.values(MATCH_MODES).includes(mode)) {
    throw new Error('Valid match mode is required');
  }
  
  const payload = { mode };
  if (skillId) payload.skill_id = skillId;
  if (maxPlayers) payload.max_players = Math.min(8, Math.max(2, maxPlayers));
  
  const response = await api.post(API_ENDPOINTS.MATCH_CREATE, payload);
  return response.data;
}

/**
 * Join an existing match
 * @param {string} matchId - Match ID to join
 * @returns {Promise<Object>} Match data
 */
export async function joinMatch(matchId) {
  if (!matchId) {
    throw new Error('Match ID is required');
  }
  
  const url = API_ENDPOINTS.MATCH_JOIN.replace('{id}', matchId);
  const response = await api.post(url);
  return response.data;
}

/**
 * Get match details
 * @param {string} matchId - Match ID
 * @returns {Promise<Object>} Match details
 */
export async function getMatch(matchId) {
  if (!matchId) {
    throw new Error('Match ID is required');
  }
  
  const url = API_ENDPOINTS.MATCH_DETAIL.replace('{id}', matchId);
  const response = await api.get(url);
  return response.data;
}

/**
 * Leave a match
 * @param {string} matchId - Match ID
 * @returns {Promise<void>}
 */
export async function leaveMatch(matchId) {
  if (!matchId) {
    throw new Error('Match ID is required');
  }
  
  const url = `${API_ENDPOINTS.MATCH_DETAIL.replace('{id}', matchId)}/leave/`;
  await api.post(url);
}

/**
 * Submit match solution
 * @param {string} matchId - Match ID
 * @param {Object} solution - Solution data
 * @param {string} solution.code - Submitted code
 * @param {string} solution.language - Programming language
 * @returns {Promise<Object>} Submission result
 */
export async function submitSolution(matchId, solution) {
  if (!matchId) {
    throw new Error('Match ID is required');
  }
  
  if (!solution?.code || !solution?.language) {
    throw new Error('Code and language are required');
  }
  
  const url = `${API_ENDPOINTS.MATCH_DETAIL.replace('{id}', matchId)}/submit/`;
  const response = await api.post(url, solution);
  return response.data;
}

/**
 * Get match leaderboard
 * @param {string} matchId - Match ID
 * @returns {Promise<Array>} Match leaderboard
 */
export async function getMatchLeaderboard(matchId) {
  if (!matchId) {
    throw new Error('Match ID is required');
  }
  
  const url = `${API_ENDPOINTS.MATCH_DETAIL.replace('{id}', matchId)}/leaderboard/`;
  const response = await api.get(url);
  return response.data;
}

/**
 * Get available matches to join
 * @param {Object} params - Query parameters
 * @param {string} params.mode - Filter by mode
 * @param {string} params.status - Filter by status
 * @returns {Promise<Array>} Available matches
 */
export async function getAvailableMatches(params = {}) {
  const response = await api.get(`${API_ENDPOINTS.MATCH_CREATE}available/`, { params });
  return response.data;
}

/**
 * Get user's match history
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @returns {Promise<Object>} Match history
 */
export async function getMatchHistory(params = {}) {
  const { page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE } = params;
  
  const response = await api.get(`${API_ENDPOINTS.MATCH_CREATE}history/`, {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get user's active match
 * @returns {Promise<Object|null>} Active match or null
 */
export async function getActiveMatch() {
  const response = await api.get(`${API_ENDPOINTS.MATCH_CREATE}active/`);
  return response.data;
}

/**
 * Get match statistics for current user
 * @returns {Promise<Object>} Match stats
 */
export async function getMatchStats() {
  const response = await api.get(`${API_ENDPOINTS.MATCH_CREATE}stats/`);
  return response.data;
}

/**
 * Create tournament
 * @param {Object} tournamentData - Tournament data
 * @param {string} tournamentData.name - Tournament name
 * @param {string} tournamentData.mode - Match mode
 * @param {number} tournamentData.maxParticipants - Max participants
 * @param {string} tournamentData.startTime - Start time ISO string
 * @returns {Promise<Object>} Created tournament
 */
export async function createTournament(tournamentData) {
  const { name, mode, maxParticipants, startTime } = tournamentData;
  
  if (!name) {
    throw new Error('Tournament name is required');
  }
  
  const payload = { name, mode: mode || MATCH_MODES.TOURNAMENT };
  if (maxParticipants) payload.max_participants = maxParticipants;
  if (startTime) payload.start_time = startTime;
  
  const response = await api.post('/api/multiplayer/tournaments/', payload);
  return response.data;
}

/**
 * Join a tournament
 * @param {string} tournamentId - Tournament ID
 * @returns {Promise<Object>} Tournament data
 */
export async function joinTournament(tournamentId) {
  if (!tournamentId) {
    throw new Error('Tournament ID is required');
  }
  
  const url = `/api/multiplayer/tournaments/${tournamentId}/join/`;
  const response = await api.post(url);
  return response.data;
}

export default {
  createMatch,
  joinMatch,
  getMatch,
  leaveMatch,
  submitSolution,
  getMatchLeaderboard,
  getAvailableMatches,
  getMatchHistory,
  getActiveMatch,
  getMatchStats,
  createTournament,
  joinTournament,
};