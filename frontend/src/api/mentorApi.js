/**
 * SkillTree AI - Mentor API
 * @module api/mentorApi
 */

import api from './api';
import { API_ENDPOINTS, PAGINATION } from '../constants';

/**
 * Get list of mentors
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {number} params.pageSize - Items per page
 * @param {string} params.specialty - Filter by specialty
 * @param {number} params.minLevel - Filter by minimum level
 * @returns {Promise<Object>} Paginated mentors list
 */
export async function getMentors(params = {}) {
  const { page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE, specialty, minLevel } = params;
  
  const queryParams = {
    page,
    page_size: pageSize,
  };
  
  if (specialty) queryParams.specialty = specialty;
  if (minLevel) queryParams.min_level = minLevel;
  
  const response = await api.get(API_ENDPOINTS.MENTOR_LIST, { params: queryParams });
  return response.data;
}

/**
 * Get mentor details
 * @param {number|string} mentorId - Mentor ID
 * @returns {Promise<Object>} Mentor details
 */
export async function getMentor(mentorId) {
  if (!mentorId) {
    throw new Error('Mentor ID is required');
  }
  
  const url = API_ENDPOINTS.MENTOR_DETAIL.replace('{id}', mentorId);
  const response = await api.get(url);
  return response.data;
}

/**
 * Request mentorship from a mentor
 * @param {number|string} mentorId - Mentor ID
 * @param {string} message - Introduction message
 * @returns {Promise<Object>} Request result
 */
export async function requestMentorship(mentorId, message = '') {
  if (!mentorId) {
    throw new Error('Mentor ID is required');
  }
  
  const url = `${API_ENDPOINTS.MENTOR_DETAIL.replace('{id}', mentorId)}/request/`;
  const response = await api.post(url, { message });
  return response.data;
}

/**
 * Accept mentorship request
 * @param {number|string} requestId - Request ID
 * @returns {Promise<Object>} Updated request
 */
export async function acceptMentorshipRequest(requestId) {
  if (!requestId) {
    throw new Error('Request ID is required');
  }
  
  const url = `/api/mentor/requests/${requestId}/accept/`;
  const response = await api.post(url);
  return response.data;
}

/**
 * Decline mentorship request
 * @param {number|string} requestId - Request ID
 * @param {string} reason - Decline reason
 * @returns {Promise<void>}
 */
export async function declineMentorshipRequest(requestId, reason = '') {
  if (!requestId) {
    throw new Error('Request ID is required');
  }
  
  const url = `/api/mentor/requests/${requestId}/decline/`;
  await api.post(url, { reason });
}

/**
 * End mentorship relationship
 * @param {number|string} mentorshipId - Mentorship ID
 * @returns {Promise<void>}
 */
export async function endMentorship(mentorshipId) {
  if (!mentorshipId) {
    throw new Error('Mentorship ID is required');
  }
  
  const url = `/api/mentor/mentorships/${mentorshipId}/end/`;
  await api.post(url);
}

/**
 * Get my mentors (people mentoring me)
 * @returns {Promise<Array>} My mentors
 */
export async function getMyMentors() {
  const response = await api.get(`${API_ENDPOINTS.MENTOR_LIST}my-mentors/`);
  return response.data;
}

/**
 * Get my mentees (people I am mentoring)
 * @returns {Promise<Array>} My mentees
 */
export async function getMyMentees() {
  const response = await api.get(`${API_ENDPOINTS.MENTOR_LIST}my-mentees/`);
  return response.data;
}

/**
 * Get pending mentorship requests (for mentors)
 * @returns {Promise<Array>} Pending requests
 */
export async function getPendingRequests() {
  const response = await api.get(`${API_ENDPOINTS.MENTOR_LIST}pending-requests/`);
  return response.data;
}

/**
 * Get mentorship sessions
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} Sessions list
 */
export async function getMentorshipSessions(params = {}) {
  const { page = PAGINATION.DEFAULT_PAGE, pageSize = PAGINATION.DEFAULT_PAGE_SIZE } = params;
  
  const response = await api.get(`${API_ENDPOINTS.MENTOR_LIST}sessions/`, {
    params: { page, page_size: pageSize },
  });
  return response.data;
}

/**
 * Schedule mentorship session
 * @param {Object} sessionData - Session data
 * @param {number|string} sessionData.mentorId - Mentor ID
 * @param {string} sessionData.scheduledTime - ISO datetime
 * @param {string} sessionData.topic - Session topic
 * @returns {Promise<Object>} Created session
 */
export async function scheduleSession(sessionData) {
  const { mentorId, scheduledTime, topic } = sessionData;
  
  if (!mentorId) {
    throw new Error('Mentor ID is required');
  }
  
  if (!scheduledTime) {
    throw new Error('Scheduled time is required');
  }
  
  const payload = {
    mentor_id: mentorId,
    scheduled_time: scheduledTime,
    topic: topic || '',
  };
  
  const response = await api.post(`${API_ENDPOINTS.MENTOR_LIST}sessions/`, payload);
  return response.data;
}

/**
 * Get mentor specialties/categories
 * @returns {Promise<Array>} List of specialties
 */
export async function getMentorSpecialties() {
  const response = await api.get(`${API_ENDPOINTS.MENTOR_LIST}specialties/`);
  return response.data;
}

/**
 * Search mentors
 * @param {string} query - Search query
 * @param {Object} filters - Additional filters
 * @returns {Promise<Object>} Search results
 */
export async function searchMentors(query, filters = {}) {
  if (!query) {
    throw new Error('Search query is required');
  }
  
  const params = { q: query, ...filters };
  const response = await api.get(`${API_ENDPOINTS.MENTOR_LIST}search/`, { params });
  return response.data;
}

export default {
  getMentors,
  getMentor,
  requestMentorship,
  acceptMentorshipRequest,
  declineMentorshipRequest,
  endMentorship,
  getMyMentors,
  getMyMentees,
  getPendingRequests,
  getMentorshipSessions,
  scheduleSession,
  getMentorSpecialties,
  searchMentors,
};