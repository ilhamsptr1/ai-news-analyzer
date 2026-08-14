/**
 * api.js — Central API service layer.
 * All backend communication goes through this module.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/** Generic GET request */
async function get(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw { status: response.status, detail: err.detail || `HTTP ${response.status}` };
  }
  return response.json();
}

/** Generic POST request */
async function post(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw { status: response.status, detail: data.detail || `HTTP ${response.status}` };
  }
  return data;
}

/**
 * Check backend health status.
 * @returns {Promise<{ status: string, service: string }>}
 */
export async function checkHealth() {
  return get('/api/health');
}

/**
 * Extract and save an article from a public URL.
 * @param {string} url - The public article URL.
 * @returns {Promise<ArticleResponse>}
 * @throws {{ status: number, detail: string }} on error
 */
export async function extractArticle(url) {
  return post('/api/articles/extract', { url });
}

/**
 * List stored articles (paginated).
 * @param {number} skip
 * @param {number} limit
 * @returns {Promise<{ total: number, articles: ArticleResponse[] }>}
 */
export async function listArticles(skip = 0, limit = 20) {
  return get(`/api/articles?skip=${skip}&limit=${limit}`);
}

/**
 * Run the full AI analysis pipeline on a URL.
 * @param {string} url - The public article URL.
 * @param {number} [topKeywords=10]
 * @returns {Promise<ArticleAnalyzeResponse | UnsupportedLanguageResponse>}
 */
export async function analyzeArticle(url, topKeywords = 10) {
  return post('/api/articles/analyze', { url, top_keywords: topKeywords });
}

export default { checkHealth, extractArticle, listArticles, analyzeArticle };
