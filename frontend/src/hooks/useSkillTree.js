/**
 * SkillTree AI - Skill Tree Hook
 * Custom hook for skill tree interactions and state
 * @module hooks/useSkillTree
 */

import { useEffect, useCallback, useMemo } from 'react';
import useSkillStore from '../store/skillStore';
import { SKILL_STATUS } from '../constants';

/**
 * Custom hook for skill tree operations
 * @param {Object} options - Hook options
 * @param {boolean} options.autoFetch - Auto-fetch skill tree on mount
 * @returns {Object} Skill tree methods and state
 */
export function useSkillTree(options = {}) {
  const { autoFetch = true } = options;

  const {
    skillTree,
    skills,
    selectedSkill,
    isLoading,
    error,
    filters,
    fetchSkillTree,
    fetchSkills,
    fetchSkill,
    selectSkill,
    clearSelectedSkill,
    unlockSkill,
    startLearning,
    completeSkill,
    setFilters,
    clearFilters,
    clearError,
    getFilteredSkills,
    getAvailableSkills,
    getCompletedSkills,
  } = useSkillStore();

  // Auto-fetch skill tree on mount
  useEffect(() => {
    if (autoFetch) {
      fetchSkillTree();
    }
  }, [autoFetch, fetchSkillTree]);

  /**
   * Get skill by ID from store
   * @param {number|string} skillId - Skill ID
   * @returns {Object|null} Skill object
   */
  const getSkillById = useCallback((skillId) => {
    return skills.find((s) => s.id === skillId) || null;
  }, [skills]);

  /**
   * Check if a skill is unlockable (prerequisites met)
   * @param {Object} skill - Skill object
   * @returns {boolean} Whether skill can be unlocked
   */
  const isSkillUnlockable = useCallback((skill) => {
    if (!skill?.prerequisites?.length) return true;
    
    return skill.prerequisites.every((prereqId) => {
      const prereq = getSkillById(prereqId);
      return prereq?.status === SKILL_STATUS.COMPLETED;
    });
  }, [getSkillById]);

  /**
   * Get skills that can be unlocked
   * @returns {Array} Unlockable skills
   */
  const unlockableSkills = useMemo(() => {
    return skills.filter((skill) => 
      skill.status === SKILL_STATUS.AVAILABLE && isSkillUnlockable(skill)
    );
  }, [skills, isSkillUnlockable]);

  /**
   * Get skill tree as nodes and edges for visualization
   * @returns {Object} { nodes, edges }
   */
  const treeVisualization = useMemo(() => {
    if (!skillTree) {
      return { nodes: [], edges: [] };
    }

    const nodes = skills.map((skill) => ({
      id: skill.id,
      label: skill.name,
      type: skill.type,
      status: skill.status,
      x: skill.x || 0,
      y: skill.y || 0,
    }));

    const edges = [];
    skills.forEach((skill) => {
      if (skill.prerequisites?.length) {
        skill.prerequisites.forEach((prereqId) => {
          edges.push({
            from: prereqId,
            to: skill.id,
          });
        });
      }
    });

    return { nodes, edges };
  }, [skillTree, skills]);

  /**
   * Get progress statistics
   * @returns {Object} Progress stats
   */
  const progressStats = useMemo(() => {
    const total = skills.length;
    const completed = skills.filter((s) => s.status === SKILL_STATUS.COMPLETED).length;
    const inProgress = skills.filter((s) => s.status === SKILL_STATUS.IN_PROGRESS).length;
    const available = skills.filter((s) => s.status === SKILL_STATUS.AVAILABLE).length;
    const locked = skills.filter((s) => s.status === SKILL_STATUS.LOCKED).length;

    return {
      total,
      completed,
      inProgress,
      available,
      locked,
      completionPercentage: total > 0 ? Math.round((completed / total) * 100) : 0,
    };
  }, [skills]);

  /**
   * Handle skill click
   * @param {Object} skill - Clicked skill
   */
  const handleSkillClick = useCallback((skill) => {
    selectSkill(skill);
  }, [selectSkill]);

  /**
   * Handle skill unlock
   * @param {number|string} skillId - Skill ID
   */
  const handleUnlock = useCallback(async (skillId) => {
    await unlockSkill(skillId);
  }, [unlockSkill]);

  /**
   * Handle start learning
   * @param {number|string} skillId - Skill ID
   */
  const handleStartLearning = useCallback(async (skillId) => {
    await startLearning(skillId);
  }, [startLearning]);

  /**
   * Handle complete skill
   * @param {number|string} skillId - Skill ID
   * @param {Object} completionData - Completion data
   */
  const handleComplete = useCallback(async (skillId, completionData) => {
    await completeSkill(skillId, completionData);
  }, [completeSkill]);

  return {
    // State
    skillTree,
    skills,
    selectedSkill,
    isLoading,
    error,
    filters,
    
    // Computed
    unlockableSkills,
    treeVisualization,
    progressStats,
    filteredSkills: getFilteredSkills(),
    availableSkills: getAvailableSkills(),
    completedSkills: getCompletedSkills(),
    
    // Actions
    fetchSkillTree,
    fetchSkills,
    fetchSkill,
    selectSkill,
    clearSelectedSkill,
    unlockSkill,
    startLearning,
    completeSkill,
    setFilters,
    clearFilters,
    clearError,
    
    // Helpers
    getSkillById,
    isSkillUnlockable,
    handleSkillClick,
    handleUnlock,
    handleStartLearning,
    handleComplete,
  };
}

export default useSkillTree;