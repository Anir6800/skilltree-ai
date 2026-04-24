/**
 * SkillTree AI - Match Store
 * Zustand store for multiplayer match state management
 * @module store/matchStore
 */

import { create } from 'zustand';
import * as matchApi from '../api/matchApi';
import { MATCH_STATUS, MATCH_MODES } from '../constants';

/**
 * @typedef {Object} Match
 * @property {string} id - Match ID
 * @property {string} mode - Match mode
 * @property {string} status - Match status
 * @property {Array} players - Match players
 * @property {Object} currentProblem - Current problem/challenge
 * @property {number} timeLimit - Time limit in seconds
 * @property {string} startTime - Start time
 * @property {string} endTime - End time
 */

/**
 * @typedef {Object} MatchState
 * @property {Match|null} currentMatch - Current active match
 * @property {Array} availableMatches - Available matches to join
 * @property {Array} matchHistory - Match history
 * @property {Object|null} matchStats - User's match statistics
 * @property {boolean} isLoading - Loading state
 * @property {string|null} error - Error message
 * @property {function} createMatch - Create new match
 * @property {function} joinMatch - Join existing match
 * @property {function} leaveMatch - Leave current match
 * @property {function} submitSolution - Submit solution
 * @property {function} fetchAvailableMatches - Fetch available matches
 * @property {function} fetchMatchHistory - Fetch match history
 * @property {function} fetchMatchStats - Fetch match statistics
 * @property {function} clearError - Clear error
 */

/**
 * Create match store
 * @type {import('zustand').UseStore<MatchState>}
 */
const useMatchStore = create((set, get) => ({
  // State
  currentMatch: null,
  availableMatches: [],
  matchHistory: [],
  matchStats: null,
  isLoading: false,
  error: null,

  // Create a new match
  createMatch: async (matchData) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.createMatch(matchData);
      
      set({
        currentMatch: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to create match';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Join an existing match
  joinMatch: async (matchId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.joinMatch(matchId);
      
      set({
        currentMatch: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to join match';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Leave current match
  leaveMatch: async () => {
    const { currentMatch } = get();
    
    if (!currentMatch?.id) return;
    
    set({ isLoading: true, error: null });
    
    try {
      await matchApi.leaveMatch(currentMatch.id);
      
      set({
        currentMatch: null,
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to leave match';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Get current match details
  fetchMatch: async (matchId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.getMatch(matchId);
      
      set({
        currentMatch: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch match';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Submit solution
  submitSolution: async (matchId, solution) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.submitSolution(matchId, solution);
      
      // Update current match with new data
      set((state) => ({
        currentMatch: state.currentMatch ? { ...state.currentMatch, ...data } : null,
        isLoading: false,
      }));
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to submit solution';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch available matches
  fetchAvailableMatches: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.getAvailableMatches(params);
      
      set({
        availableMatches: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch available matches';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch match history
  fetchMatchHistory: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.getMatchHistory(params);
      
      set({
        matchHistory: data.results || data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch match history';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch match statistics
  fetchMatchStats: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.getMatchStats();
      
      set({
        matchStats: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch match statistics';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Get active match
  fetchActiveMatch: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await matchApi.getActiveMatch();
      
      set({
        currentMatch: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch active match';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Update match state (from WebSocket)
  updateMatchState: (matchData) => {
    set((state) => ({
      currentMatch: state.currentMatch ? { ...state.currentMatch, ...matchData } : matchData,
    }));
  },

  // Clear current match
  clearCurrentMatch: () => {
    set({ currentMatch: null });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Check if in active match
  isInMatch: () => {
    const { currentMatch } = get();
    return currentMatch?.status === MATCH_STATUS.IN_PROGRESS;
  },

  // Get matches by mode
  getMatchesByMode: (mode) => {
    const { availableMatches } = get();
    return availableMatches.filter((m) => m.mode === mode);
  },

  // Get ranked matches only
  getRankedMatches: () => {
    return get().getMatchesByMode(MATCH_MODES.RANKED);
  },
}));

export default useMatchStore;