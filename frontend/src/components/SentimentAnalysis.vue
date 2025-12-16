<template>
  <div class="space-y-6">
    <!-- Layer 3 Header -->
    <div class="bg-gradient-to-r from-amber-600 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
      <h2 class="text-2xl font-bold">📰 Layer 3: Sentiment & Trend Corpus</h2>
      <p class="text-amber-100 mt-1">Financial news sentiment analysis and economic term trends</p>
    </div>

    <!-- Sub-tabs -->
    <div class="flex gap-2 border-b border-gray-200 flex-wrap">
      <button
        @click="activeTab = 'dashboard'"
        :class="[
          'px-4 py-2 font-medium transition-colors rounded-t-lg',
          activeTab === 'dashboard' ? 'bg-amber-100 text-amber-700 border-b-2 border-amber-600' : 'text-gray-600 hover:text-amber-600'
        ]"
      >
        📊 Dashboard
      </button>
      <button
        @click="activeTab = 'crawl'"
        :class="[
          'px-4 py-2 font-medium transition-colors rounded-t-lg',
          activeTab === 'crawl' ? 'bg-amber-100 text-amber-700 border-b-2 border-amber-600' : 'text-gray-600 hover:text-amber-600'
        ]"
      >
        🌐 Crawl News
      </button>
      <button
        @click="activeTab = 'articles'"
        :class="[
          'px-4 py-2 font-medium transition-colors rounded-t-lg',
          activeTab === 'articles' ? 'bg-amber-100 text-amber-700 border-b-2 border-amber-600' : 'text-gray-600 hover:text-amber-600'
        ]"
      >
        📰 Articles
      </button>
      <button
        @click="activeTab = 'trends'"
        :class="[
          'px-4 py-2 font-medium transition-colors rounded-t-lg',
          activeTab === 'trends' ? 'bg-amber-100 text-amber-700 border-b-2 border-amber-600' : 'text-gray-600 hover:text-amber-600'
        ]"
      >
        📈 Trends
      </button>
      <button
        @click="activeTab = 'export'"
        :class="[
          'px-4 py-2 font-medium transition-colors rounded-t-lg',
          activeTab === 'export' ? 'bg-amber-100 text-amber-700 border-b-2 border-amber-600' : 'text-gray-600 hover:text-amber-600'
        ]"
      >
        📥 Export
      </button>
    </div>

    <!-- Dashboard Tab -->
    <div v-if="activeTab === 'dashboard'" class="space-y-6">
      <!-- Statistics Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl shadow-sm p-4 border border-gray-100">
          <div class="text-3xl font-bold text-amber-600">{{ stats.total_articles || 0 }}</div>
          <div class="text-gray-500 text-sm">Total Articles</div>
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
            :style="{width: sentimentPercentages.bullish + '%'}"
            class="bg-green-500 flex items-center justify-center text-white text-sm font-medium"
          >
            {{ sentimentPercentages.bullish > 10 ? sentimentPercentages.bullish.toFixed(0) + '%' : '' }}
          </div>
          <div 
            :style="{width: sentimentPercentages.neutral + '%'}"
            class="bg-gray-500 flex items-center justify-center text-white text-sm font-medium"
          >
            {{ sentimentPercentages.neutral > 10 ? sentimentPercentages.neutral.toFixed(0) + '%' : '' }}
          </div>
          <div 
            :style="{width: sentimentPercentages.bearish + '%'}"
            class="bg-red-500 flex items-center justify-center text-white text-sm font-medium"
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
        <div v-if="recentArticles.length === 0" class="text-gray-500 text-center py-8">
          No articles yet. Start by crawling news sources.
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="article in recentArticles.slice(0, 5)" 
            :key="article.id"
            class="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors"
          >
            <span :class="getSentimentBadgeClass(article.annotation?.sentiment?.label)">
              {{ getSentimentEmoji(article.annotation?.sentiment?.label) }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-gray-900 truncate">{{ article.title }}</p>
              <p class="text-xs text-gray-500">
                {{ article.source }} • {{ formatDate(article.published_date) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Crawl News Tab -->
    <div v-if="activeTab === 'crawl'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">📡 Crawl International News Sources</h3>
        
        <!-- Crawling Progress Animation -->
        <div v-if="crawling" class="mb-6 bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-xl p-6">
          <div class="flex items-center gap-4 mb-4">
            <div class="relative">
              <div class="w-16 h-16 border-4 border-amber-200 border-t-amber-600 rounded-full animate-spin"></div>
              <div class="absolute inset-0 flex items-center justify-center text-2xl">📰</div>
            </div>
            <div class="flex-1">
              <h4 class="text-lg font-bold text-amber-900">Crawling in Progress...</h4>
              <p class="text-amber-700 text-sm">Fetching news from {{ selectedSources.length }} sources</p>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex justify-between text-sm text-amber-800">
              <span>Progress</span>
              <span>{{ crawlProgress }}%</span>
            </div>
            <div class="h-3 bg-amber-200 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-500 rounded-full"
                :style="{width: crawlProgress + '%'}"
              ></div>
            </div>
            <p class="text-xs text-amber-700 italic">{{ crawlStatusMessage }}</p>
          </div>
        </div>
        
        <!-- Source Selection by Region -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-3">
            <label class="block text-sm font-medium text-gray-700">Select News Sources ({{ selectedSources.length }} selected)</label>
            <div class="flex gap-2">
              <button @click="selectAllSources" class="text-xs px-3 py-1 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200">
                Select All
              </button>
              <button @click="clearSources" class="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200">
                Clear All
              </button>
            </div>
          </div>
          
          <!-- Group sources by region -->
          <div class="space-y-4">
            <div v-for="(sourcesInRegion, region) in sourcesByRegion" :key="region">
              <div class="flex items-center gap-2 mb-2">
                <span class="text-xs font-semibold text-gray-500 uppercase tracking-wide">{{ region }}</span>
                <div class="flex-1 h-px bg-gray-200"></div>
              </div>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="source in sourcesInRegion"
                  :key="source.key"
                  @click="toggleSource(source.key)"
                  :class="[
                    'px-3 py-2 rounded-lg font-medium text-sm transition-all',
                    selectedSources.includes(source.key)
                      ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-md transform scale-105'
                      : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
                  ]"
                  :disabled="!source.has_rss"
                  :title="`${source.name} (${source.language.toUpperCase()})`"
                >
                  <span class="flex items-center gap-1.5">
                    <span>{{ getRegionFlag(region) }}</span>
                    <span>{{ source.name }}</span>
                    <span v-if="!source.has_rss" class="text-xs">(No RSS)</span>
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Crawl Options -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Days Back</label>
            <input 
              type="number" 
              v-model="crawlDaysBack" 
              min="1" 
              max="30"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            <p class="text-xs text-gray-500 mt-1">Fetch news from the last N days (1-30)</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Keywords (optional)</label>
            <input 
              type="text" 
              v-model="crawlKeywords" 
              placeholder="inflation, fed, rate cut"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
            <p class="text-xs text-gray-500 mt-1">Filter articles by keywords (comma-separated)</p>
          </div>
        </div>

        <button
          @click="startCrawl"
          :disabled="crawling || selectedSources.length === 0"
          class="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-semibold rounded-lg hover:from-amber-600 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
        >
          <span v-if="crawling" class="flex items-center justify-center gap-2">
            <span class="animate-pulse">⏳</span>
            <span>Crawling in progress...</span>
          </span>
          <span v-else class="flex items-center justify-center gap-2">
            <span>🚀</span>
            <span>Start Crawl ({{ selectedSources.length }} sources)</span>
          </span>
        </button>

        <div v-if="crawlMessage" class="mt-4 p-4 rounded-lg" :class="crawlError ? 'bg-red-50 text-red-700 border border-red-200' : 'bg-green-50 text-green-700 border border-green-200'">
          <div class="flex items-start gap-2">
            <span class="text-lg">{{ crawlError ? '❌' : '✅' }}</span>
            <span>{{ crawlMessage }}</span>
          </div>
        </div>
      </div>

      <!-- Annotate Section -->
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">🤖 Auto-Annotate Articles</h3>
        
        <!-- Annotating Progress Animation -->
        <div v-if="annotating" class="mb-6 bg-gradient-to-r from-purple-50 to-pink-50 border-2 border-purple-300 rounded-xl p-6">
          <div class="flex items-center gap-4 mb-4">
            <div class="relative">
              <div class="w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
              <div class="absolute inset-0 flex items-center justify-center text-2xl">🤖</div>
            </div>
            <div class="flex-1">
              <h4 class="text-lg font-bold text-purple-900">Annotation in Progress...</h4>
              <p class="text-purple-700 text-sm">Analyzing article sentiments using {{ annotateMethod }}</p>
            </div>
          </div>
          <div class="space-y-2">
            <div class="flex items-center gap-2 text-sm text-purple-800">
              <div class="flex-1 flex gap-1">
                <div class="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
                <div class="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
                <div class="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
              </div>
              <span class="italic">Processing articles...</span>
            </div>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Annotation Method</label>
            <select 
              v-model="annotateMethod"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            >
              <option value="auto">Auto (LLM with fallback)</option>
              <option value="llm">LLM Only (Gemini API)</option>
              <option value="rule_based">Rule-based (No API)</option>
              <option value="hybrid">Hybrid (Optimized)</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Max Articles</label>
            <input 
              type="number" 
              v-model="annotateLimit" 
              min="1" 
              max="500"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>
        </div>

        <button
          @click="startAnnotate"
          :disabled="annotating"
          class="w-full py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 transition-all"
        >
          <span v-if="annotating">⏳ Annotating...</span>
          <span v-else>🏷️ Start Annotation</span>
        </button>

        <div v-if="annotateMessage" class="mt-4 p-4 rounded-lg" :class="annotateError ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
          {{ annotateMessage }}
        </div>
      </div>
    </div>

    <!-- Articles Tab -->
    <div v-if="activeTab === 'articles'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">📰 News Articles</h3>
          <div class="flex gap-2">
            <select 
              v-model="filterSentiment"
              @change="loadArticles"
              class="px-3 py-1 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Sentiments</option>
              <option value="bullish">🟢 Bullish</option>
              <option value="bearish">🔴 Bearish</option>
              <option value="neutral">⚪ Neutral</option>
            </select>
            <button @click="loadArticles" class="px-3 py-1 bg-gray-100 rounded-lg hover:bg-gray-200">
              🔄 Refresh
            </button>
          </div>
        </div>

        <!-- Articles List -->
        <div v-if="loadingArticles" class="text-center py-8">
          <div class="animate-spin w-8 h-8 border-4 border-amber-500 border-t-transparent rounded-full mx-auto"></div>
        </div>
        <div v-else-if="articles.length === 0" class="text-gray-500 text-center py-8">
          No articles found.
        </div>
        <div v-else class="space-y-4">
          <div 
            v-for="article in articles" 
            :key="article.id"
            class="border border-gray-200 rounded-lg p-4 hover:border-amber-300 transition-colors"
          >
            <div class="flex items-start gap-4">
              <span :class="getSentimentBadgeClass(article.annotation?.sentiment?.label)" class="mt-1">
                {{ getSentimentEmoji(article.annotation?.sentiment?.label) }}
              </span>
              <div class="flex-1">
                <h4 class="font-medium text-gray-900">{{ article.title }}</h4>
                <p class="text-sm text-gray-500 mt-1">{{ article.summary?.substring(0, 200) }}...</p>
                <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                  <span>{{ article.source }}</span>
                  <span>{{ formatDate(article.published_date) }}</span>
                  <span v-if="article.annotation">
                    Confidence: {{ (article.annotation.sentiment?.score * 100).toFixed(0) }}%
                  </span>
                  <a :href="article.url" target="_blank" class="text-amber-600 hover:underline">View Source ↗</a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Trends Tab -->
    <div v-if="activeTab === 'trends'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">📈 Term Trend Analysis</h3>
        
        <!-- Term Search -->
        <div class="flex gap-4 mb-6">
          <input 
            type="text" 
            v-model="trendTerm"
            placeholder="Enter economic term (e.g., inflation, interest rate)"
            class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            @keyup.enter="loadTrend"
          />
          <select 
            v-model="trendDays"
            class="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option :value="7">7 Days</option>
            <option :value="14">14 Days</option>
            <option :value="30">30 Days</option>
            <option :value="60">60 Days</option>
          </select>
          <button
            @click="loadTrend"
            :disabled="!trendTerm || loadingTrend"
            class="px-6 py-2 bg-amber-500 text-white font-semibold rounded-lg hover:bg-amber-600 disabled:opacity-50"
          >
            Analyze
          </button>
        </div>

        <!-- Trend Results -->
        <div v-if="loadingTrend" class="text-center py-8">
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

          <!-- Trend Chart Placeholder -->
          <div class="border border-gray-200 rounded-lg p-6 bg-gray-50">
            <h4 class="font-medium text-gray-700 mb-4">📊 Mention Trend (Last {{ trendDays }} days)</h4>
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
            v-for="(term, idx) in hotTerms" 
            :key="term.term"
            class="flex items-center gap-4 p-3 bg-gray-50 rounded-lg hover:bg-amber-50 transition-colors cursor-pointer"
            @click="trendTerm = term.term; loadTrend()"
          >
            <span class="text-2xl font-bold text-gray-400 w-8">{{ idx + 1 }}</span>
            <div class="flex-1">
              <p class="font-medium text-gray-900 capitalize">{{ term.term.replace('_', ' ') }}</p>
              <p class="text-sm text-gray-500">{{ term.mentions }} mentions</p>
            </div>
            <span :class="term.avg_sentiment > 0.1 ? 'text-green-500' : term.avg_sentiment < -0.1 ? 'text-red-500' : 'text-gray-500'">
              {{ term.avg_sentiment > 0.1 ? '📈' : term.avg_sentiment < -0.1 ? '📉' : '➡️' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Export Tab -->
    <div v-if="activeTab === 'export'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">📥 Export Data</h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Articles Export -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="font-medium mb-2">📰 Articles with Annotations</h4>
            <p class="text-sm text-gray-500 mb-4">Export all crawled articles with their sentiment annotations.</p>
            <div class="flex gap-2">
              <button 
                @click="exportData('articles', 'json')"
                class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                JSON
              </button>
              <button 
                @click="exportData('articles', 'jsonl')"
                class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                JSONL
              </button>
            </div>
          </div>

          <!-- Sentiment Export -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="font-medium mb-2">🏷️ Sentiment Labels</h4>
            <p class="text-sm text-gray-500 mb-4">Export sentiment annotations for ML training.</p>
            <div class="flex gap-2">
              <button 
                @click="exportData('sentiment', 'jsonl')"
                class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                JSONL
              </button>
              <button 
                @click="exportData('sentiment', 'csv')"
                class="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
              >
                CSV
              </button>
            </div>
          </div>

          <!-- Doccano Export -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="font-medium mb-2">🔖 Doccano Format</h4>
            <p class="text-sm text-gray-500 mb-4">Export for Doccano annotation platform.</p>
            <button 
              @click="exportData('doccano', 'jsonl')"
              class="px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600"
            >
              Export JSONL
            </button>
          </div>

          <!-- Layer 3 Stats -->
          <div class="border border-gray-200 rounded-lg p-4">
            <h4 class="font-medium mb-2">📊 Statistics</h4>
            <p class="text-sm text-gray-500 mb-4">Export Layer 3 corpus statistics.</p>
            <button 
              @click="downloadStats"
              class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Download JSON
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = 'http://localhost:8000/api/sentiment'

// State
const activeTab = ref('dashboard')
const stats = ref({})
const recentArticles = ref([])
const articles = ref([])
const loadingArticles = ref(false)
const filterSentiment = ref('')

// Crawl state
const availableSources = ref([])
const selectedSources = ref(['reuters', 'wsj', 'bbc', 'bloomberg'])
const crawlDaysBack = ref(7)
const crawlKeywords = ref('')
const crawling = ref(false)
const crawlMessage = ref('')
const crawlError = ref(false)
const crawlProgress = ref(0)
const crawlStatusMessage = ref('Initializing...')

// Annotate state
const annotateMethod = ref('auto')
const annotateLimit = ref(50)
const annotating = ref(false)
const annotateMessage = ref('')
const annotateError = ref(false)

// Trends state
const trendTerm = ref('')
const trendDays = ref(30)
const trendData = ref(null)
const loadingTrend = ref(false)
const hotTerms = ref([])

// Computed - Group sources by region
const sourcesByRegion = computed(() => {
  const regions = {
    'North America': [],
    'Europe': [],
    'Asia-Pacific': [],
    'Global': []
  }
  
  availableSources.value.forEach(source => {
    // Map source keys to regions based on country
    if (['bloomberg', 'reuters', 'wsj', 'cnbc', 'marketwatch', 'yahoo_finance'].includes(source.key)) {
      regions['North America'].push(source)
    } else if (['ft', 'bbc', 'guardian', 'dw', 'handelsblatt', 'lesechos'].includes(source.key)) {
      regions['Europe'].push(source)
    } else if (['xinhua', 'chinadaily', 'caixin', 'nikkei', 'japantimes', 'economictimes', 'koreaherald', 'afr', 'globeandmail'].includes(source.key)) {
      regions['Asia-Pacific'].push(source)
    } else {
      regions['Global'].push(source)
    }
  })
  
  // Remove empty regions
  return Object.fromEntries(
    Object.entries(regions).filter(([_, sources]) => sources.length > 0)
  )
})

// Computed
const sentimentPercentages = computed(() => {
  const total = (stats.value.annotations_by_sentiment?.bullish || 0) +
                (stats.value.annotations_by_sentiment?.bearish || 0) +
                (stats.value.annotations_by_sentiment?.neutral || 0)
  if (total === 0) return { bullish: 33.33, neutral: 33.33, bearish: 33.34 }
  return {
    bullish: ((stats.value.annotations_by_sentiment?.bullish || 0) / total) * 100,
    neutral: ((stats.value.annotations_by_sentiment?.neutral || 0) / total) * 100,
    bearish: ((stats.value.annotations_by_sentiment?.bearish || 0) / total) * 100
  }
})

// Methods
const loadStats = async () => {
  try {
    const response = await axios.get(`${API_BASE}/stats`)
    stats.value = response.data.statistics || {}
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const loadSources = async () => {
  try {
    const response = await axios.get(`${API_BASE}/sources`)
    availableSources.value = response.data.sources || []
  } catch (error) {
    console.error('Failed to load sources:', error)
  }
}

const loadArticles = async () => {
  loadingArticles.value = true
  try {
    let url = `${API_BASE}/articles?limit=50`
    if (filterSentiment.value) {
      url = `${API_BASE}/annotations?sentiment_label=${filterSentiment.value}&limit=50`
    }
    const response = await axios.get(url)
    articles.value = response.data.articles || response.data.annotations?.map(a => ({
      id: a.article_id,
      title: a.article_title,
      source: a.article_source,
      url: a.article_url,
      annotation: { sentiment: { label: a.sentiment?.label, score: a.sentiment?.score } }
    })) || []
  } catch (error) {
    console.error('Failed to load articles:', error)
  } finally {
    loadingArticles.value = false
  }
}

const loadRecentArticles = async () => {
  try {
    const response = await axios.get(`${API_BASE}/articles?limit=10&days_back=7`)
    recentArticles.value = response.data.articles || []
  } catch (error) {
    console.error('Failed to load recent articles:', error)
  }
}

const loadHotTerms = async () => {
  try {
    const response = await axios.get(`${API_BASE}/trends/hot?days_back=7&limit=10`)
    hotTerms.value = response.data.hot_terms || []
  } catch (error) {
    console.error('Failed to load hot terms:', error)
  }
}

const toggleSource = (key) => {
  const idx = selectedSources.value.indexOf(key)
  if (idx > -1) {
    selectedSources.value.splice(idx, 1)
  } else {
    selectedSources.value.push(key)
  }
}

const selectAllSources = () => {
  selectedSources.value = availableSources.value
    .filter(s => s.has_rss)
    .map(s => s.key)
}

const clearSources = () => {
  selectedSources.value = []
}

const getRegionFlag = (region) => {
  const flags = {
    'North America': '🌎',
    'Europe': '🇪🇺',
    'Asia-Pacific': '🌏',
    'Global': '🌐'
  }
  return flags[region] || '📰'
}

const startCrawl = async () => {
  crawling.value = true
  crawlMessage.value = ''
  crawlError.value = false
  crawlProgress.value = 0
  crawlStatusMessage.value = 'Starting crawl...'
  
  try {
    const params = new URLSearchParams()
    selectedSources.value.forEach(s => params.append('sources', s))
    params.append('days_back', crawlDaysBack.value)
    if (crawlKeywords.value) {
      crawlKeywords.value.split(',').forEach(k => params.append('keywords', k.trim()))
    }
    
    crawlProgress.value = 10
    crawlStatusMessage.value = 'Connecting to news sources...'
    
    const response = await axios.post(`${API_BASE}/crawl?${params.toString()}`)
    
    crawlProgress.value = 30
    crawlStatusMessage.value = 'Fetching RSS feeds...'
    
    crawlMessage.value = response.data.message || 'Crawl started!'
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      if (crawlProgress.value < 90) {
        crawlProgress.value += 10
        const messages = [
          'Parsing articles...',
          'Detecting related terms...',
          'Storing data...',
          'Almost done...'
        ]
        crawlStatusMessage.value = messages[Math.floor(Math.random() * messages.length)]
      }
    }, 1000)
    
    // Refresh after delay
    setTimeout(() => {
      clearInterval(progressInterval)
      crawlProgress.value = 100
      crawlStatusMessage.value = 'Completed!'
      loadStats()
      loadRecentArticles()
    }, 6000)
    
  } catch (error) {
    crawlError.value = true
    crawlMessage.value = error.response?.data?.detail || 'Failed to start crawl'
    crawlProgress.value = 0
  } finally {
    setTimeout(() => {
      crawling.value = false
      crawlProgress.value = 0
    }, 7000)
  }
}

const startAnnotate = async () => {
  annotating.value = true
  annotateMessage.value = ''
  annotateError.value = false
  
  try {
    const response = await axios.post(
      `${API_BASE}/annotate?method=${annotateMethod.value}&limit=${annotateLimit.value}`
    )
    annotateMessage.value = response.data.message || 'Annotation started!'
    
    // Refresh after delay
    setTimeout(() => {
      loadStats()
    }, 3000)
    
  } catch (error) {
    annotateError.value = true
    annotateMessage.value = error.response?.data?.detail || 'Failed to start annotation'
  } finally {
    annotating.value = false
  }
}

const loadTrend = async () => {
  if (!trendTerm.value) return
  
  loadingTrend.value = true
  try {
    const response = await axios.get(
      `${API_BASE}/trend/${encodeURIComponent(trendTerm.value)}?days_back=${trendDays.value}`
    )
    trendData.value = response.data
  } catch (error) {
    console.error('Failed to load trend:', error)
    trendData.value = null
  } finally {
    loadingTrend.value = false
  }
}

const exportData = async (type, format) => {
  let url = ''
  let filename = ''
  
  switch (type) {
    case 'articles':
      url = `${API_BASE}/export/articles?format=${format}`
      filename = `layer3_articles.${format}`
      break
    case 'sentiment':
      url = `${API_BASE}/export/sentiment?format=${format}`
      filename = `layer3_sentiment.${format}`
      break
    case 'doccano':
      url = `${API_BASE}/export/doccano`
      filename = 'doccano_export.jsonl'
      break
  }
  
  window.open(url, '_blank')
}

const downloadStats = async () => {
  try {
    const response = await axios.get(`${API_BASE}/stats`)
    const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'layer3_statistics.json'
    a.click()
  } catch (error) {
    console.error('Failed to download stats:', error)
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'Unknown'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const getSentimentEmoji = (label) => {
  switch (label) {
    case 'bullish': return '🟢'
    case 'bearish': return '🔴'
    case 'neutral': return '⚪'
    default: return '❓'
  }
}

const getSentimentBadgeClass = (label) => {
  const base = 'text-xl'
  return base
}

const getTrendDirectionClass = (direction) => {
  switch (direction) {
    case 'increasing': return 'text-green-600'
    case 'decreasing': return 'text-red-600'
    default: return 'text-gray-600'
  }
}

const getTrendDirectionEmoji = (direction) => {
  switch (direction) {
    case 'increasing': return '📈'
    case 'decreasing': return '📉'
    default: return '➡️'
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    loadStats(),
    loadSources(),
    loadRecentArticles(),
    loadHotTerms()
  ])
})
</script>
