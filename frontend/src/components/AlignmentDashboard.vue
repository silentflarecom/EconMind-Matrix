<template>
  <div class="layer4-dashboard">
    <div class="dashboard-header">
      <h2>🏭 Layer 4: Semantic Alignment Pipeline</h2>
      <p class="subtitle">Offline batch alignment of Terms → Policy → Sentiment</p>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.totalCells }}</div>
          <div class="stat-label">Knowledge Cells</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.avgScore.toFixed(2) }}</div>
          <div class="stat-label">Avg Quality Score</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📜</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.policyPct }}%</div>
          <div class="stat-label">Policy Coverage</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📰</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.sentimentPct }}%</div>
          <div class="stat-label">Sentiment Coverage</div>
        </div>
      </div>
    </div>

    <!-- Knowledge Cells List -->
    <div class="cells-section">
      <div class="section-header">
        <h3>Knowledge Cells</h3>
        <div class="header-actions">
          <button class="export-btn" @click="exportJsonl" :disabled="cells.length === 0">
            📥 JSONL
          </button>
          <button class="export-btn" @click="exportCsv" :disabled="cells.length === 0">
            📊 CSV
          </button>
          <div class="llm-export-group">
            <select v-model="bulkFormat" class="bulk-format-select" :disabled="cells.length === 0">
              <option value="alpaca">Alpaca</option>
              <option value="sharegpt">ShareGPT</option>
              <option value="openai">OpenAI</option>
              <option value="dolly">Dolly</option>
              <option value="text">Text</option>
            </select>
            <button class="llm-export-btn" @click="exportLlmFormat(bulkFormat)" :disabled="cells.length === 0">
              🤖 Export LLM
            </button>
          </div>
          <button class="refresh-btn" @click="loadData" :disabled="loading">
            {{ loading ? 'Loading...' : '🔄 Refresh' }}
          </button>
        </div>
      </div>

      <!-- Language Info -->
      <div v-if="languageInfo.languages && languageInfo.languages.length > 0" class="language-info">
        <span class="lang-label">🌐 Languages:</span>
        <span v-for="lang in languageInfo.languages" :key="lang" class="lang-tag">
          {{ lang.toUpperCase() }} ({{ languageInfo.language_stats[lang] }})
        </span>
      </div>

      <div v-if="error" class="error-message">{{ error }}</div>

      <div v-if="cells.length === 0 && !loading" class="empty-state">
        <p>No Knowledge Cells found.</p>
        <p class="hint">Run the alignment pipeline to generate cells:</p>
        <code>python layer4_alignment/scripts/run_full_alignment.py</code>
      </div>

      <div v-else class="cells-grid">
        <div 
          v-for="cell in cells" 
          :key="cell.concept_id" 
          class="cell-card"
          :class="{ expanded: expandedCell === cell.concept_id }"
          @click="toggleCell(cell.concept_id)"
        >
          <div class="cell-header">
            <span class="cell-term">{{ cell.primary_term }}</span>
            <span class="cell-score" :class="getScoreClass(cell.metadata.quality_metrics.overall_score)">
              {{ cell.metadata.quality_metrics.overall_score.toFixed(2) }}
            </span>
          </div>
          
          <div class="cell-stats">
            <span class="badge lang">{{ Object.keys(cell.definitions).length }} langs</span>
            <span class="badge policy">{{ cell.policy_evidence.length }} policy</span>
            <span class="badge sentiment">{{ cell.sentiment_evidence.length }} sentiment</span>
          </div>

          <!-- Expanded Details -->
          <div v-if="expandedCell === cell.concept_id" class="cell-details" @click.stop>
            <!-- Definitions -->
            <div class="detail-section">
              <h4>📚 Definitions</h4>
              <div v-for="(def, lang) in cell.definitions" :key="lang" class="definition-item">
                <span class="lang-code">{{ lang.toUpperCase() }}</span>
                <span class="def-term">{{ def.term }}</span>
                <p class="def-summary">{{ truncate(def.summary, 200) }}</p>
              </div>
            </div>

            <!-- Policy Evidence -->
            <div v-if="cell.policy_evidence.length > 0" class="detail-section">
              <h4>📜 Policy Evidence</h4>
              <div v-for="evidence in cell.policy_evidence" :key="evidence.paragraph_id" class="evidence-item">
                <div class="evidence-header">
                  <span class="source-badge" :class="evidence.source">{{ evidence.source.toUpperCase() }}</span>
                  <span class="score">Score: {{ evidence.alignment_scores.final.toFixed(2) }}</span>
                </div>
                <p class="evidence-text">{{ truncate(evidence.text, 300) }}</p>
              </div>
            </div>

            <!-- Sentiment Evidence -->
            <div v-if="cell.sentiment_evidence.length > 0" class="detail-section">
              <h4>📰 Sentiment Evidence</h4>
              <div v-for="evidence in cell.sentiment_evidence" :key="evidence.article_id" class="evidence-item">
                <div class="evidence-header">
                  <span class="sentiment-badge" :class="evidence.sentiment.label">
                    {{ evidence.sentiment.label }}
                  </span>
                  <span class="source">{{ evidence.source }}</span>
                  <span class="score">Score: {{ evidence.alignment_scores.final.toFixed(2) }}</span>
                </div>
                <p class="evidence-title">{{ evidence.title }}</p>
              </div>
            </div>

            <!-- Per-Cell Export -->
            <div class="cell-export-section">
              <h4>🚀 Export This Cell</h4>
              <div class="export-controls">
                <select v-model="selectedFormat" class="format-select">
                  <option value="alpaca">Alpaca</option>
                  <option value="sharegpt">ShareGPT</option>
                  <option value="openai">OpenAI</option>
                  <option value="dolly">Dolly</option>
                  <option value="text">Plain Text</option>
                  <option value="jsonl">JSONL (Raw)</option>
                </select>
                <select v-model="selectedLang" class="lang-select">
                  <option v-for="lang in languageInfo.languages" :key="lang" :value="lang">
                    {{ getLanguageName(lang) }}
                  </option>
                </select>
                <button class="cell-export-btn" @click="exportCell(cell.concept_id)">
                  📥 Export
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quality Report -->
    <div v-if="qualityReport" class="report-section">
      <h3>📈 Quality Report</h3>
      <div class="report-content" v-html="qualityReport"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { API_BASE } from '../services/api'
import axios from 'axios'

const cells = ref([])
const loading = ref(false)
const error = ref(null)
const expandedCell = ref(null)
const qualityReport = ref(null)
const languageInfo = ref({ languages: [], language_stats: {} })

const stats = computed(() => {
  if (cells.value.length === 0) {
    return { totalCells: 0, avgScore: 0, policyPct: 0, sentimentPct: 0 }
  }
  
  const total = cells.value.length
  const withPolicy = cells.value.filter(c => c.policy_evidence.length > 0).length
  const withSentiment = cells.value.filter(c => c.sentiment_evidence.length > 0).length
  const avgScore = cells.value.reduce((sum, c) => sum + c.metadata.quality_metrics.overall_score, 0) / total
  
  return {
    totalCells: total,
    avgScore,
    policyPct: Math.round((withPolicy / total) * 100),
    sentimentPct: Math.round((withSentiment / total) * 100)
  }
})

const loadData = async () => {
  loading.value = true
  error.value = null
  
  try {
    // Load cells and language info in parallel
    const [cellsRes, langRes] = await Promise.all([
      axios.get(`${API_BASE}/api/v1/alignment/cells`),
      axios.get(`${API_BASE}/api/v1/alignment/languages`).catch(() => ({ data: { languages: [], language_stats: {} } }))
    ])
    cells.value = cellsRes.data.cells || []
    languageInfo.value = langRes.data
  } catch (err) {
    if (err.response && err.response.status === 404) {
      error.value = 'Alignment API endpoint not configured. Layer 4 is an offline pipeline.'
    } else {
      error.value = 'Could not load Knowledge Cells. Please run the alignment pipeline first.'
    }
    cells.value = []
  } finally {
    loading.value = false
  }
}

const exportJsonl = () => {
  window.open(`${API_BASE}/api/v1/alignment/export/jsonl`, '_blank')
}

const exportCsv = () => {
  window.open(`${API_BASE}/api/v1/alignment/export/csv`, '_blank')
}

// Per-cell export state
const selectedFormat = ref('alpaca')
const selectedLang = ref('en')
const bulkFormat = ref('alpaca')

const exportCell = (conceptId) => {
  const url = `${API_BASE}/api/v1/alignment/cell/${conceptId}/export?format=${selectedFormat.value}&lang=${selectedLang.value}`
  window.open(url, '_blank')
}

// Bulk LLM format export
const exportLlmFormat = (format) => {
  window.open(`${API_BASE}/api/v1/alignment/export/llm/${format}?lang=${selectedLang.value}`, '_blank')
}

const toggleCell = (conceptId) => {
  expandedCell.value = expandedCell.value === conceptId ? null : conceptId
}

const getScoreClass = (score) => {
  if (score >= 0.7) return 'high'
  if (score >= 0.5) return 'medium'
  return 'low'
}

const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// Language code to readable name mapping (supports 20+ Wikipedia languages)
const languageNames = {
  en: 'English',
  zh: '中文',
  ja: '日本語',
  ko: '한국어',
  de: 'Deutsch',
  fr: 'Français',
  es: 'Español',
  it: 'Italiano',
  pt: 'Português',
  ru: 'Русский',
  ar: 'العربية',
  hi: 'हिन्दी',
  th: 'ไทย',
  vi: 'Tiếng Việt',
  id: 'Bahasa Indonesia',
  nl: 'Nederlands',
  pl: 'Polski',
  tr: 'Türkçe',
  uk: 'Українська',
  he: 'עברית',
  sv: 'Svenska',
  cs: 'Čeština',
  fi: 'Suomi',
  el: 'Ελληνικά',
  hu: 'Magyar',
  ro: 'Română',
  da: 'Dansk',
  no: 'Norsk',
  bg: 'Български',
  ca: 'Català'
}

const getLanguageName = (code) => {
  return languageNames[code] || code.toUpperCase()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.layer4-dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 32px;
}

.dashboard-header h2 {
  font-size: 28px;
  margin-bottom: 8px;
  color: #1a1a2e;
}

.subtitle {
  color: #666;
  font-size: 14px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.stat-label {
  font-size: 12px;
  opacity: 0.9;
}

/* Cells Section */
.cells-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header h3 {
  margin: 0;
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.export-btn {
  background: #10b981;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s;
}

.export-btn:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-1px);
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.llm-export-group {
  display: flex;
  gap: 4px;
  align-items: center;
}

.bulk-format-select {
  padding: 8px 10px;
  border: 2px solid #8b5cf6;
  border-radius: 8px 0 0 8px;
  background: white;
  font-size: 12px;
  cursor: pointer;
  outline: none;
}

.llm-export-btn {
  background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 0 8px 8px 0;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.3s;
}

.llm-export-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
}

.llm-export-btn:disabled, .bulk-format-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.language-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.lang-label {
  font-weight: 600;
  color: #0369a1;
}

.lang-tag {
  background: #0ea5e9;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.refresh-btn {
  background: #667eea;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.refresh-btn:hover:not(:disabled) {
  background: #5a6fd6;
  transform: translateY(-2px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: #fff3f3;
  color: #d32f2f;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state code {
  display: block;
  margin-top: 12px;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 8px;
  font-family: monospace;
}

/* Cells Grid */
.cells-grid {
  display: grid;
  gap: 16px;
}

.cell-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.cell-card:hover {
  background: #fff;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.cell-card.expanded {
  background: #fff;
  border-color: #667eea;
}

.cell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.cell-term {
  font-size: 18px;
  font-weight: 600;
  color: #1a1a2e;
}

.cell-score {
  padding: 4px 12px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
}

.cell-score.high { background: #e8f5e9; color: #2e7d32; }
.cell-score.medium { background: #fff3e0; color: #ef6c00; }
.cell-score.low { background: #ffebee; color: #c62828; }

.cell-stats {
  display: flex;
  gap: 8px;
}

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.badge.lang { background: #e3f2fd; color: #1565c0; }
.badge.policy { background: #fff3e0; color: #ef6c00; }
.badge.sentiment { background: #f3e5f5; color: #7b1fa2; }

/* Expanded Details */
.cell-details {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
}

.definition-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.lang-code {
  font-weight: 700;
  color: #667eea;
  margin-right: 8px;
}

.def-term {
  font-weight: 600;
}

.def-summary {
  margin-top: 8px;
  font-size: 13px;
  color: #555;
  line-height: 1.5;
}

.evidence-item {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 8px;
}

.evidence-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.source-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.source-badge.pboc { background: #ffcdd2; color: #c62828; }
.source-badge.fed { background: #bbdefb; color: #1565c0; }

.sentiment-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.sentiment-badge.bullish { background: #c8e6c9; color: #2e7d32; }
.sentiment-badge.bearish { background: #ffcdd2; color: #c62828; }
.sentiment-badge.neutral { background: #e0e0e0; color: #616161; }

.evidence-text, .evidence-title {
  font-size: 13px;
  color: #555;
  line-height: 1.5;
  margin: 0;
}

.score {
  font-size: 12px;
  color: #888;
}

.source {
  font-size: 12px;
  color: #666;
}

/* Per-Cell Export Section */
.cell-export-section {
  margin-top: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-radius: 12px;
  border: 1px solid #f59e0b;
}

.cell-export-section h4 {
  margin: 0 0 12px 0;
  color: #92400e;
  font-size: 14px;
}

.export-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.format-select, .lang-select {
  padding: 8px 12px;
  border: 2px solid #f59e0b;
  border-radius: 8px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  outline: none;
}

.format-select:focus, .lang-select:focus {
  border-color: #d97706;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}

.cell-export-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.3s;
}

.cell-export-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

/* Report Section */
.report-section {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.report-section h3 {
  margin-bottom: 16px;
}

@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
