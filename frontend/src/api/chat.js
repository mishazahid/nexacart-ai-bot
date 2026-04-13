import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

/**
 * Send a customer query to the /chat endpoint.
 *
 * @param {string} query - The user's question text.
 * @param {string|null} sessionId - Optional session UUID for continuity.
 * @returns {Promise<Object>} The full API response data object.
 */
export async function sendMessage(query, sessionId = null, history = []) {
  try {
    const payload = { query };
    if (sessionId) payload.session_id = sessionId;
    if (history && history.length > 0) payload.history = history;

    const response = await apiClient.post('/chat', payload);
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(
        error.response.data?.detail ||
          `Server error: ${error.response.status}`
      );
    }
    if (error.request) {
      throw new Error(
        'Unable to reach the server. Please check your connection.'
      );
    }
    throw new Error(error.message || 'An unexpected error occurred.');
  }
}

/**
 * Check the health of the backend API.
 *
 * @returns {Promise<Object>} The health response data.
 */
export async function checkHealth() {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch {
    return { status: 'error', index_loaded: false };
  }
}
