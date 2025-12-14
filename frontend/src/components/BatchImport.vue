<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const emit = defineEmits(['task-created'])

const activeTab = ref('text')
const textInput = ref('')
const uploadedFile = ref(null)
const terms = ref([])
const crawlInterval = ref(3)
const maxDepth = ref(1)
const loading = ref(false)
const error = ref(null)

// Language selection
const availableLanguages = ref([])
const selectedLanguages = ref(['en', 'zh'])
const loadingLanguages = ref(false)

// Duplicate detection state
const checkingDuplicates = ref(false)
const duplicateResult = ref(null)
const showDuplicateWarning = ref(false)
const skipDuplicates = ref(true)

// Load available languages on mount
const loadLanguages = async () => {
  loadingLanguages.value = true
  try {
    const response = await axios.get('http://localhost:8000/api/languages')
    availableLanguages.value = response.data.languages
  } catch (err) {
    console.error('Failed to load languages:', err)
    // Use fallback
    availableLanguages.value = [
      { code: 'en', name: 'English' },
      { code: 'zh', name: '中文 (Chinese)' }
    ]
  } finally {
    loadingLanguages.value = false
  }
}

const toggleLanguage = (langCode) => {
  const index = selectedLanguages.value.indexOf(langCode)
  if (index === -1) {
    selectedLanguages.value.push(langCode)
  } else if (selectedLanguages.value.length > 1) {
    // Always keep at least one language
    selectedLanguages.value.splice(index, 1)
  }
}

onMounted(() => {
  loadLanguages()
})

const parsedTerms = computed(() => {
  if (!textInput.value.trim()) return []
  return textInput.value
    .split('\n')
    .map(t => t.trim())
    .filter(t => t.length > 0)
})

const updateTermsFromText = () => {
  terms.value = [...new Set(parsedTerms.value)]
  // Reset duplicate check when terms change
  duplicateResult.value = null
  showDuplicateWarning.value = false
}

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  uploadedFile.value = file
  const reader = new FileReader()
  
  reader.onload = (e) => {
    const content = e.target.result
    const fileTerms = content
      .split('\n')
      .map(line => {
        // Handle CSV format (take first column)
        if (file.name.endsWith('.csv')) {
          return line.split(',')[0].trim()
        }
        return line.trim()
      })
      .filter(t => t.length > 0 && !t.toLowerCase().startsWith('term')) // Remove header
    
    terms.value = [...new Set(fileTerms)]
    // Reset duplicate check
    duplicateResult.value = null
    showDuplicateWarning.value = false
  }
  
  reader.readAsText(file)
}

const removeTerm = (index) => {
  terms.value.splice(index, 1)
  duplicateResult.value = null
  showDuplicateWarning.value = false
}

const clearAll = () => {
  terms.value = []
  textInput.value = ''
  uploadedFile.value = null
  error.value = null
  duplicateResult.value = null
  showDuplicateWarning.value = false
}

// Check for duplicates before creating task
const checkDuplicates = async () => {
  if (terms.value.length === 0) {
    error.value = "Please add at least one term"
    return
  }
  
  checkingDuplicates.value = true
  error.value = null
  
  try {
    const response = await axios.post('http://localhost:8000/api/corpus/check-duplicates', {
      terms: terms.value
    })
    
    duplicateResult.value = response.data
    
    if (response.data.existing_count > 0) {
      showDuplicateWarning.value = true
    } else {
      // No duplicates, proceed directly
      await createBatchTask(terms.value)
    }
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to check duplicates"
  } finally {
    checkingDuplicates.value = false
  }
}

// Proceed with task creation (after duplicate check)
const proceedWithTask = async () => {
  const termsToUse = skipDuplicates.value 
    ? duplicateResult.value.new 
    : terms.value
  
  if (termsToUse.length === 0) {
    error.value = "No new terms to crawl after skipping duplicates"
    showDuplicateWarning.value = false
    return
  }
  
  await createBatchTask(termsToUse)
  showDuplicateWarning.value = false
}

const createBatchTask = async (termsToSubmit) => {
  loading.value = true
  error.value = null
  
  try {
    const response = await axios.post('http://localhost:8000/api/batch/create', {
      terms: termsToSubmit,
      crawl_interval: crawlInterval.value,
      max_depth: maxDepth.value,
      target_languages: selectedLanguages.value
    })
    
    emit('task-created', response.data)
    clearAll()
  } catch (err) {
    error.value = err.response?.data?.detail || "Failed to create batch task"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
    <!-- Header -->
    <div class="bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4">
      <h2 class="text-xl font-bold text-white">📝 Batch Import</h2>
      <p class="text-blue-100 text-sm mt-1">Import multiple terms at once</p>
    </div>
    
    <!-- Tab Navigation -->
    <div class="border-b border-gray-200 bg-gray-50">
      <div class="flex">
        <button
          @click="activeTab = 'text'"
          :class="[
            'flex-1 px-6 py-3 text-sm font-medium transition-colors',
            activeTab === 'text' 
              ? 'text-blue-600 border-b-2 border-blue-600 bg-white' 
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          ]"
        >
          Text Input
        </button>
        <button
          @click="activeTab = 'file'"
          :class="[
            'flex-1 px-6 py-3 text-sm font-medium transition-colors',
            activeTab === 'file' 
              ? 'text-blue-600 border-b-2 border-blue-600 bg-white' 
              : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
          ]"
        >
          Upload File
        </button>
      </div>
    </div>
    
    <!-- Content Area -->
    <div class="p-6">
      <!-- Text Input Tab -->
      <div v-if="activeTab === 'text'" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Enter terms (one per line)
          </label>
          <textarea
            v-model="textInput"
            @input="updateTermsFromText"
            rows="8"
            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition font-mono text-sm"
            placeholder="Inflation&#10;Gross Domestic Product&#10;Recession&#10;..."
          ></textarea>
        </div>
      </div>
      
      <!-- File Upload Tab -->
      <div v-if="activeTab === 'file'" class="space-y-4">
        <div class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition">
          <input
            type="file"
            @change="handleFileUpload"
            accept=".txt,.csv"
            class="hidden"
            id="file-upload"
          />
          <label for="file-upload" class="cursor-pointer">
            <div class="text-gray-400 mb-2">
              <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <p class="text-sm text-gray-600">
              <span class="text-blue-600 font-medium">Click to upload</span> or drag and drop
            </p>
            <p class="text-xs text-gray-500 mt-1">TXT or CSV files only</p>
            <p v-if="uploadedFile" class="text-sm text-green-600 mt-2">
              ✓ {{ uploadedFile.name }}
            </p>
          </label>
        </div>
      </div>
      
      <!-- Error Message -->
      <div v-if="error" class="mt-4 rounded-md bg-red-50 p-4 border border-red-200">
        <p class="text-sm text-red-800">{{ error }}</p>
      </div>
      
      <!-- Terms Preview -->
      <div v-if="terms.length > 0" class="mt-6">
        <div class="flex justify-between items-center mb-3">
          <h3 class="text-sm font-medium text-gray-700">
            Terms Preview ({{ terms.length }})
          </h3>
          <button
            @click="clearAll"
            class="text-xs text-red-600 hover:text-red-700 font-medium"
          >
            Clear All
          </button>
        </div>
        
        <div class="max-h-60 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-gray-50 custom-scrollbar">
          <div
            v-for="(term, index) in terms"
            :key="index"
            class="flex items-center justify-between py-2 px-3 mb-1 bg-white rounded border border-gray-100 hover:border-blue-200 transition group"
          >
            <div class="flex items-center gap-2">
              <span class="text-xs font-mono text-gray-400 w-8">{{ index + 1 }}.</span>
              <span class="text-sm text-gray-800">{{ term }}</span>
            </div>
            <button
              @click="removeTerm(index)"
              class="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition"
            >
              ×
            </button>
          </div>
        </div>
      </div>
      
      <!-- Settings -->
      <div v-if="terms.length > 0" class="mt-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Crawl Interval (seconds)
        </label>
        <input
          v-model.number="crawlInterval"
          type="number"
          min="1"
          max="10"
          class="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        />
        <p class="text-xs text-gray-500 mt-1">
          Wait time between each Wikipedia request (prevents blocking)
        </p>
      </div>
      
      <div v-if="terms.length > 0" class="mt-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Max Crawl Depth
        </label>
        <div class="flex items-center gap-4">
          <input
            v-model.number="maxDepth"
            type="range"
            min="1"
            max="3"
            step="1"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <span class="text-sm font-medium text-gray-700 w-8">{{ maxDepth }}</span>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          1 = Only input terms. 2 = Also crawl "See Also" links of input terms. 3 = Two layers deep.
        </p>
      </div>
      
      <!-- Target Languages -->
      <div v-if="terms.length > 0" class="mt-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
          🌐 Target Languages
        </label>
        <div v-if="loadingLanguages" class="text-sm text-gray-500">
          Loading languages...
        </div>
        <div v-else class="flex flex-wrap gap-2">
          <button
            v-for="lang in availableLanguages"
            :key="lang.code"
            @click="toggleLanguage(lang.code)"
            :class="[
              'px-3 py-1.5 rounded-lg text-sm font-medium transition border',
              selectedLanguages.includes(lang.code)
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
            ]"
          >
            {{ lang.code.toUpperCase() }} - {{ lang.name.split(' ')[0] }}
          </button>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          Selected: {{ selectedLanguages.join(', ') }} ({{ selectedLanguages.length }} languages)
        </p>
      </div>
      
      <!-- Action Button -->
      <div v-if="terms.length > 0" class="mt-6">
        <button
          @click="checkDuplicates"
          :disabled="loading || checkingDuplicates"
          class="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition shadow-md hover:shadow-lg"
        >
          <span v-if="checkingDuplicates">Checking for duplicates...</span>
          <span v-else-if="loading">Creating Task...</span>
          <span v-else>Start Batch Crawl ({{ terms.length }} terms)</span>
        </button>
      </div>
      
      <!-- Duplicate Warning Modal -->
      <div v-if="showDuplicateWarning" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white rounded-xl shadow-2xl p-6 max-w-lg mx-4 max-h-[80vh] overflow-y-auto">
          <h3 class="text-xl font-bold text-amber-600 mb-2 flex items-center gap-2">
            ⚠️ Duplicate Terms Detected
          </h3>
          <p class="text-gray-600 mb-4">
            {{ duplicateResult.existing_count }} of {{ duplicateResult.total_input }} terms already exist in your corpus:
          </p>
          
          <!-- Existing Terms List -->
          <div class="max-h-40 overflow-y-auto bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
            <div 
              v-for="(term, index) in duplicateResult.existing" 
              :key="index"
              class="text-sm text-amber-800 py-1 px-2 bg-amber-100 rounded mb-1"
            >
              {{ term }}
            </div>
          </div>
          
          <!-- Options -->
          <div class="space-y-3 mb-4">
            <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition"
                   :class="skipDuplicates ? 'border-blue-500 bg-blue-50' : 'border-gray-200'">
              <input type="radio" v-model="skipDuplicates" :value="true" class="text-blue-600" />
              <div>
                <p class="font-medium text-gray-800">Skip duplicates (Recommended)</p>
                <p class="text-sm text-gray-500">Only crawl {{ duplicateResult.new_count }} new terms</p>
              </div>
            </label>
            
            <label class="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 transition"
                   :class="!skipDuplicates ? 'border-blue-500 bg-blue-50' : 'border-gray-200'">
              <input type="radio" v-model="skipDuplicates" :value="false" class="text-blue-600" />
              <div>
                <p class="font-medium text-gray-800">Force re-crawl all</p>
                <p class="text-sm text-gray-500">Crawl all {{ duplicateResult.total_input }} terms (may create duplicates)</p>
              </div>
            </label>
          </div>
          
          <div class="flex gap-3">
            <button
              @click="proceedWithTask"
              :disabled="loading"
              class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {{ loading ? 'Creating...' : 'Proceed' }}
            </button>
            <button
              @click="showDuplicateWarning = false"
              :disabled="loading"
              class="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
