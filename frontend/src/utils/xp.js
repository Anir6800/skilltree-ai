/**
 * SkillTree AI - XP Utility Functions
 * @module utils/xp
 */

import { XP_THRESHOLDS, RANK_TIERS, getLevelFromXP, getXPForNextLevel, getRankFromLevel } from '../constants';

/**
 * Calculate XP progress percentage to next level
 * @param {number} xp - Current XP
 * @param {number} level - Current level
 * @returns {number} Progress percentage (0-100)
 */
export function calculateXPProgress(xp, level) {
  if (level < 1 || level > XP_THRESHOLDS.length) return 0;
  
  const currentThreshold = XP_THRESHOLDS[level - 1] || 0;
  const nextThreshold = getXPForNextLevel(level);
  
  const xpInLevel = xp - currentThreshold;
  const xpNeeded = nextThreshold - currentThreshold;
  
  if (xpNeeded <= 0) return 100;
  
  return Math.min(100, Math.max(0, (xpInLevel / xpNeeded) * 100));
}

/**
 * Calculate total XP needed for a specific level
 * @param {number} level - Target level
 * @returns {number} Total XP needed
 */
export function getTotalXPForLevel(level) {
  if (level <= 1) return 0;
  if (level > XP_THRESHOLDS.length) {
    const lastKnown = XP_THRESHOLDS[XP_THRESHOLDS.length - 1];
    const extraLevels = level - XP_THRESHOLDS.length;
    return lastKnown + extraLevels * 150;
  }
  return XP_THRESHOLDS[level - 1];
}

/**
 * Calculate XP reward for completing a quest
 * @param {string} difficulty - Quest difficulty
 * @param {number} baseXP - Base XP value
 * @returns {number} Total XP reward
 */
export function calculateQuestXP(difficulty, baseXP) {
  const multipliers = {
    easy: 1,
    medium: 1.5,
    hard: 2,
    expert: 3,
  };
  
  const multiplier = multipliers[difficulty] || 1;
  return Math.round(baseXP * multiplier);
}

/**
 * Calculate XP reward for winning a match
 * @param {number} playerRank - Player's current rank
 * @param {boolean} isVictory - Whether the match was won
 * @param {number} baseXP - Base XP value
 * @returns {number} XP reward (can be negative for loss)
 */
export function calculateMatchXP(playerRank, isVictory, baseXP = 50) {
  const rankMultipliers = {
    Novice: 1,
    Apprentice: 1.2,
    Journeyman: 1.4,
    Expert: 1.6,
    Master: 1.8,
    Grandmaster: 2,
    Legend: 2.5,
  };
  
  const multiplier = rankMultipliers[playerRank] || 1;
  
  if (isVictory) {
    return Math.round(baseXP * multiplier);
  }
  return Math.round(-baseXP * multiplier * 0.3);
}

/**
 * Calculate skill unlock cost
 * @param {string} nodeType - Skill node type
 * @param {number} currentLevel - Player's current level
 * @returns {number} XP cost to unlock
 */
export function calculateSkillCost(nodeType, currentLevel) {
  const baseCosts = {
    core: 0,
    advanced: 50,
    elite: 150,
    legendary: 500,
  };
  
  const baseCost = baseCosts[nodeType] || 0;
  const levelDiscount = Math.max(0, (currentLevel - 1) * 5);
  
  return Math.max(0, baseCost - levelDiscount);
}

/**
 * Calculate mentor XP bonus
 * @param {number} mentorLevel - Mentor player's level
 * @param {number} baseXP - Base XP being earned
 * @returns {number} Bonus XP percentage
 */
export function calculateMentorBonus(mentorLevel, baseXP) {
  const bonusPerLevel = 0.5;
  const maxBonus = 25;
  
  const bonus = Math.min(maxBonus, mentorLevel * bonusPerLevel);
  return Math.round(baseXP * (bonus / 100));
}

/**
 * Validate XP value
 * @param {*} xp - Value to validate
 * @returns {boolean} Whether XP is valid
 */
export function isValidXP(xp) {
  return typeof xp === 'number' && xp >= 0 && Number.isFinite(xp);
}

/**
 * Get XP breakdown for display
 * @param {number} xp - Current XP
 * @returns {Object} XP breakdown object
 */
export function getXPBreakdown(xp) {
  const level = getLevelFromXP(xp);
  const rank = getRankFromLevel(level);
  const xpForNextLevel = getXPForNextLevel(level);
  const progress = calculateXPProgress(xp, level);
  const xpInCurrentLevel = xp - (XP_THRESHOLDS[level - 1] || 0);
  
  return {
    level,
    rank,
    xp,
    xpForNextLevel,
    xpInCurrentLevel,
    xpNeeded: xpForNextLevel - (XP_THRESHOLDS[level - 1] || 0),
    progress: Math.round(progress),
  };
}

/**
 * Calculate streak bonus XP
 * @param {number} streakDays - Number of consecutive days
 * @param {number} baseXP - Base XP for the activity
 * @returns {number} Bonus XP from streak
 */
export function calculateStreakBonus(streakDays, baseXP) {
  if (streakDays < 3) return 0;
  
  const bonusMultipliers = {
    3: 1.1,
    7: 1.25,
    14: 1.5,
    30: 2,
    60: 2.5,
    100: 3,
  };
  
  let multiplier = 1;
  for (const [days, mult] of Object.entries(bonusMultipliers)) {
    if (streakDays >= parseInt(days)) {
      multiplier = mult;
    }
  }
  
  return Math.round(baseXP * (multiplier - 1));
}

/**
 * Calculate level-up bonus XP
 * @param {number} newLevel - The new level reached
 * @returns {number} Bonus XP awarded
 */
export function calculateLevelUpBonus(newLevel) {
  const baseBonus = 50;
  const levelBonus = newLevel * 25;
  return baseBonus + levelBonus;
}