/**
 * api.js — Central API service layer.
 * All backend communication goes through this module.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

/**
 * Helper to map HTTP status codes to user-friendly Indonesian messages
 */
function getErrorMessage(status, defaultDetail) {
  switch (status) {
    case 400: return 'Permintaan tidak valid. Pastikan format data sudah benar.';
    case 401: return 'Sesi telah habis. Silakan login kembali.';
    case 403: return 'Akses ditolak. Website menolak akses otomatis.';
    case 404: return 'Data atau halaman tidak ditemukan.';
    case 409: return 'Data sudah ada (konflik).';
    case 422: return 'Format konten tidak dapat diproses.';
    case 429: return 'Terlalu banyak permintaan. Silakan coba lagi nanti.';
    case 500: return 'Terjadi kesalahan internal pada server.';
    case 502: return 'Website sumber tidak dapat dihubungi.';
    case 504: return 'Website terlalu lama merespons.';
    default: return defaultDetail || `Terjadi kesalahan (HTTP ${status}).`;
  }
}

/** Generic GET request */
async function get(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'Bypass-Tunnel-Reminder': 'true' },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail = getErrorMessage(response.status, err.detail);
    throw { status: response.status, detail };
  }
  return response.json();
}

/** Generic POST request */
async function post(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json', 'Bypass-Tunnel-Reminder': 'true' },
    body: JSON.stringify(body),
  });
  
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = getErrorMessage(response.status, data.detail);
    throw { status: response.status, detail };
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

/**
 * Get analysis history list (Phase 5C-2)
 * @param {Object} params - Query parameters (limit, offset, language, category, sentiment)
 * @returns {Promise<AnalysisListResponse>}
 */
export async function getAnalysisHistory(params = {}) {
  const queryParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      queryParams.append(key, value);
    }
  }
  const queryString = queryParams.toString();
  const path = `/api/analyses${queryString ? '?' + queryString : ''}`;
  return get(path);
}

/**
 * Get full detail of an analysis (Phase 5C-2)
 * @param {number|string} id - Analysis ID
 * @returns {Promise<AnalysisDetailResponse>}
 */
export async function getAnalysisDetail(id) {
  return get(`/api/analyses/${id}`);
}

/**
 * Get dashboard analytics statistics (Phase 6)
 * @returns {Promise<DashboardStats>}
 */
export async function getDashboardStats() {
  return get('/api/dashboard/stats');
}

export default { 
  checkHealth, 
  extractArticle, 
  listArticles, 
  analyzeArticle,
  getAnalysisHistory,
  getAnalysisDetail,
  getDashboardStats,
};
