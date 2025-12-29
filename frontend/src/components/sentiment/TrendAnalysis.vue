<template>
  <div class="space-y-6">
    <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h3 class="text-lg font-semibold mb-4">📈 Term Trend Analysis</h3>
      
      <!-- Term Search -->
      <div class="flex gap-4 mb-6">
        <input 
          type="text" 
          v-model="term"
          placeholder="Enter economic term (e.g., inflation, interest rate)"
          class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
          @keyup.enter="loadTrend"
        />
        <select 
          v-model="days"
          class="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option :value="7">7 Days</option>
          <option :value="14">14 Days</option>
          <option :value="30">30 Days</option>
          <option :value="60">60 Days</option>
        </select>
        <button
          @click="loadTrend"
          :disabled="!term || loading"
          class="px-6 py-2 bg-amber-500 text-white font-semibold rounded-lg hover:bg-amber-600 disabled:opacity-50"
        >
          Analyze
        </button>
      </div>

      <!-- Trend Results -->
      <div v-if="loading" class="text-center py-8">
        <div class="animate-spin w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full mx-auto"></div>
      </div>
      <div v-else-if="trendData">
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-amber-50 rounded-lg p-4">
            <div class="text-2xl font-bold text-amber-600">{{ trendData.summary?.mentions?.total || 0 }}</div>
            <div class="text-sm text-gray-600">Total Mentions</div>
          </div>
          <div class="bg-green-50 rounded-lg p-4">
            <div class="text-2xl font-bold text-green-600">{{ trendData.summary?.sentiment?.distribution?.bullish || 0 }}</div>
            <div class="text-sm text-gray-600">Bullish</div>
          </div>
          <div class="bg-red-50 rounded-lg p-4">
            <div class="text-2xl font-bold text-red-600">{{ trendData.summary?.sentiment?.distribution?.bearish || 0 }}</div>
            <div class="text-sm text-gray-600">Bearish</div>
          </div>
          <div class="bg-blue-50 rounded-lg p-4">
            <div class="text-2xl font-bold" :class="getTrendDirectionClass(trendData.summary?.trend?.direction)">
              {{ getTrendDirectionEmoji(trendData.summary?.trend?.direction) }}
            </div>
            <div class="text-sm text-gray-600">Trend: {{ trendData.summary?.trend?.direction || 'stable' }}</div>
          </div>
        </div>

        <!-- Trend Chart -->
        <div class="border border-gray-200 rounded-lg p-6 bg-gray-50">
          <h4 class="font-medium text-gray-700 mb-4">📊 Mention Trend (Last {{ days }} days)</h4>
          <div class="h-48 flex items-end justify-center gap-1">
            <div 
              v-for="(point, idx) in trendData.daily_data?.slice(-30)" 
              :key="idx"
              class="bg-amber-400 hover:bg-amber-500 transition-colors rounded-t"
              :style="{
                width: '20px',
                height: Math.max(4, point.mention_count * 10) + 'px'
              }"
              :title="`${point.date}: ${point.mention_count} mentions`"
            ></div>
          </div>
          <div class="text-center text-xs text-gray-500 mt-2">
            Daily mention count over time
          </div>
        </div>
      </div>
      <div v-else class="text-gray-500 text-center py-8">
        Enter a term and click "Analyze" to view trend data.
      </div>
    </div>

    <!-- Hot Terms -->
    <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h3 class="text-lg font-semibold mb-4">🔥 Hot Economic Terms</h3>
      <div v-if="hotTerms.length === 0" class="text-gray-500 text-center py-4">
        No trend data available yet.
      </div>
      <div v-else class="space-y-3">
        <div 
          v-for="(hotTerm, idx) in hotTerms" 
          :key="hotTerm.term"
          class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg hover:bg-amber-50 transition-colors cursor-pointer"
          @click="term = hotTerm.term; loadTrend()"
        >
          <span class="text-2xl font-bold text-gray-400 w-8">{{ idx + 1 }}</span>
          <div class="flex-1">
            <p class="font-medium text-gray-900 capitalize">{{ hotTerm.term.replace('_', ' ') }}</p>
            <p class="text-sm text-gray-500">{{ hotTerm.mentions }} mentions</p>
          </div>
          <span :class="hotTerm.avg_sentiment > 0.1 ? 'text-green-500' : hotTerm.avg_sentiment < -0.1 ? 'text-red-500' : 'text-gray-500'">
            {{ hotTerm.avg_sentiment > 0.1 ? '📈' : hotTerm.avg_sentiment < -0.1 ? '📉' : '➡️' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const props = defineProps({
  apiBase: { type: String, required: true },
  hotTerms: { type: Array, default: () => [] }
})

const term = ref('')
const days = ref(30)
const trendData = ref(null)
const loading = ref(false)

const loadTrend = async () => {
  if (!term.value) return
  
  loading.value = true
  try {
    const response = await axios.get(
      `${props.apiBase}/trend/${encodeURIComponent(term.value)}?days_back=${days.value}`
    )
    trendData.value = response.data
  } catch (error) {
    console.error('Failed to load trend:', error)
    trendData.value = null
  } finally {
    loading.value = false
  }
}

const getTrendDirectionClass = (direction) => {
  if (direction === 'rising') return 'text-green-600'
  if (direction === 'falling') return 'text-red-600'
  return 'text-gray-600'
}

const getTrendDirectionEmoji = (direction) => {
  if (direction === 'rising') return '📈'
  if (direction === 'falling') return '📉'
  return '➡️'
}
</script>
