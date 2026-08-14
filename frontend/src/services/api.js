/**
 * api.js — Central API service layer.
 * All backend communication goes through this module.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Perform a GET request to the backend.
 * @param {string} path - The API path (e.g. '/api/health')
 * @returns {Promise<any>} Parsed JSON response
 */
async function get(path) {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error — status: ${response.status}`);
  }

  return response.json();
}

/**
 * Check backend health status.
 * @returns {Promise<{ status: string, service: string }>}
 */
export async function checkHealth() {
  return get('/api/health');
}

export default { checkHealth };
