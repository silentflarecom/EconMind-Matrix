<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'
import VisualGraph from './VisualGraph.vue'

const props = defineProps({
  taskId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['task-completed', 'close'])

const activeTab = ref('status')
const status = ref(null)
const currentTerm = ref('')
const polling = ref(null)
const loading = ref(true)

const progressPercent = computed(() => {
  return status.value?.progress_percent || 0
})

const isRunning = computed(() => {
  return status.value?.status === 'running'
})

const isCompleted = computed(() => {
  return status.value?.status === 'completed'
})

const fetchStatus = async () => {
  try {
    const response = await axios.get(`http://localhost:8000/api/batch/${props.taskId}/status`)
    status.value = response.data
    loading.value = false
    
    // If completed or failed, stop polling
    if (status.value.status === 'completed' || status.value.status === 'failed' || status.value.status === 'cancelled') {
      stopPolling()
      if (status.value.status === 'completed') {
        emit('task-completed', props.taskId)
      }
    }
  } catch (error) {
    console.error('Error fetching status:', error)
    loading.value = false
  }
}

const startPolling = () => {
  fetchStatus()
  polling.value = setInterval(fetchStatus, 2000) // Poll every 2 seconds
}

const stopPolling = () => {
  if (polling.value) {
    clearInterval(polling.value)
    polling.value = null
  }
}

const cancelTask = async () => {
  try {
    await axios.post(`http://localhost:8000/api/batch/${props.taskId}/cancel`)
    await fetchStatus()
  } catch (error) {
    console.error('Error cancelling task:', error)
  }
}

onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
    <!-- Header -->
    <div class="bg-gradient-to-r from-green-500 to-green-600 px-6 py-4 flex justify-between items-center">
      <div>
        <h2 class="text-xl font-bold text-white">📊 Task #{{ taskId }} Progress</h2>
        <p class="text-green-100 text-sm mt-1">Real-time crawling status</p>
      </div>
      <button
        @click="emit('close')"
        class="text-white hover:text-gray-200 transition text-2xl"
      >
        ×
      </button>
    </div>
    
    <div class="p-6 pt-2">
      <!-- Tabs -->
      <div v-if="status" class="flex gap-6 border-b border-gray-200 mb-6">
        <button
          @click="activeTab = 'status'"
          class="py-3 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === 'status' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          Task Status
        </button>
        <button
          @click="activeTab = 'graph'"
          class="py-3 text-sm font-medium border-b-2 transition-colors"
          :class="activeTab === 'graph' ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
        >
          Knowledge Graph 🕸️
        </button>
      </div>

      <div v-if="loading">
        <div class="text-center py-8">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p class="text-gray-500 mt-4">Loading task status...</p>
        </div>
      </div>
      
      <div v-else-if="status">
        <!-- Status Tab -->
        <div v-if="activeTab === 'status'">
          <!-- Progress Bar -->
        <div class="mb-6">
          <div class="flex justify-between items-center mb-2">
            <span class="text-sm font-medium text-gray-700">Progress</span>
            <span class="text-sm font-bold text-blue-600">{{ progressPercent }}%</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              class="h-3 rounded-full transition-all duration-500 bg-gradient-to-r from-blue-500 to-blue-600"
              :style="{ width: `${progressPercent}%` }"
            ></div>
          </div>
        </div>
        
        <!-- Statistics Cards -->
        <div class="grid grid-cols-3 gap-4 mb-6">
          <div class="bg-green-50 rounded-lg p-4 border border-green-200">
            <div class="flex items-center gap-2">
              <span class="text-2xl">✅</span>
              <div>
                <p class="text-xs text-green-600 font-medium">Completed</p>
                <p class="text-2xl font-bold text-green-700">{{ status.completed_terms }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-red-50 rounded-lg p-4 border border-red-200">
            <div class="flex items-center gap-2">
              <span class="text-2xl">❌</span>
              <div>
                <p class="text-xs text-red-600 font-medium">Failed</p>
                <p class="text-2xl font-bold text-red-700">{{ status.failed_terms }}</p>
              </div>
            </div>
          </div>
          
          <div class="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div class="flex items-center gap-2">
              <span class="text-2xl">⏳</span>
              <div>
                <p class="text-xs text-blue-600 font-medium">Pending</p>
                <p class="text-2xl font-bold text-blue-700">
                  {{ status.total_terms - status.completed_terms - status.failed_terms }}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Status Badge -->
        <div class="mb-6">
          <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium"
               :class="{
                 'bg-green-100 text-green-700': status.status === 'completed',
                 'bg-blue-100 text-blue-700': status.status === 'running',
                 'bg-yellow-100 text-yellow-700': status.status === 'pending',
                 'bg-red-100 text-red-700': status.status === 'failed',
                 'bg-gray-100 text-gray-700': status.status === 'cancelled'
               }">
            <span v-if="status.status === 'running'" class="animate-pulse">●</span>
            <span v-else>●</span>
            <span class="capitalize">{{ status.status }}</span>
          </div>
        </div>
        
        <!-- Current Activity -->
        <div v-if="isRunning" class="mb-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
          <p class="text-sm text-blue-700 font-medium mb-2">Currently crawling...</p>
          <div class="flex items-center gap-2">
            <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <p class="text-blue-900 font-mono text-sm">Processing terms</p>
          </div>
        </div>
        
        <!-- Completion Message -->
        <div v-if="isCompleted" class="mb-6 bg-green-50 rounded-lg p-4 border border-green-200">
          <div class="flex items-center gap-2">
            <span class="text-2xl">🎉</span>
            <div>
              <p class="text-green-800 font-medium">Task completed successfully!</p>
              <p class="text-sm text-green-600 mt-1">
                All {{ status.completed_terms }} terms have been crawled and saved.
              </p>
            </div>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="flex gap-3">
          <button
            v-if="isRunning"
            @click="cancelTask"
            class="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 transition"
          >
            Cancel Task
          </button>
          
          <button
            @click="emit('close')"
            class="flex-1 bg-gray-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-700 transition"
          >
            Close Monitor
          </button>
        </div>
        
        <!-- Timestamps -->
        <div class="mt-6 pt-4 border-t border-gray-200">
          <div class="grid grid-cols-2 gap-4 text-xs text-gray-500">
            <div>
              <p class="font-medium">Created:</p>
              <p>{{ new Date(status.created_at).toLocaleString() }}</p>
            </div>
            <div>
              <p class="font-medium">Last Updated:</p>
              <p>{{ new Date(status.updated_at).toLocaleString() }}</p>
            </div>
          </div>
        </div>
        </div>
        
        <!-- Graph Tab -->
        <div v-if="activeTab === 'graph'">
          <VisualGraph :task-id="taskId" />
        </div>
      </div>
    </div>
  </div>
</template>
