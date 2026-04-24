/**
 * SkillTree AI - Skill Store
 * Zustand store for skill tree state management
 * @module store/skillStore
 */

import { create } from 'zustand';
import * as skillApi from '../api/skillApi';
import { SKILL_STATUS, SKILL_NODE_TYPES } from '../constants';

/**
 * @typedef {Object} SkillNode
 * @property {number|string} id - Node ID
 * @property {string} name - Skill name
 * @property {string} description - Skill description
 * @property {string} type - Node type (core, advanced, elite, legendary)
 * @property {string} status - Node status (locked, available, in_progress, completed)
 * @property {number} xpCost - XP cost to unlock
 * @property {number} xpReward - XP reward for completion
 * @property {Array<string>} prerequisites - Array of prerequisite skill IDs
 * @property {string} category - Skill category
 * @property {string} icon - Icon identifier
 * @property {number} order - Display order
 */

/**
 * @typedef {Object} SkillState
 * @property {Array<SkillNode>} skills - All skills
 * @property {Object|null} skillTree - Full skill tree data
 * @property {SkillNode|null} selectedSkill - Currently selected skill
 * @property {boolean} isLoading - Loading state
 * @property {string|null} error - Error message
 * @property {Object} filters - Current filters
 * @property {function} fetchSkills - Fetch skills list
 * @property {function} fetchSkillTree - Fetch full skill tree
 * @property {function} selectSkill - Select a skill
 * @property {function} unlockSkill - Unlock a skill
 * @property {function} startLearning - Start learning a skill
 * @property {function} completeSkill - Complete a skill
 * @property {function} setFilters - Set filters
 * @property {function} clearError - Clear error
 */

/**
 * Create skill store
 * @type {import('zustand').UseStore<SkillState>}
 */
const useSkillStore = create((set, get) => ({
  // State
  skills: [],
  skillTree: null,
  selectedSkill: null,
  isLoading: false,
  error: null,
  filters: {
    category: null,
    status: null,
    type: null,
  },

  // Fetch skills list
  fetchSkills: async (params = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await skillApi.getSkills(params);
      
      set({
        skills: data.results || data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch skills';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch full skill tree
  fetchSkillTree: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await skillApi.getSkillTree();
      
      set({
        skillTree: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch skill tree';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Fetch single skill
  fetchSkill: async (skillId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await skillApi.getSkill(skillId);
      
      set({
        selectedSkill: data,
        isLoading: false,
      });
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to fetch skill';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Select a skill
  selectSkill: (skill) => {
    set({ selectedSkill: skill });
  },

  // Clear selected skill
  clearSelectedSkill: () => {
    set({ selectedSkill: null });
  },

  // Unlock a skill
  unlockSkill: async (skillId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await skillApi.unlockSkill(skillId);
      
      // Update skills list
      set((state) => ({
        skills: state.skills.map((s) => 
          s.id === skillId ? { ...s, status: SKILL_STATUS.AVAILABLE } : s
        ),
        selectedSkill: state.selectedSkill?.id === skillId ? data : state.selectedSkill,
        isLoading: false,
      }));
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to unlock skill';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Start learning a skill
  startLearning: async (skillId) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await skillApi.startLearning(skillId);
      
      // Update skills list
      set((state) => ({
        skills: state.skills.map((s) => 
          s.id === skillId ? { ...s, status: SKILL_STATUS.IN_PROGRESS } : s
        ),
        selectedSkill: state.selectedSkill?.id === skillId ? data : state.selectedSkill,
        isLoading: false,
      }));
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to start learning';
      set({ isLoading: false, error: errorMessage });
      throw error;
    }
  },

  // Complete a skill
  completeSkill: async (skillId, completionData = {}) => {
    set({ isLoading: true, error: null });
    
    try {
      const data = await skillApi.completeSkill(skillId, completionData);
      
      // Update skills list
      set((state) => ({
        skills: state.skills.map((s) => 
          s.id === skillId ? { ...s, status: SKILL_STATUS.COMPLETED } : s
        ),
        selectedSkill: state.selectedSkill?.id === skillId ? data : state.selectedSkill,
        isLoading: false,
      }));
      
      return data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Failed to complete skill';
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
        category: null,
        status: null,
        type: null,
      },
    });
  },

  // Clear error
  clearError: () => {
    set({ error: null });
  },

  // Get filtered skills
  getFilteredSkills: () => {
    const { skills, filters } = get();
    
    return skills.filter((skill) => {
      if (filters.category && skill.category !== filters.category) return false;
      if (filters.status && skill.status !== filters.status) return false;
      if (filters.type && skill.type !== filters.type) return false;
      return true;
    });
  },

  // Get skills by status
  getSkillsByStatus: (status) => {
    const { skills } = get();
    return skills.filter((s) => s.status === status);
  },

  // Get available skills (prerequisites met)
  getAvailableSkills: () => {
    const { skills } = get();
    return skills.filter((s) => s.status === SKILL_STATUS.AVAILABLE);
  },

  // Get completed skills
  getCompletedSkills: () => {
    const { skills } = get();
    return skills.filter((s) => s.status === SKILL_STATUS.COMPLETED);
  },
}));

export default useSkillStore;