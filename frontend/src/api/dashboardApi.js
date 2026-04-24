/**
 * SkillTree AI - Dashboard API
 * Service for fetching aggregated dashboard data
 * @module api/dashboardApi
 */

import api from './api';

/**
 * Fetch combined dashboard data for the authenticated user
 * @returns {Promise<Object>} Dashboard data
 */
export const fetchDashboardData = async () => {
  try {
    const response = await api.get('/api/users/dashboard/');
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};

const dashboardApi = {
  fetchDashboardData,
};

export default dashboardApi;
