/**
 * SkillTree AI - Study Groups API Client
 * Handles all group-related API calls.
 */

import { API_BASE_URL } from '../constants';
import { getAccessToken } from './api';

const GROUPS_API = `${API_BASE_URL}/api/groups`;

/**
 * Create a new study group.
 * @param {string} name - Group name
 * @returns {Promise<Object>} Created group data
 */
export async function createGroup(name) {
  const response = await fetch(`${GROUPS_API}/create/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAccessToken()}`,
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to create group');
  }

  return response.json();
}

/**
 * Join a study group via invite code.
 * @param {string} inviteCode - 6-character invite code
 * @returns {Promise<Object>} Group data
 */
export async function joinGroup(inviteCode) {
  const response = await fetch(`${GROUPS_API}/join/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAccessToken()}`,
    },
    body: JSON.stringify({ invite_code: inviteCode }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to join group');
  }

  return response.json();
}

/**
 * Get the authenticated user's study group.
 * @returns {Promise<Object>} Group data with members and goals
 */
export async function getMyGroup() {
  const response = await fetch(`${GROUPS_API}/my-group/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  if (!response.ok) {
    if (response.status === 404) {
      return null;
    }
    throw new Error('Failed to fetch group');
  }

  return response.json();
}

/**
 * Get group leaderboard (members ranked by XP this week).
 * @param {number} groupId - Group ID
 * @returns {Promise<Object>} Leaderboard data
 */
export async function getGroupLeaderboard(groupId) {
  const response = await fetch(`${GROUPS_API}/${groupId}/leaderboard/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch leaderboard');
  }

  return response.json();
}

/**
 * Get group goals.
 * @param {number} groupId - Group ID
 * @returns {Promise<Array>} Array of goal objects
 */
export async function getGroupGoals(groupId) {
  const response = await fetch(`${GROUPS_API}/${groupId}/goals/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch goals');
  }

  return response.json();
}

/**
 * Create a new group goal.
 * @param {number} groupId - Group ID
 * @param {number} skillId - Skill ID
 * @param {string} targetDate - Target date (YYYY-MM-DD)
 * @returns {Promise<Object>} Created goal data
 */
export async function createGroupGoal(groupId, skillId, targetDate) {
  const response = await fetch(`${GROUPS_API}/${groupId}/goals/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getAccessToken()}`,
    },
    body: JSON.stringify({
      skill_id: skillId,
      target_date: targetDate,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to create goal');
  }

  return response.json();
}

/**
 * Get recent group messages.
 * @param {number} groupId - Group ID
 * @param {number} limit - Number of messages to fetch (default 50)
 * @returns {Promise<Array>} Array of message objects
 */
export async function getGroupMessages(groupId, limit = 50) {
  const response = await fetch(`${GROUPS_API}/${groupId}/messages/?limit=${limit}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch messages');
  }

  return response.json();
}

/**
 * Leave a study group.
 * @param {number} groupId - Group ID
 * @returns {Promise<Object>} Success message
 */
export async function leaveGroup(groupId) {
  const response = await fetch(`${GROUPS_API}/${groupId}/leave/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getAccessToken()}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to leave group');
  }

  return response.json();
}
