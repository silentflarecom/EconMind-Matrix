<template>
  <div class="space-y-6">
    <!-- Statistics Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div class="text-3xl font-bold text-amber-600">{{ stats.total_articles || 0 }}</div>
        <div class="text-gray-500 text-sm">Articles</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div class="text-3xl font-bold text-green-600">{{ stats.annotations_by_sentiment?.bullish || 0 }}</div>
        <div class="text-gray-500 text-sm">Bullish</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div class="text-3xl font-bold text-red-600">{{ stats.annotations_by_sentiment?.bearish || 0 }}</div>
        <div class="text-gray-500 text-sm">Bearish</div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
        <div class="text-3xl font-bold text-gray-600">{{ stats.annotations_by_sentiment?.neutral || 0 }}</div>
        <div class="text-gray-500 text-sm">Neutral</div>
      </div>
    </div>

    <!-- Sentiment Distribution Chart -->
    <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h3 class="text-lg font-semibold mb-4">Sentiment Distribution</h3>
      <div class="h-8 flex rounded-full overflow-hidden bg-gray-200">
        <div 
          class="bg-green-500 flex items-center justify-center text-white text-sm font-medium"
          :style="{width: sentimentPercentages.bullish + '%'}"
        >
          {{ sentimentPercentages.bullish > 10 ? sentimentPercentages.bullish.toFixed(0) + '%' : '' }}
        </div>
        <div 
          class="bg-gray-500 flex items-center justify-center text-white text-sm font-medium"
          :style="{width: sentimentPercentages.neutral + '%'}"
        >
          {{ sentimentPercentages.neutral > 10 ? sentimentPercentages.neutral.toFixed(0) + '%' : '' }}
        </div>
        <div 
          class="bg-red-500 flex items-center justify-center text-white text-sm font-medium"
          :style="{width: sentimentPercentages.bearish + '%'}"
        >
          {{ sentimentPercentages.bearish > 10 ? sentimentPercentages.bearish.toFixed(0) + '%' : '' }}
        </div>
      </div>
      <div class="flex justify-center gap-6 mt-4 text-sm">
        <span class="flex items-center gap-2"><span class="w-3 h-3 bg-green-500 rounded-full"></span> Bullish</span>
        <span class="flex items-center gap-2"><span class="w-3 h-3 bg-gray-500 rounded-full"></span> Neutral</span>
        <span class="flex items-center gap-2"><span class="w-3 h-3 bg-red-500 rounded-full"></span> Bearish</span>
      </div>
    </div>

    <!-- Recent Articles -->
    <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h3 class="text-lg font-semibold mb-4">Recent Articles</h3>
      <div v-if="recentArticles.length === 0" class="text-gray-500 text-center py-4">
        No articles yet. Start crawling to populate the corpus.
      </div>
      <div v-else class="space-y-3">
        <div v-for="article in recentArticles.slice(0, 5)" :key="article.id" class="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
          <span class="text-lg">{{ getSentimentEmoji(article.annotation?.sentiment?.label) }}</span>
          <div class="flex-1 min-w-0">
            <h4 class="font-medium text-gray-900 line-clamp-1">{{ article.title }}</h4>
            <p class="text-xs text-gray-500">
              {{ article.source }} • {{ formatDate(article.published_date) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: { type: Object, default: () => ({}) },
  recentArticles: { type: Array, default: () => [] }
})

const sentimentPercentages = computed(() => {
  const total = (props.stats.annotations_by_sentiment?.bullish || 0) +
                (props.stats.annotations_by_sentiment?.bearish || 0) +
                (props.stats.annotations_by_sentiment?.neutral || 0)
  if (total === 0) return { bullish: 33.33, neutral: 33.33, bearish: 33.34 }
  return {
    bullish: ((props.stats.annotations_by_sentiment?.bullish || 0) / total) * 100,
    neutral: ((props.stats.annotations_by_sentiment?.neutral || 0) / total) * 100,
    bearish: ((props.stats.annotations_by_sentiment?.bearish || 0) / total) * 100
  }
})

const getSentimentEmoji = (label) => {
  if (label === 'bullish') return '🟢'
  if (label === 'bearish') return '🔴'
  return '⚪'
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}
</script>
