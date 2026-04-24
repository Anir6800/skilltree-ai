/**
 * SkillTree AI - Quest Store
 * Zustand store for quest state management
 * @module store/questStore
 */

import { create } from 'zustand';
import * as questApi from '../api/questApi';
import { QUEST_STATUS, QUEST_DIFFICULTY } from '../constants';

/**
 * @typedef {Object} Quest
 * @property {number|string} id - Quest ID
 * @property {string} title - Quest title
 * @property {string} description - Quest description
 * @property {string} difficulty - Difficulty level
 * @property {string} status - Quest status
 * @property {number} xpReward - XP reward
 * @property {string} category - Quest category
 * @property {string} skillId - Related skill ID
 * @property {string} createdAt - Creation date
 * @property {string} completedAt - Completion date
 */

/**
 * @typedef {Object} QuestState
 * @property {Array<Quest>} quests - All quests
 * @property {Array<Quest>} activeQuests - Active quests
 * @property {Quest|null} selectedQuest - Currently selected quest
 * @property {boolean} isLoading - Loading state
 * @property {string|null} error - Error message
 * @property {Object} filters - Current filters
 * @property {function} fetchQuests - Fetch quests list
 * @property {function} fetchActiveQuests - Fetch active quests
 * @property {function} selectQuest - Select a quest
 * @property {function} acceptQuest - Accept a quest
 * @property {function} completeQuest - Complete a quest
 * @property {function} abandonQuest - Abandon a quest
 * @property {function} setFilters - Set filters
 * @property {function} clearError - Clear error
 */

/**
 * Create quest store
 * @type {import('zustand').UseStore<QuestState>}
 */
const useQuestStore = create((set, get) => ({
  // State
  quests: [],
  activeQuests: [],
  completedQuests: [],
  selectedQuest: null,
  isLoading: false,
  error: null,
  filters: {
    difficulty: null,
    status: null,
    category: null,
  },

  // Fetch quests list
  fetchQuests: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.getQuests(params);
      
      set({
        quests: data.results || data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch quests';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch active quests
  fetchActiveQuests: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.getActiveQuests();
      
      set({
        activeQuests: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch active quests';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch completed quests
  fetchCompletedQuests: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.getCompletedQuests(params);
      
      set({
        completedQuests: data.results || data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch completed quests';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch available quests
  fetchAvailableQuests: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.getAvailableQuests();
      
      set({ isLoading: false });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch available quests';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch single quest
  fetchQuest: async (questId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.getQuest(questId);
      
      set({
        selectedQuest: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch quest';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Select a quest
  selectQuest: (quest) => {
    set({ selectedQuest: quest });
  },

  // Clear selected quest
  clearSelectedQuest: () => {
    set({ selectedQuest: null });
  },

  // Accept a quest
  acceptQuest: async (questId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.acceptQuest(questId);
      
      // Update quests list
      set((state) => ({
        quests: state.quests.map((q) => 
          q.id === questId ? { ...q, status: QUEST_STATUS.IN_PROGRESS } : q
        ),
        activeQuests: [...state.activeQuests, data],
        selectedQuest: state.selectedQuest?.id === questId ? data : state.selectedQuest,
        isLoading: false,
      }));
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to accept quest';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Complete a quest
  completeQuest: async (questId, completionData = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await questApi.completeQuest(questId, completionData);
      
      // Update quests list
      set((state) => ({
        quests: state.quests.map((q) => 
          q.id === questId ? { ...q, status: QUEST_STATUS.COMPLETED } : q
        ),
        activeQuests: state.activeQuests.filter((q) => q.id !== questId),
        completedQuests: [data, ...state.completedQuests],
        selectedQuest: state.selectedQuest?.id === questId ? data : state.selectedQuest,
        isLoading: false,
      }));
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to complete quest';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Abandon a quest
  abandonQuest: async (questId) => {
    set({ isLoading: true, error: null });
    
    try {
      await questApi.abandonQuest(questId);
      
      // Update quests list
      set((state) => ({
        quests: state.quests.map((q) => 
          q.id === questId ? { ...q, status: QUEST_STATUS.AVAILABLE } : q
        ),
        activeQuests: state.activeQuests.filter((q) => q.id !== questId),
        selectedQuest: state.selectedQuest?.id === questId ? null : state.selectedQuest,
        isLoading: false,
      }));
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to abandon quest';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Set filters
  setFilters: (filters) => {
    set((state) => ({
      filters: { ...state.filters, ...filters },
    }));
  },

  // Clear filters
  clearFilters: () => {
    set({
      filters: {
        difficulty: null,
        status: null,
        category: null,
      },
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Get filtered quests
  getFilteredQuests: () => {
    const { quests, filters } = get();
    
    return quests.filter((quest) => {
      if (filters.difficulty && quest.difficulty !== filters.difficulty) return false;
      if (filters.status && quest.status !== filters.status) return false;
      if (filters.category && quest.category !== filters.category) return false;
      return true;
    });
  },

  // Get quests by difficulty
  getQuestsByDifficulty: (difficulty) => {
    const { quests } = get();
    return quests.filter((q) => q.difficulty === difficulty);
  },

  // Get active quest count
  getActiveQuestCount: () => {
    const { activeQuests } = get();
    return activeQuests.length;
  },
}));

export default useQuestStore;