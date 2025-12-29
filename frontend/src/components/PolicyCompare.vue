<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { API_BASE as API_ROOT } from '@/services/api'

const API_BASE = `${API_ROOT}/api/policy`

// State
const loading = ref(false)
const error = ref(null)
const activeTab = ref('upload')

// Reports
const reports = ref([])
const selectedSourceId = ref(null)
const selectedTargetId = ref(null)

// Upload state
const uploadSource = ref('pboc')
const uploadTitle = ref('')
const uploadText = ref('')
const uploadFile = ref(null)
const uploadLoading = ref(false)

// Alignment state
const alignments = ref([])
const alignmentLoading = ref(false)
const alignmentMethod = ref('auto')
const alignmentThreshold = ref(0.5)

// Statistics
const stats = ref(null)
const topics = ref([])

// History state
const alignmentHistory = ref([])
const historyLoading = ref(false)
const historyPage = ref(1)
const historyLimit = ref(20)

// Load data on mount
onMounted(async () => {
  await loadReports()
  await loadStats()
  await loadTopics()
})

// API calls
const loadReports = async () => {
  try {
    const res = await axios.get(`${API_BASE}/reports`)
    reports.value = res.data.reports || []
  } catch (err) {
    console.error('Failed to load reports:', err)
  }
}

const loadStats = async () => {
  try {
    const res = await axios.get(`${API_BASE}/stats`)
    stats.value = res.data.statistics
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

const loadTopics = async () => {
  try {
    const res = await axios.get(`${API_BASE}/topics`)
    topics.value = res.data.topics || []
  } catch (err) {
    console.error('Failed to load topics:', err)
  }
}

// User custom topics (stored locally + can be used for alignment filtering)
const customTopics = ref([])
const newSingleTerm = ref('')
const newBatchTerms = ref('')
const importFile = ref(null)

// Add single term to topic pool
const addSingleTerm = () => {
  const term = newSingleTerm.value.trim()
  if (!term) return
  if (customTopics.value.some(t => t.term.toLowerCase() === term.toLowerCase())) {
    error.value = 'Term already exists in pool'
    return
  }
  customTopics.value.push({
    term: term,
    addedAt: new Date().toISOString(),
    source: 'manual'
  })
  newSingleTerm.value = ''
  saveCustomTopicsToStorage()
}

// Add batch terms
const addBatchTerms = () => {
  const terms = newBatchTerms.value
    .split('\n')
    .map(t => t.trim())
    .filter(t => t.length > 0)
  
  if (terms.length === 0) return
  
  let added = 0
  for (const term of terms) {
    if (!customTopics.value.some(t => t.term.toLowerCase() === term.toLowerCase())) {
      customTopics.value.push({
        term: term,
        addedAt: new Date().toISOString(),
        source: 'batch'
      })
      added++
    }
  }
  newBatchTerms.value = ''
  saveCustomTopicsToStorage()
  if (added > 0) {
    alert(`Added ${added} new terms to topic pool`)
  }
}

// Import from Layer 1 JSON file
const handleImportFile = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  try {
    const text = await file.text()
    let terms = []
    
    // Try JSONL format first
    if (file.name.endsWith('.jsonl')) {
      const lines = text.split('\n').filter(l => l.trim())
      for (const line of lines) {
        try {
          const obj = JSON.parse(line)
          if (obj.term) terms.push(obj.term)
          else if (obj.en_term) terms.push(obj.en_term)
        } catch (e) { /* skip invalid lines */ }
      }
    } else {
      // Try JSON array or object
      const data = JSON.parse(text)
      if (Array.isArray(data)) {
        terms = data.map(item => item.term || item.en_term || item).filter(t => typeof t === 'string')
      } else if (data.terms) {
        terms = data.terms
      }
    }
    
    let added = 0
    for (const term of terms) {
      if (term && !customTopics.value.some(t => t.term.toLowerCase() === term.toLowerCase())) {
        customTopics.value.push({
          term: term,
          addedAt: new Date().toISOString(),
          source: 'layer1-import'
        })
        added++
      }
    }
    saveCustomTopicsToStorage()
    alert(`Imported ${added} terms from ${file.name}`)
    event.target.value = '' // Reset file input
  } catch (err) {
    error.value = 'Failed to parse import file. Ensure it is valid JSON or JSONL.'
  }
}

// Remove term from pool
const removeCustomTopic = (index) => {
  customTopics.value.splice(index, 1)
  saveCustomTopicsToStorage()
}

// Clear all custom topics
const clearAllCustomTopics = () => {
  if (!confirm('Remove all custom terms from pool?')) return
  customTopics.value = []
  saveCustomTopicsToStorage()
}

// Save to localStorage
const saveCustomTopicsToStorage = () => {
  localStorage.setItem('layer2_custom_topics', JSON.stringify(customTopics.value))
}

// Load from localStorage
const loadCustomTopicsFromStorage = () => {
  try {
    const saved = localStorage.getItem('layer2_custom_topics')
    if (saved) {
      customTopics.value = JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load custom topics:', e)
  }
}

// Load saved topics on mount
loadCustomTopicsFromStorage()

// Upload text report
const uploadTextReport = async () => {
  if (!uploadText.value.trim() || !uploadTitle.value.trim()) {
    error.value = 'Please enter title and text content'
    return
  }
  
  uploadLoading.value = true
  error.value = null
  
  try {
    const res = await axios.post(`${API_BASE}/upload-text`, {
      text: uploadText.value,
      source: uploadSource.value,
      title: uploadTitle.value
    })
    
    // Refresh reports
    await loadReports()
    await loadStats()
    
    // Clear form
    uploadTitle.value = ''
    uploadText.value = ''
    
    alert(`Report uploaded successfully! ID: ${res.data.report.id}, ${res.data.paragraphs_count} paragraphs detected.`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Upload failed'
  } finally {
    uploadLoading.value = false
  }
}

// Upload PDF file
const handleFileSelect = (event) => {
  uploadFile.value = event.target.files[0]
}

const uploadPdfReport = async () => {
  if (!uploadFile.value) {
    error.value = 'Please select a PDF file'
    return
  }
  
  uploadLoading.value = true
  error.value = null
  
  const formData = new FormData()
  formData.append('file', uploadFile.value)
  formData.append('source', uploadSource.value)
  if (uploadTitle.value) formData.append('title', uploadTitle.value)
  
  try {
    const res = await axios.post(`${API_BASE}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    await loadReports()
    await loadStats()
    
    uploadFile.value = null
    uploadTitle.value = ''
    
    alert(`PDF uploaded successfully! ID: ${res.data.report.id}, ${res.data.paragraphs_count} paragraphs detected.`)
  } catch (err) {
    error.value = err.response?.data?.detail || 'PDF upload failed'
  } finally {
    uploadLoading.value = false
  }
}

// Run alignment
const runAlignment = async () => {
  if (!selectedSourceId.value || !selectedTargetId.value) {
    error.value = 'Please select source and target reports'
    return
  }
  
  alignmentLoading.value = true
  error.value = null
  
  try {
    const res = await axios.post(`${API_BASE}/align`, {
      source_report_id: selectedSourceId.value,
      target_report_id: selectedTargetId.value,
      threshold: alignmentThreshold.value,
      method: alignmentMethod.value
    })
    
    alignments.value = res.data.alignments || []
    await loadStats()
    
    if (alignments.value.length === 0) {
      error.value = 'No alignments found. Try lowering the threshold.'
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Alignment failed'
  } finally {
    alignmentLoading.value = false
  }
}

// Delete report
const deleteReport = async (reportId) => {
  if (!confirm('Are you sure you want to delete this report?')) return
  
  try {
    await axios.delete(`${API_BASE}/reports/${reportId}`)
    await loadReports()
    await loadStats()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Delete failed'
  }
}

// Export data
const exportData = (type, format) => {
  const url = `${API_BASE}/export/${type}?format=${format}`
  window.open(url, '_blank')
}

// Load alignment history
const loadAlignmentHistory = async () => {
  historyLoading.value = true
  try {
    const res = await axios.get(`${API_BASE}/alignments`, {
      params: {
        limit: 100
      }
    })
    alignmentHistory.value = res.data.alignments || []
  } catch (err) {
    console.error('Failed to load alignment history:', err)
    error.value = 'Failed to load history'
  } finally {
    historyLoading.value = false
  }
}

// Computed
const pbocReports = computed(() => reports.value.filter(r => r.source === 'pboc'))
const fedReports = computed(() => reports.value.filter(r => r.source === 'fed'))

const getTopicColor = (topic) => {
  const colors = {
    'inflation': 'bg-red-100 text-red-800',
    'interest_rate': 'bg-blue-100 text-blue-800',
    'employment': 'bg-green-100 text-green-800',
    'gdp_growth': 'bg-yellow-100 text-yellow-800',
    'trade_balance': 'bg-purple-100 text-purple-800',
    'exchange_rate': 'bg-pink-100 text-pink-800',
    'financial_market': 'bg-indigo-100 text-indigo-800',
    'monetary_policy': 'bg-orange-100 text-orange-800'
  }
  return colors[topic] || 'bg-gray-100 text-gray-800'
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white shadow-lg">
      <h2 class="text-2xl font-bold">📊 Policy Parallel Corpus (Layer 2)</h2>
      <p class="text-emerald-100 mt-1">Compare PBOC vs Fed policy reports with AI-powered alignment</p>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-xl p-4">
      <p class="text-red-700">{{ error }}</p>
      <button @click="error = null" class="text-red-500 text-sm hover:underline mt-1">Dismiss</button>
    </div>

    <!-- Stats Cards -->
    <div v-if="stats" class="grid grid-cols-4 gap-4">
      <div class="bg-white rounded-xl p-4 shadow-md border border-gray-100">
        <p class="text-3xl font-bold text-blue-600">{{ Object.values(stats.reports_by_source || {}).reduce((a, b) => a + b, 0) }}</p>
        <p class="text-sm text-gray-500">Total Reports</p>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-md border border-gray-100">
        <p class="text-3xl font-bold text-green-600">{{ stats.total_paragraphs }}</p>
        <p class="text-sm text-gray-500">Total Paragraphs</p>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-md border border-gray-100">
        <p class="text-3xl font-bold text-purple-600">{{ stats.total_alignments }}</p>
        <p class="text-sm text-gray-500">Total Alignments</p>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-md border border-gray-100">
        <p class="text-3xl font-bold text-orange-600">{{ (stats.avg_similarity * 100).toFixed(1) }}%</p>
        <p class="text-sm text-gray-500">Avg Similarity</p>
      </div>
    </div>

    <!-- Export Section -->
    <div v-if="stats && stats.total_alignments > 0" class="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-200">
      <div class="flex items-center justify-between">
        <div>
          <h4 class="font-medium text-gray-800">📦 Export Layer 2 Data</h4>
          <p class="text-sm text-gray-500">Download reports, alignments, or parallel corpus</p>
        </div>
        <div class="flex gap-2">
          <button
            @click="exportData('alignments', 'jsonl')"
            class="px-3 py-1.5 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition"
            title="Export alignments as JSONL"
          >
            📥 Alignments
          </button>
          <button
            @click="exportData('reports', 'jsonl')"
            class="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
            title="Export reports with paragraphs"
          >
            📄 Reports
          </button>
          <button
            @click="exportData('parallel-corpus', 'tsv')"
            class="px-3 py-1.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition"
            title="Export as parallel corpus (TSV)"
          >
            🔗 Parallel TSV
          </button>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 border-b border-gray-200">
      <button
        @click="activeTab = 'upload'"
        :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', activeTab === 'upload' ? 'bg-white text-emerald-600 border-t-2 border-emerald-500' : 'text-gray-500 hover:text-gray-700']"
      >
        📤 Upload Report
      </button>
      <button
        @click="activeTab = 'reports'"
        :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', activeTab === 'reports' ? 'bg-white text-emerald-600 border-t-2 border-emerald-500' : 'text-gray-500 hover:text-gray-700']"
      >
        📋 Reports ({{ reports.length }})
      </button>
      <button
        @click="activeTab = 'align'"
        :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', activeTab === 'align' ? 'bg-white text-emerald-600 border-t-2 border-emerald-500' : 'text-gray-500 hover:text-gray-700']"
      >
        🔗 Align & Compare
      </button>
      <button
        @click="activeTab = 'topics'"
        :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', activeTab === 'topics' ? 'bg-white text-emerald-600 border-t-2 border-emerald-500' : 'text-gray-500 hover:text-gray-700']"
      >
        🏷️ Topics ({{ customTopics.length }})
      </button>
      <button
        @click="activeTab = 'history'; loadAlignmentHistory()"
        :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', activeTab === 'history' ? 'bg-white text-emerald-600 border-t-2 border-emerald-500' : 'text-gray-500 hover:text-gray-700']"
      >
        📊 History ({{ stats?.total_alignments || 0 }})
      </button>
    </div>

    <!-- Upload Tab -->
    <div v-if="activeTab === 'upload'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">Upload Policy Report</h3>
      
      <!-- Source Selection -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">Report Source</label>
        <div class="flex gap-4">
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" v-model="uploadSource" value="pboc" class="text-emerald-600" />
            <span class="text-sm">🇨🇳 PBOC (Chinese)</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer">
            <input type="radio" v-model="uploadSource" value="fed" class="text-emerald-600" />
            <span class="text-sm">🇺🇸 Fed (English)</span>
          </label>
        </div>
      </div>

      <!-- Title -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">Report Title</label>
        <input 
          v-model="uploadTitle" 
          type="text" 
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="e.g., 2024 Q3 Monetary Policy Report"
        />
      </div>

      <!-- PDF Upload -->
      <div class="mb-4 p-4 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <label class="block text-sm font-medium text-gray-700 mb-2">Upload PDF File</label>
        <input 
          type="file" 
          accept=".pdf"
          @change="handleFileSelect"
          class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
        />
        <button 
          @click="uploadPdfReport"
          :disabled="!uploadFile || uploadLoading"
          class="mt-3 px-6 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {{ uploadLoading ? 'Uploading...' : 'Upload PDF' }}
        </button>
      </div>

      <!-- Text Upload (for testing) -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">Or Paste Text (for testing)</label>
        <textarea 
          v-model="uploadText" 
          rows="6"
          class="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          placeholder="Paste policy report text here..."
        ></textarea>
        <button 
          @click="uploadTextReport"
          :disabled="!uploadText.trim() || uploadLoading"
          class="mt-3 px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
        >
          {{ uploadLoading ? 'Uploading...' : 'Upload Text' }}
        </button>
      </div>

      <!-- Sample Data -->
      <div class="mt-6 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
        <h4 class="font-medium text-emerald-800 mb-2">💡 Sample Data for Testing</h4>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p class="font-medium text-gray-700">PBOC Sample:</p>
            <button 
              @click="uploadSource = 'pboc'; uploadTitle = '2024Q3 PBOC Report'; uploadText = '当前通胀水平保持温和，CPI同比上涨0.4%，核心CPI同比上涨0.3%。物价水平总体稳定，为货币政策提供了较大的操作空间。\n\n9月份，人民银行下调存款准备金率0.5个百分点，释放长期流动性约1万亿元。同时，降低政策利率0.2个百分点，引导贷款市场报价利率（LPR）下行。\n\n就业形势总体稳定，新增就业持续增长。'"
              class="text-emerald-600 hover:underline"
            >
              Load PBOC Sample
            </button>
          </div>
          <div>
            <p class="font-medium text-gray-700">Fed Sample:</p>
            <button 
              @click="uploadSource = 'fed'; uploadTitle = 'December 2024 Beige Book'; uploadText = 'Economic activity expanded slightly in most Districts since the prior report. Consumer spending was mixed, with some Districts reporting modest gains while others noted flat or declining sales.\n\nPrices continued to rise modestly across most Districts, with inflation pressures easing somewhat from earlier in the year. Input costs remained elevated but increases have slowed.\n\nEmployment grew modestly overall, though labor market conditions remained tight.'"
              class="text-emerald-600 hover:underline"
            >
              Load Fed Sample
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reports Tab -->
    <div v-if="activeTab === 'reports'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-800">Policy Reports</h3>
        <button @click="loadReports" class="text-sm text-blue-600 hover:underline">Refresh</button>
      </div>
      
      <div v-if="reports.length === 0" class="text-center py-12 text-gray-500">
        <p class="text-5xl mb-4">📄</p>
        <p>No reports uploaded yet. Go to "Upload Report" to add one.</p>
      </div>

      <div v-else class="grid grid-cols-2 gap-6">
        <!-- PBOC Reports -->
        <div>
          <h4 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
            🇨🇳 PBOC Reports ({{ pbocReports.length }})
          </h4>
          <div class="space-y-2">
            <div v-for="report in pbocReports" :key="report.id" class="p-3 bg-red-50 rounded-lg border border-red-100">
              <div class="flex justify-between">
                <div>
                  <p class="font-medium text-gray-800">{{ report.title }}</p>
                  <p class="text-xs text-gray-500">ID: {{ report.id }} | {{ report.paragraph_count }} paragraphs</p>
                </div>
                <button @click="deleteReport(report.id)" class="text-red-500 hover:text-red-700 text-sm">Delete</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Fed Reports -->
        <div>
          <h4 class="font-medium text-gray-700 mb-3 flex items-center gap-2">
            🇺🇸 Fed Reports ({{ fedReports.length }})
          </h4>
          <div class="space-y-2">
            <div v-for="report in fedReports" :key="report.id" class="p-3 bg-blue-50 rounded-lg border border-blue-100">
              <div class="flex justify-between">
                <div>
                  <p class="font-medium text-gray-800">{{ report.title }}</p>
                  <p class="text-xs text-gray-500">ID: {{ report.id }} | {{ report.paragraph_count }} paragraphs</p>
                </div>
                <button @click="deleteReport(report.id)" class="text-red-500 hover:text-red-700 text-sm">Delete</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Align Tab -->
    <div v-if="activeTab === 'align'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">Align Reports</h3>
      
      <!-- Example/Instructions Box -->
      <div class="mb-6 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
        <p class="text-sm font-medium text-emerald-800 mb-2">💡 How to use:</p>
        <ol class="text-sm text-gray-700 list-decimal list-inside space-y-1">
          <li><strong>Upload at least one PBOC report and one Fed report</strong> from the Upload tab</li>
          <li><strong>Select Source (PBOC)</strong> - e.g., "2024Q3 PBOC Report"</li>
          <li><strong>Select Target (Fed)</strong> - e.g., "December 2024 Beige Book"</li>
          <li><strong>Adjust Threshold</strong> - Lower = more matches, Higher = stricter matching (0.3-0.5 recommended)</li>
          <li><strong>Run Alignment</strong> to find matching paragraphs on similar topics</li>
        </ol>
        <p class="text-xs text-emerald-600 mt-2">
          Example: Compare how PBOC and Fed discuss "inflation" - the system will find paragraphs about price stability from both reports.
        </p>
      </div>
      
      <div class="grid grid-cols-3 gap-4 mb-6">
        <!-- Source Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Source Report (PBOC)</label>
          <select v-model="selectedSourceId" class="w-full border border-gray-300 rounded-lg px-3 py-2">
            <option :value="null">Select PBOC report...</option>
            <option v-for="r in pbocReports" :key="r.id" :value="r.id">{{ r.title }}</option>
          </select>
        </div>

        <!-- Target Selection -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Target Report (Fed)</label>
          <select v-model="selectedTargetId" class="w-full border border-gray-300 rounded-lg px-3 py-2">
            <option :value="null">Select Fed report...</option>
            <option v-for="r in fedReports" :key="r.id" :value="r.id">{{ r.title }}</option>
          </select>
        </div>

        <!-- Threshold -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Threshold: {{ alignmentThreshold }}</label>
          <input type="range" v-model.number="alignmentThreshold" min="0.1" max="0.9" step="0.1" class="w-full" />
        </div>
      </div>

      <button 
        @click="runAlignment"
        :disabled="!selectedSourceId || !selectedTargetId || alignmentLoading"
        class="px-6 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
      >
        {{ alignmentLoading ? 'Running Alignment...' : '🔗 Run Alignment' }}
      </button>

      <!-- Alignment Results -->
      <div v-if="alignments.length > 0" class="mt-6">
        <h4 class="font-medium text-gray-700 mb-3">Alignment Results ({{ alignments.length }})</h4>
        <div class="space-y-4 max-h-96 overflow-y-auto">
          <div v-for="(a, idx) in alignments" :key="idx" class="border border-gray-200 rounded-lg p-4">
            <div class="flex justify-between items-center mb-2">
              <span :class="['px-2 py-1 rounded text-xs font-medium', getTopicColor(a.topic)]">
                {{ a.topic || 'unknown' }}
              </span>
              <span class="text-sm font-bold text-emerald-600">{{ (a.similarity_score * 100).toFixed(1) }}% match</span>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-red-50 p-3 rounded text-sm text-gray-700">
                <p class="font-medium text-red-800 mb-1">🇨🇳 PBOC</p>
                {{ a.source_text?.substring(0, 200) }}...
              </div>
              <div class="bg-blue-50 p-3 rounded text-sm text-gray-700">
                <p class="font-medium text-blue-800 mb-1">🇺🇸 Fed</p>
                {{ a.target_text?.substring(0, 200) }}...
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Topics Tab -->
    <div v-if="activeTab === 'topics'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">🏷️ Topic Pool</h3>
      
      <!-- Info Box -->
      <div class="mb-6 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
        <p class="text-sm font-medium text-emerald-800 mb-2">💡 How topics work:</p>
        <ul class="text-xs text-emerald-700 list-disc list-inside space-y-1">
          <li>Add terms to the pool to improve paragraph matching during alignment</li>
          <li>Import terms directly from Layer 1 exports (JSON/JSONL)</li>
          <li>Topics are saved locally in your browser</li>
        </ul>
      </div>

      <!-- Add Custom Term Section -->
      <div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h4 class="font-medium text-gray-800 mb-3">➕ Add Terms to Pool</h4>
        
        <div class="grid grid-cols-2 gap-4 mb-4">
          <!-- Single Term -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Single Term</label>
            <div class="flex gap-2">
              <input
                v-model="newSingleTerm"
                @keyup.enter="addSingleTerm"
                type="text"
                placeholder="e.g., Quantitative easing"
                class="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
              />
              <button 
                @click="addSingleTerm"
                class="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 transition"
              >
                Add
              </button>
            </div>
          </div>
          
          <!-- Import from Layer 1 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Import from Layer 1</label>
            <div class="flex gap-2">
              <input
                type="file"
                @change="handleImportFile"
                accept=".json,.jsonl"
                class="flex-1 text-sm text-gray-500 file:mr-2 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-sm file:bg-blue-50 file:text-blue-700 file:cursor-pointer"
              />
            </div>
            <p class="text-xs text-gray-500 mt-1">Accepts JSON or JSONL format</p>
          </div>
        </div>

        <!-- Batch Add -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Batch Add (one per line)</label>
          <div class="flex gap-2">
            <textarea
              v-model="newBatchTerms"
              rows="3"
              placeholder="Inflation&#10;GDP growth&#10;Interest rate&#10;Money supply"
              class="flex-1 px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
            ></textarea>
            <button 
              @click="addBatchTerms"
              class="px-4 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700 transition h-fit"
            >
              Batch Add
            </button>
          </div>
        </div>
      </div>

      <!-- Topic Pool Display -->
      <div class="mb-4 flex justify-between items-center">
        <h4 class="font-medium text-gray-800">� Your Topic Pool ({{ customTopics.length }})</h4>
        <button 
          v-if="customTopics.length > 0"
          @click="clearAllCustomTopics"
          class="text-xs text-red-600 hover:text-red-700"
        >
          Clear All
        </button>
      </div>

      <!-- Empty State -->
      <div v-if="customTopics.length === 0" class="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p class="text-3xl mb-2">📭</p>
        <p class="text-gray-500 text-sm">No topics in pool yet</p>
        <p class="text-gray-400 text-xs mt-1">Add terms above or import from Layer 1</p>
      </div>

      <!-- Topic Pool Grid -->
      <div v-else class="flex flex-wrap gap-2 max-h-64 overflow-y-auto p-2 bg-gray-50 rounded-lg border border-gray-200">
        <div 
          v-for="(topic, index) in customTopics" 
          :key="index"
          class="group flex items-center gap-1 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm hover:border-emerald-400 transition"
        >
          <span class="text-gray-700">{{ topic.term }}</span>
          <span 
            v-if="topic.source === 'layer1-import'" 
            class="text-xs text-blue-500"
            title="Imported from Layer 1"
          >
            📁
          </span>
          <button 
            @click="removeCustomTopic(index)"
            class="ml-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition"
          >
            ×
          </button>
        </div>
      </div>

      <!-- Quick Add Examples -->
      <div class="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 class="font-medium text-blue-800 mb-2">� Quick Add Examples</h4>
        <p class="text-xs text-blue-700 mb-2">Click to add common economic terms:</p>
        <div class="flex flex-wrap gap-2">
          <button 
            v-for="term in ['Inflation', 'GDP', 'Interest rate', 'Monetary policy', 'Exchange rate', 'Unemployment', 'Fiscal policy', 'Trade balance']"
            :key="term"
            @click="newSingleTerm = term; addSingleTerm()"
            class="px-2 py-1 bg-white text-xs text-blue-700 rounded border border-blue-200 hover:bg-blue-100 transition"
          >
            + {{ term }}
          </button>
        </div>
      </div>
    </div>

    <!-- History Tab -->
    <div v-if="activeTab === 'history'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-800">📊 Alignment History</h3>
        <button
          @click="loadAlignmentHistory"
          class="px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-700 transition"
        >
          🔄 Refresh
        </button>
      </div>

      <!-- Info Box -->
      <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <p class="text-sm text-blue-800">
          <strong>💡 Alignment History:</strong> All paragraph pairs that have been aligned across reports.
          Use this to review, verify, or export alignment results for further analysis.
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="historyLoading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto"></div>
        <p class="text-gray-500 mt-4">Loading alignment history...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="alignmentHistory.length === 0" class="text-center py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p class="text-3xl mb-2">📭</p>
        <p class="text-gray-500 text-sm">No alignments yet</p>
        <p class="text-gray-400 text-xs mt-1">Upload reports and run alignment to see results here</p>
      </div>

      <!-- History Table -->
      <div v-else class="overflow-x-auto">
        <table class="w-full border border-gray-200 rounded-lg">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Similarity</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Topic</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source (PBOC)</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target (Fed)</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="align in alignmentHistory" :key="align.id" class="hover:bg-gray-50 transition">
              <td class="px-4 py-3 text-sm text-gray-600">{{ align.id }}</td>
              <td class="px-4 py-3">
                <span 
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    align.similarity_score > 0.7 ? 'bg-green-100 text-green-800' :
                    align.similarity_score > 0.4 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  ]"
                >
                  {{ (align.similarity_score * 100).toFixed(1) }}%
                </span>
              </td>
              <td class="px-4 py-3">
                <span v-if="align.topic" class="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs">
                  {{ align.topic }}
                </span>
                <span v-else class="text-gray-400 text-xs">-</span>
              </td>
              <td class="px-4 py-3 text-xs text-gray-500">{{ align.alignment_method }}</td>
              <td class="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">
                {{ align.source_text?.substring(0, 100) }}...
              </td>
              <td class="px-4 py-3 text-sm text-gray-700 max-w-xs truncate">
                {{ align.target_text?.substring(0, 100) }}...
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Total Count -->
        <div class="mt-4 text-sm text-gray-500 text-center">
          Showing {{ alignmentHistory.length }} alignment{{ alignmentHistory.length !== 1 ? 's' : '' }}
        </div>
      </div>
    </div>
  </div>
</template>
