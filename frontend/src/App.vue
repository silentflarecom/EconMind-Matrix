<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE } from './services/api'
import BatchImport from './components/BatchImport.vue'
import ProgressMonitor from './components/ProgressMonitor.vue'
import ResultsTable from './components/ResultsTable.vue'
import PolicyCompare from './components/PolicyCompare.vue'
import SentimentAnalysis from './components/SentimentAnalysis.vue'

// Active view: 'layer1', 'layer2', or 'system'
const activeView = ref('layer1')

// Layer 1 sub-tabs: 'search', 'batch', 'results', 'tasks'
const layer1Tab = ref('search')

// Single search state
const term = ref('')
const loading = ref(false)
const error = ref(null)
const result = ref(null)

// Batch processing state
const currentTaskId = ref(null)
const showProgress = ref(false)
const showResults = ref(false)

// Single search functions
const search = async () => {
  if (!term.value.trim()) return
  
  loading.value = true
  error.value = null
  result.value = null
  
  try {
    const response = await axios.get(`${API_BASE}/search?term=${encodeURIComponent(term.value)}`)
    result.value = response.data
  } catch (err) {
    if (err.response && err.response.data && err.response.data.detail) {
      error.value = err.response.data.detail
    } else {
      error.value = "An error occurred while fetching data."
    }
  } finally {
    loading.value = false
  }
}

const downloadJson = () => {
  if (!result.value) return
  const dataStr = JSON.stringify(result.value, null, 2)
  const blob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${result.value.term}_data.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

const handleKeyup = (e) => {
  if (e.key === 'Enter') search()
}

// Batch processing functions
const handleTaskCreated = async (taskData) => {
  currentTaskId.value = taskData.task_id
  
  // Start the task
  try {
    await axios.post(`${API_BASE}/api/batch/${taskData.task_id}/start`)
    showProgress.value = true
    layer1Tab.value = 'progress'
  } catch (err) {
    console.error('Error starting task:', err)
  }
}

const handleTaskCompleted = (taskId) => {
  console.log('Task completed:', taskId)
}

const handleRetry = async (taskId) => {
  try {
    await axios.post(`${API_BASE}/api/batch/${taskId}/retry-failed`)
    showResults.value = false
    showProgress.value = true
  } catch (err) {
    console.error('Error retrying:', err)
  }
}

const viewResults = () => {
  showProgress.value = false
  showResults.value = true
  layer1Tab.value = 'results'
}

const closeProgress = () => {
  showProgress.value = false
  layer1Tab.value = 'batch'
}

const closeResults = () => {
  showResults.value = false
  layer1Tab.value = 'batch'
}

// Task Manager functions
const handleViewTask = (taskId) => {
  currentTaskId.value = taskId
  showResults.value = true
  layer1Tab.value = 'results'
}

// System state
const systemStats = ref(null)
const layer2Stats = ref(null)
const layer3Stats = ref(null)
const userAgent = ref('')
const loadingSettings = ref(false)
const savingSettings = ref(false)
const settingsSuccess = ref(false)
const tasks = ref([])
const deleteConfirm = ref(null)
const resetConfirm = ref(false)
const resetting = ref(false)

const loadSystemData = async () => {
  try {
    const [statsRes, tasksRes, layer2Res, layer3Res] = await Promise.all([
      axios.get(`${API_BASE}/api/corpus/statistics`),
      axios.get(`${API_BASE}/api/batch/tasks`),
      axios.get(`${API_BASE}/api/policy/stats`).catch(() => ({ data: { statistics: null } })),
      axios.get(`${API_BASE}/api/sentiment/stats`).catch(() => ({ data: { statistics: null } }))
    ])
    systemStats.value = statsRes.data
    tasks.value = tasksRes.data
    layer2Stats.value = layer2Res.data?.statistics || null
    layer3Stats.value = layer3Res.data?.statistics || null
  } catch (err) {
    console.error('Failed to load system data:', err)
  }
  
  try {
    const settingsRes = await axios.get(`${API_BASE}/api/system/settings/user_agent`)
    userAgent.value = settingsRes.data.value
  } catch (err) {
    console.warn('Failed to load user agent:', err)
  }
}

const saveUserAgent = async () => {
  savingSettings.value = true
  settingsSuccess.value = false
  try {
    await axios.post(`${API_BASE}/api/system/settings`, {
      key: 'user_agent',
      value: userAgent.value
    })
    settingsSuccess.value = true
    setTimeout(() => { settingsSuccess.value = false }, 3000)
  } catch (err) {
    error.value = 'Failed to save settings'
  } finally {
    savingSettings.value = false
  }
}

const downloadBackup = () => {
  window.open(`${API_BASE}/api/system/backup`, '_blank')
}

const downloadLayer2Backup = () => {
  window.open(`${API_BASE}/api/policy/backup`, '_blank')
}

const downloadLayer3Backup = () => {
  window.open(`${API_BASE}/api/sentiment/backup`, '_blank')
}

const deleteTask = async (taskId) => {
  try {
    await axios.delete(`${API_BASE}/api/batch/${taskId}`)
    deleteConfirm.value = null
    await loadSystemData()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete task'
  }
}

const resetAllData = async () => {
  resetting.value = true
  try {
    await axios.post(`${API_BASE}/api/system/reset?confirm=true`)
    resetConfirm.value = false
    await loadSystemData()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to reset database'
  } finally {
    resetting.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getStatusColor = (status) => {
  const colors = {
    'pending': 'bg-yellow-100 text-yellow-800',
    'running': 'bg-blue-100 text-blue-800',
    'completed': 'bg-green-100 text-green-800',
    'failed': 'bg-red-100 text-red-800',
    'cancelled': 'bg-gray-100 text-gray-800'
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}
</script>

<template>
  <div class="min-h-screen flex flex-col items-center py-12 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-blue-50 via-white to-purple-50">
    <div class="w-full max-w-6xl space-y-8">
      
      <!-- Header -->
      <div class="text-center">
        <h1 class="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 tracking-tight">
          EconMind Matrix
        </h1>
        <p class="mt-3 text-lg text-gray-600">
          Multi-Granularity Bilingual Economic Corpus Platform
        </p>
      </div>

      <!-- Main Navigation -->
      <div class="flex justify-center gap-3 flex-wrap">
        <button
          @click="activeView = 'layer1'"
          :class="[
            'px-8 py-3 rounded-xl font-semibold text-lg transition-all shadow-md',
            activeView === 'layer1'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-blue-200'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          ]"
        >
          📚 Layer 1: Terminology
        </button>
        <button
          @click="activeView = 'layer2'"
          :class="[
            'px-8 py-3 rounded-xl font-semibold text-lg transition-all shadow-md',
            activeView === 'layer2'
              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-emerald-200'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          ]"
        >
          📊 Layer 2: Policy Corpus
        </button>
        <button
          @click="activeView = 'layer3'"
          :class="[
            'px-8 py-3 rounded-xl font-semibold text-lg transition-all shadow-md',
            activeView === 'layer3'
              ? 'bg-gradient-to-r from-amber-600 to-orange-600 text-white shadow-amber-200'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          ]"
        >
          📰 Layer 3: Sentiment
        </button>
        <button
          @click="activeView = 'system'; loadSystemData()"
          :class="[
            'px-8 py-3 rounded-xl font-semibold text-lg transition-all shadow-md',
            activeView === 'system'
              ? 'bg-gradient-to-r from-gray-700 to-gray-800 text-white shadow-gray-300'
              : 'bg-white text-gray-600 hover:bg-gray-50'
          ]"
        >
          ⚙️ System
        </button>
      </div>

      <!-- ==================== LAYER 1: TERMINOLOGY ==================== -->
      <div v-if="activeView === 'layer1'" class="space-y-6">
        
        <!-- Layer 1 Header -->
        <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
          <h2 class="text-2xl font-bold">📚 Layer 1: Terminology Knowledge Base</h2>
          <p class="text-blue-100 mt-1">Search and batch import economic terms from Wikipedia in 20+ languages</p>
        </div>

        <!-- Layer 1 Sub-tabs -->
        <div class="flex gap-2 border-b border-gray-200 flex-wrap">
          <button
            @click="layer1Tab = 'search'"
            :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', layer1Tab === 'search' ? 'bg-white text-blue-600 border-t-2 border-blue-500' : 'text-gray-500 hover:text-gray-700']"
          >
            🔍 Single Search
          </button>
          <button
            @click="layer1Tab = 'batch'"
            :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', layer1Tab === 'batch' ? 'bg-white text-purple-600 border-t-2 border-purple-500' : 'text-gray-500 hover:text-gray-700']"
          >
            📥 Batch Import
          </button>
          <button
            @click="layer1Tab = 'tasks'; loadSystemData()"
            :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', layer1Tab === 'tasks' ? 'bg-white text-gray-600 border-t-2 border-gray-500' : 'text-gray-500 hover:text-gray-700']"
          >
            📋 Task History
          </button>
          <button
            @click="layer1Tab = 'settings'; loadSystemData()"
            :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', layer1Tab === 'settings' ? 'bg-white text-yellow-600 border-t-2 border-yellow-500' : 'text-gray-500 hover:text-gray-700']"
          >
            🔧 Settings
          </button>
          <button
            v-if="showProgress && currentTaskId"
            @click="layer1Tab = 'progress'"
            :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', layer1Tab === 'progress' ? 'bg-white text-green-600 border-t-2 border-green-500' : 'text-gray-500 hover:text-gray-700']"
          >
            ⏳ Progress
          </button>
          <button
            v-if="showResults && currentTaskId"
            @click="layer1Tab = 'results'"
            :class="['px-6 py-3 font-medium text-sm rounded-t-lg transition', layer1Tab === 'results' ? 'bg-white text-orange-600 border-t-2 border-orange-500' : 'text-gray-500 hover:text-gray-700']"
          >
            📋 Results
          </button>
        </div>

        <!-- Single Search -->
        <div v-if="layer1Tab === 'search'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">Single Term Search</h3>
          
          <!-- Example Box -->
          <div class="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <p class="text-sm font-medium text-blue-800 mb-2">💡 Examples to try:</p>
            <div class="flex flex-wrap gap-2">
              <button @click="term = 'Inflation'" class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition">Inflation</button>
              <button @click="term = 'GDP'" class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition">GDP</button>
              <button @click="term = 'Monetary policy'" class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition">Monetary policy</button>
              <button @click="term = 'Interest rate'" class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition">Interest rate</button>
              <button @click="term = 'Exchange rate'" class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm hover:bg-blue-200 transition">Exchange rate</button>
            </div>
          </div>

          <!-- Search Box -->
          <div class="flex gap-2">
            <div class="relative flex-grow">
              <input 
                v-model="term" 
                @keyup="handleKeyup"
                type="text" 
                class="block w-full rounded-xl border-gray-300 shadow-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-lg pl-4 py-4 border outline-none transition-all duration-200" 
                placeholder="Enter a term (e.g., Inflation)" 
              />
            </div>
            <button 
              @click="search" 
              :disabled="loading"
              class="inline-flex items-center px-8 py-4 border border-transparent text-base font-medium rounded-xl shadow-md text-white bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              <span v-if="loading" class="animate-spin mr-2">⟳</span>
              Search
            </button>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="mt-4 rounded-xl bg-red-50 p-4 border border-red-200">
            <p class="text-red-700">{{ error }}</p>
          </div>

          <!-- Results Area -->
          <div v-if="result" class="mt-6 bg-gray-50 shadow-xl rounded-2xl overflow-hidden border border-gray-100">
            <div class="px-6 py-4 flex justify-between items-center bg-gradient-to-r from-gray-50 to-blue-50 border-b border-gray-100">
              <h3 class="text-lg leading-6 font-medium text-gray-900">
                Results for: <span class="font-bold text-blue-600">{{ result.term }}</span>
              </h3>
              <button 
                @click="downloadJson" 
                class="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition"
              >
                Export JSON
              </button>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-100">
              <!-- English Section -->
              <div class="p-6">
                <div class="flex items-center justify-between mb-4">
                  <h4 class="text-lg font-bold text-gray-800">🇺🇸 English</h4>
                  <a :href="result.en_url" target="_blank" class="text-sm text-blue-500 hover:text-blue-700 font-medium transition">Wikipedia →</a>
                </div>
                <p class="text-gray-600 leading-relaxed text-sm h-64 overflow-y-auto pr-2 custom-scrollbar">
                  {{ result.en_summary }}
                </p>
              </div>

              <!-- Chinese Section -->
              <div class="p-6 bg-slate-50/50">
                <div class="flex items-center justify-between mb-4">
                  <h4 class="text-lg font-bold text-gray-800">🇨🇳 Chinese</h4>
                  <a v-if="result.zh_url" :href="result.zh_url" target="_blank" class="text-sm text-blue-500 hover:text-blue-700 font-medium transition">Wikipedia →</a>
                </div>
                <div v-if="result.zh_url">
                  <p class="text-gray-600 leading-relaxed text-sm h-64 overflow-y-auto pr-2 custom-scrollbar">
                    {{ result.zh_summary }}
                  </p>
                </div>
                <div v-else class="flex flex-col items-center justify-center h-64 text-gray-400">
                  <span>No Chinese translation found.</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Batch Import -->
        <div v-if="layer1Tab === 'batch'" class="space-y-6">
          <!-- Example Box -->
          <div class="bg-purple-50 rounded-xl p-6 border border-purple-200">
            <p class="text-sm font-medium text-purple-800 mb-3">💡 Batch Import Examples:</p>
            <div class="grid grid-cols-2 gap-4 text-sm text-gray-700">
              <div>
                <p class="font-medium">Macroeconomics Terms:</p>
                <code class="text-xs bg-white px-2 py-1 rounded block mt-1">GDP, Inflation, Unemployment, Fiscal policy, Trade deficit</code>
              </div>
              <div>
                <p class="font-medium">Financial Markets:</p>
                <code class="text-xs bg-white px-2 py-1 rounded block mt-1">Stock market, Bond, Derivatives, Hedge fund, Securities</code>
              </div>
            </div>
          </div>
          
          <BatchImport @task-created="handleTaskCreated" />
          
          <!-- Quick Access to Current Task -->
          <div v-if="currentTaskId && !showProgress && !showResults" class="bg-blue-50 border border-blue-200 rounded-xl p-4">
            <div class="flex justify-between items-center">
              <div>
                <p class="text-sm font-medium text-blue-900">Recent Task #{{ currentTaskId }}</p>
                <p class="text-xs text-blue-600 mt-1">Click to view progress or results</p>
              </div>
              <div class="flex gap-2">
                <button
                  @click="showProgress = true; layer1Tab = 'progress'"
                  class="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
                >
                  View Progress
                </button>
                <button
                  @click="showResults = true; layer1Tab = 'results'"
                  class="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition"
                >
                  View Results
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Progress Monitor -->
        <div v-if="layer1Tab === 'progress' && showProgress && currentTaskId">
          <ProgressMonitor 
            :taskId="currentTaskId" 
            @task-completed="viewResults"
            @close="closeProgress"
          />
        </div>

        <!-- Results Table -->
        <div v-if="layer1Tab === 'results' && showResults && currentTaskId">
          <ResultsTable 
            :taskId="currentTaskId" 
            @close="closeResults"
            @retry="handleRetry"
          />
        </div>

        <!-- Task History -->
        <div v-if="layer1Tab === 'tasks'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold text-gray-800">Task History</h3>
            <button @click="loadSystemData" class="text-sm text-blue-600 hover:underline">Refresh</button>
          </div>
          
          <div v-if="tasks.length === 0" class="text-center py-12 text-gray-500">
            <p class="text-5xl mb-4">📭</p>
            <p>No tasks yet. Go to "Batch Import" to create one.</p>
          </div>
          
          <div v-else class="divide-y divide-gray-100">
            <div v-for="task in tasks" :key="task.id" class="py-4 flex justify-between items-center">
              <div class="flex items-center gap-3">
                <span class="font-bold text-gray-600">#{{ task.id }}</span>
                <span :class="['px-2 py-1 rounded-full text-xs font-medium', getStatusColor(task.status)]">{{ task.status }}</span>
                <span class="text-sm text-gray-500">{{ task.completed_terms }}/{{ task.total_terms }} terms</span>
              </div>
              <div class="flex gap-2">
                <button @click="handleViewTask(task.id)" class="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200">View Results</button>
                <button @click="deleteConfirm = task.id" class="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">Delete</button>
              </div>
            </div>
          </div>
          
          <!-- Delete Confirmation -->
          <div v-if="deleteConfirm" class="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <p class="text-sm text-red-700 mb-2">Are you sure you want to delete Task #{{ deleteConfirm }}?</p>
            <div class="flex gap-2">
              <button @click="deleteTask(deleteConfirm)" class="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700">Yes, Delete</button>
              <button @click="deleteConfirm = null" class="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300">Cancel</button>
            </div>
          </div>
        </div>

        <!-- Settings -->
        <div v-if="layer1Tab === 'settings'" class="bg-white rounded-xl shadow-md p-6 border border-gray-100">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">🔧 Layer 1 Settings</h3>
          
          <!-- User Agent Configuration -->
          <div class="mb-6">
            <h4 class="font-medium text-gray-700 mb-2">Wikipedia User Agent</h4>
            <p class="text-sm text-gray-500 mb-3">Required for Wikipedia API crawling. Must include project name and contact info.</p>
            
            <!-- Example Box -->
            <div class="mb-4 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <p class="text-sm font-medium text-yellow-800 mb-2">⚠️ Required format: ProjectName/Version (Contact)</p>
              <div class="space-y-1 text-xs text-yellow-700">
                <p>Example: <code class="bg-white px-2 py-0.5 rounded">MyResearchBot/1.0 (mailto:me@university.edu)</code></p>
                <p>Example: <code class="bg-white px-2 py-0.5 rounded">EconCorpus/2.0 (https://github.com/user/project)</code></p>
              </div>
            </div>

            <div class="flex gap-4">
              <input
                v-model="userAgent"
                type="text"
                placeholder="e.g. MyBot/1.0 (mailto:me@example.com)"
                class="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                :disabled="savingSettings"
              />
              <button
                @click="saveUserAgent"
                :disabled="savingSettings"
                class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {{ savingSettings ? 'Saving...' : '💾 Save' }}
              </button>
            </div>
            <p v-if="settingsSuccess" class="mt-2 text-green-600 text-sm font-medium">✓ Settings saved!</p>
          </div>

          <!-- Statistics -->
          <div v-if="systemStats" class="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
            <h4 class="font-medium text-gray-700 mb-3">📊 Layer 1 Statistics</h4>
            <div class="grid grid-cols-4 gap-4 text-center">
              <div>
                <p class="text-2xl font-bold text-blue-600">{{ systemStats.total_tasks }}</p>
                <p class="text-xs text-gray-500">Tasks</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-green-600">{{ systemStats.completed_terms }}</p>
                <p class="text-xs text-gray-500">Terms</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-purple-600">{{ systemStats.bilingual_pairs }}</p>
                <p class="text-xs text-gray-500">Bilingual</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-gray-600">{{ formatBytes(systemStats.db_size_bytes) }}</p>
                <p class="text-xs text-gray-500">DB Size</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ==================== LAYER 2: POLICY CORPUS ==================== -->
      <div v-if="activeView === 'layer2'" class="space-y-6">
        <PolicyCompare />
      </div>

      <!-- ==================== LAYER 3: SENTIMENT ==================== -->
      <div v-if="activeView === 'layer3'" class="space-y-6">
        <SentimentAnalysis />
      </div>

      <!-- ==================== SYSTEM ==================== -->
      <div v-if="activeView === 'system'" class="space-y-6">
        
        <!-- System Header -->
        <div class="bg-gradient-to-r from-gray-700 to-gray-800 rounded-2xl p-6 text-white shadow-lg">
          <h2 class="text-2xl font-bold">⚙️ Global Settings</h2>
          <p class="text-gray-300 mt-1">Database backup, restore, and global configuration</p>
        </div>

        <!-- Statistics -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Layer 1 Stats -->
          <div class="bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg p-6 text-white">
            <h3 class="text-lg font-bold mb-3">📚 Layer 1: Terminology</h3>
            <div v-if="systemStats" class="space-y-2">
              <div class="flex justify-between">
                <span class="text-white/80">Tasks</span>
                <span class="font-bold">{{ systemStats.total_tasks || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">Terms</span>
                <span class="font-bold">{{ systemStats.completed_terms || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">Bilingual Pairs</span>
                <span class="font-bold">{{ systemStats.bilingual_pairs || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">DB Size</span>
                <span class="font-bold">{{ formatBytes(systemStats.db_size_bytes) }}</span>
              </div>
            </div>
            <div v-else class="text-white/60 text-sm">Loading...</div>
          </div>
          
          <!-- Layer 2 Stats -->
          <div class="bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl shadow-lg p-6 text-white">
            <h3 class="text-lg font-bold mb-3">📊 Layer 2: Policy Corpus</h3>
            <div v-if="layer2Stats" class="space-y-2">
              <div class="flex justify-between">
                <span class="text-white/80">Reports</span>
                <span class="font-bold">{{ Object.values(layer2Stats.reports_by_source || {}).reduce((a, b) => a + b, 0) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">Paragraphs</span>
                <span class="font-bold">{{ layer2Stats.total_paragraphs || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">Alignments</span>
                <span class="font-bold">{{ layer2Stats.total_alignments || 0 }}</span>
              </div>
            </div>
            <div v-else class="text-white/60 text-sm">No data</div>
          </div>
          
          <!-- Layer 3 Stats -->
          <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl shadow-lg p-6 text-white">
            <h3 class="text-lg font-bold mb-3">📰 Layer 3: Sentiment</h3>
            <div v-if="layer3Stats" class="space-y-2">
              <div class="flex justify-between">
                <span class="text-white/80">Articles</span>
                <span class="font-bold">{{ layer3Stats.total_articles || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">Annotations</span>
                <span class="font-bold">{{ layer3Stats.total_annotations || 0 }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-white/80">Sources</span>
                <span class="font-bold">{{ Object.keys(layer3Stats.sources_breakdown || {}).length }}</span>
              </div>
            </div>
            <div v-else class="text-white/60 text-sm">No data</div>
          </div>
        </div>


        <!-- Danger Zone -->
        <div class="bg-white rounded-xl shadow-lg border border-red-200 overflow-hidden">
          <div class="bg-red-600 px-6 py-4">
            <h3 class="text-lg font-bold text-white">⚠️ Danger Zone</h3>
          </div>
          <div class="p-6 space-y-4">
            <!-- Backup Layer 1 -->
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-800">📚 Backup Layer 1 (Terminology)</p>
                <p class="text-sm text-gray-500">Download corpus.db - Terms & definitions</p>
              </div>
              <button @click="downloadBackup" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                📥 Download
              </button>
            </div>
            <hr class="border-gray-200" />
            <!-- Backup Layer 2 -->
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-800">📊 Backup Layer 2 (Policy Corpus)</p>
                <p class="text-sm text-gray-500">Download policy_corpus.db - Reports & alignments</p>
              </div>
              <button @click="downloadLayer2Backup" class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition">
                📥 Download
              </button>
            </div>
            <hr class="border-gray-200" />
            <!-- Backup Layer 3 -->
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-gray-800">📰 Backup Layer 3 (Sentiment Corpus)</p>
                <p class="text-sm text-gray-500">Download sentiment.db - Articles & annotations</p>
              </div>
              <button @click="downloadLayer3Backup" class="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition">
                📥 Download
              </button>
            </div>
            <hr class="border-gray-200" />
            <!-- Reset All -->
            <div class="flex items-center justify-between bg-red-50 -mx-6 px-6 py-4">
              <div>
                <p class="font-medium text-red-700">Reset All Data</p>
                <p class="text-sm text-gray-500">Delete ALL data from Layer 1, 2, and 3. Cannot be undone!</p>
              </div>
              <button @click="resetConfirm = true" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
                🗑️ Reset All
              </button>
            </div>
          </div>
        </div>

        <!-- Reset Confirmation Modal -->
        <div v-if="resetConfirm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div class="bg-white rounded-xl shadow-2xl p-6 max-w-md mx-4">
            <h3 class="text-xl font-bold text-red-700 mb-4">⚠️ Confirm Reset All Data</h3>
            <p class="text-gray-600 mb-3">This will permanently delete ALL data from:</p>
            <ul class="text-sm text-gray-700 mb-4 space-y-1">
              <li>📚 <strong>Layer 1:</strong> Terms & bilingual definitions</li>
              <li>📊 <strong>Layer 2:</strong> Policy reports & alignments</li>
              <li>📰 <strong>Layer 3:</strong> News articles & sentiment annotations</li>
            </ul>
            <p class="text-red-600 text-sm font-medium mb-4">This action cannot be undone!</p>
            <div class="flex gap-3">
              <button @click="resetAllData" :disabled="resetting" class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50">
                {{ resetting ? 'Resetting...' : 'Delete Everything' }}
              </button>
              <button @click="resetConfirm = false" :disabled="resetting" class="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1; 
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1; 
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8; 
}
</style>
