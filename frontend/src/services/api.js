/**
 * API Service Layer for EconMind-Matrix
 * Centralizes all API calls to avoid hardcoded URLs
 */

// Get API base URL from environment or fallback to localhost
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Helper for making API requests with error handling
 */
async function request(url, options = {}) {
    const response = await fetch(url, options)
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }))
        throw new Error(error.detail || 'Request failed')
    }
    return response.json()
}

/**
 * Layer 1: Terminology Corpus API
 */
export const layer1 = {
    // Single search
    search: (term) => request(`${API_BASE}/search?term=${encodeURIComponent(term)}`),

    // Languages
    getLanguages: () => request(`${API_BASE}/api/languages`),

    // Batch operations
    batch: {
        create: (data) => request(`${API_BASE}/api/batch/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
        getTasks: () => request(`${API_BASE}/api/batch/tasks`),
        getStatus: (taskId) => request(`${API_BASE}/api/batch/${taskId}/status`),
        getTerms: (taskId) => request(`${API_BASE}/api/batch/${taskId}/terms`),
        start: (taskId) => request(`${API_BASE}/api/batch/${taskId}/start`, { method: 'POST' }),
        cancel: (taskId) => request(`${API_BASE}/api/batch/${taskId}/cancel`, { method: 'POST' }),
        retryFailed: (taskId) => request(`${API_BASE}/api/batch/${taskId}/retry-failed`, { method: 'POST' }),
        delete: (taskId) => request(`${API_BASE}/api/batch/${taskId}`, { method: 'DELETE' }),
        getGraph: (taskId) => request(`${API_BASE}/api/batch/${taskId}/graph`),
        exportUrl: (taskId, format) => `${API_BASE}/api/batch/${taskId}/export?format=${format}`,
    },

    // Corpus operations
    corpus: {
        getStatistics: () => request(`${API_BASE}/api/corpus/statistics`),
        checkDuplicates: (terms) => request(`${API_BASE}/api/corpus/check-duplicates`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ terms })
        }),
    },

    // Quality
    quality: {
        analyze: (taskId) => request(`${API_BASE}/api/quality/analyze${taskId ? `?task_id=${taskId}` : ''}`),
        getIssues: (params) => request(`${API_BASE}/api/quality/issues?${params}`),
        clean: (data) => request(`${API_BASE}/api/quality/clean`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }),
    },

    // System
    system: {
        getSetting: (key) => request(`${API_BASE}/api/system/settings/${key}`),
        updateSetting: (key, value) => request(`${API_BASE}/api/system/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value })
        }),
        reset: () => request(`${API_BASE}/api/system/reset?confirm=true`, { method: 'POST' }),
        backupUrl: () => `${API_BASE}/api/system/backup`,
        restoreUrl: () => `${API_BASE}/api/system/restore?confirm=true`,
    },
}

/**
 * Layer 2: Policy Corpus API
 */
export const layer2 = {
    base: `${API_BASE}/api/policy`,

    getStats: () => request(`${API_BASE}/api/policy/stats`),
    getReports: () => request(`${API_BASE}/api/policy/reports`),
    getReport: (id) => request(`${API_BASE}/api/policy/reports/${id}`),
    deleteReport: (id) => request(`${API_BASE}/api/policy/reports/${id}`, { method: 'DELETE' }),

    uploadReport: (formData) => fetch(`${API_BASE}/api/policy/upload`, {
        method: 'POST',
        body: formData
    }).then(r => r.json()),

    getAlignments: (params = '') => request(`${API_BASE}/api/policy/alignments${params ? `?${params}` : ''}`),
    runAlignment: (data) => request(`${API_BASE}/api/policy/align`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }),

    getTopics: () => request(`${API_BASE}/api/policy/topics`),
    searchTerm: (term) => request(`${API_BASE}/api/policy/search/${encodeURIComponent(term)}`),

    backupUrl: () => `${API_BASE}/api/policy/backup`,
    exportUrl: (format) => `${API_BASE}/api/policy/export?format=${format}`,
}

/**
 * Layer 3: Sentiment Corpus API
 */
export const layer3 = {
    base: `${API_BASE}/api/sentiment`,

    getStats: () => request(`${API_BASE}/api/sentiment/stats`),
    getSources: () => request(`${API_BASE}/api/sentiment/sources`),

    // Articles
    getArticles: (params = '') => request(`${API_BASE}/api/sentiment/articles${params ? `?${params}` : ''}`),
    getArticle: (id) => request(`${API_BASE}/api/sentiment/articles/${id}`),
    deleteArticle: (id) => request(`${API_BASE}/api/sentiment/articles/${id}`, { method: 'DELETE' }),

    // Crawling
    getCrawlStatus: () => request(`${API_BASE}/api/sentiment/crawl/status`),
    startCrawl: (params) => request(`${API_BASE}/api/sentiment/crawl?${params}`, { method: 'POST' }),
    stopCrawl: () => request(`${API_BASE}/api/sentiment/crawl/stop`, { method: 'POST' }),

    // Annotations
    getAnnotations: (params = '') => request(`${API_BASE}/api/sentiment/annotations${params ? `?${params}` : ''}`),
    annotate: (params) => request(`${API_BASE}/api/sentiment/annotate?${params}`, { method: 'POST' }),

    // Trends
    getTrend: (term, daysBack) => request(`${API_BASE}/api/sentiment/trend/${encodeURIComponent(term)}?days_back=${daysBack}`),
    getHotTerms: (daysBack = 7, limit = 10) => request(`${API_BASE}/api/sentiment/trends/hot?days_back=${daysBack}&limit=${limit}`),

    backupUrl: () => `${API_BASE}/api/sentiment/backup`,
    exportUrl: (type, format) => `${API_BASE}/api/sentiment/export/${type}?format=${format}`,
}

/**
 * Unified API (Phase 4 Integration)
 */
export const unified = {
    base: `${API_BASE}/api/v1`,

    // Unified search across all three layers
    search: (term, options = {}) => {
        const params = new URLSearchParams()
        if (options.includeLayer1 !== undefined) params.append('include_layer1', options.includeLayer1)
        if (options.includeLayer2 !== undefined) params.append('include_layer2', options.includeLayer2)
        if (options.includeLayer3 !== undefined) params.append('include_layer3', options.includeLayer3)
        if (options.daysBack) params.append('days_back', options.daysBack)
        const queryStr = params.toString()
        return request(`${API_BASE}/api/v1/search/${encodeURIComponent(term)}${queryStr ? `?${queryStr}` : ''}`)
    },

    // Trend analysis for a term
    trend: (term, daysBack = 30) => request(`${API_BASE}/api/v1/trend/${encodeURIComponent(term)}?days_back=${daysBack}`),

    // Health check
    health: () => request(`${API_BASE}/api/v1/health`),
}

// Export API base for components that need direct access
export { API_BASE }

// Default export for convenience
export default { layer1, layer2, layer3, unified, API_BASE }
