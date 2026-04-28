/**
 * SkillTree AI - Match/Multiplayer API
 * @module api/matchApi
 */

import api from './api';
import { API_ENDPOINTS, MATCH_MODES, MATCH_STATUS, PAGINATION } from '../constants';

/**
 * Create a new match
 * @param {Object} matchData - Match creation data
 * @param {number} matchData.quest_id - Quest ID for the match
 * @param {number} [matchData.max_participants=2] - Maximum players
 * @returns {Promise<Object>} Created match data with invite_code
 */
export async function createMatch(matchData) {
  const { quest_id, max_participants = 2 } = matchData;

  if (!quest_id) {
    throw new Error('quest_id is required');
  }

  const response = await api.post(API_ENDPOINTS.MATCH_CREATE, {
    quest_id,
    max_participants,
  });
  return response.data;
}

/**
 * Join an existing match by invite code
 * @param {string} inviteCode - Invite code (e.g. "MATCH-123")
 * @returns {Promise<Object>} Match data
 */
export async function joinMatch(inviteCode) {
  if (!inviteCode) {
    throw new Error('Invite code is required');
  }

  const response = await api.post(API_ENDPOINTS.MATCH_JOIN, { invite_code: inviteCode });
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
 * Submit match solution — uses the quest submit endpoint with match_id to bypass skill lock.
 * @param {string} matchId - Match ID
 * @param {Object} solution - Solution data
 * @param {string} solution.code - Submitted code
 * @param {string} solution.language - Programming language
 * @param {number} solution.questId - Quest ID
 * @returns {Promise<Object>} Submission result with submission_id for polling
 */
export async function submitSolution(matchId, solution) {
  if (!matchId) {
    throw new Error('Match ID is required');
  }

  if (!solution?.code || !solution?.language || !solution?.questId) {
    throw new Error('Code, language, and questId are required');
  }

  const url = API_ENDPOINTS.QUESTS_SUBMIT.replace('{id}', solution.questId);
  const response = await api.post(url, {
    code: solution.code,
    language: solution.language,
    match_id: matchId,
  });
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
 * Get available matches to join — uses the main list endpoint with status filter.
 * @param {Object} params - Query parameters
 * @param {string} params.status - Filter by status (default: 'waiting')
 * @returns {Promise<Array>} Available matches
 */
export async function getAvailableMatches(params = {}) {
  const response = await api.get(API_ENDPOINTS.MATCH_LIST, {
    params: { status: params.status || 'waiting', ...params },
  });
  const data = response.data;
  return Array.isArray(data) ? data : (data?.results ?? []);
}

/**
 * Get user's match history — uses the main list endpoint with finished status.
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @returns {Promise<Object>} Match history
 */
export async function getMatchHistory(params = {}) {
  const { page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE } = params;
  const response = await api.get(API_ENDPOINTS.MATCH_LIST, {
    params: { status: 'finished', page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Get user's active match — returns the first in_progress match the user is in.
 * @returns {Promise<Object|null>} Active match or null
 */
export async function getActiveMatch() {
  try {
    const response = await api.get(API_ENDPOINTS.MATCH_LIST, {
      params: { status: 'active' },
    });
    const data = response.data;
    const results = Array.isArray(data) ? data : (data?.results ?? []);
    return results[0] ?? null;
  } catch {
    return null;
  }
}

/**
 * Get match statistics for current user — derived from match history.
 * @returns {Promise<Object>} Match stats
 */
export async function getMatchStats() {
  try {
    const response = await api.get(API_ENDPOINTS.MATCH_LIST, {
      params: { status: 'finished', page_size: 100 },
    });
    const data = response.data;
    const matches = Array.isArray(data) ? data : (data?.results ?? []);
    return {
      total_matches: matches.length,
      wins: 0, // Would need user context to compute — return safe default
      losses: 0,
      win_rate: 0,
    };
  } catch {
    return { total_matches: 0, wins: 0, losses: 0, win_rate: 0 };
  }
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