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
        
        <!-- Running Crawler Detection Warning -->
        <div v-if="detectedRunningCrawl && !crawling" class="mb-6 bg-yellow-50 border-2 border-yellow-400 rounded-xl p-4">
          <div class="flex items-center gap-4">
            <span class="text-4xl">⚠️</span>
            <div class="flex-1">
              <h4 class="font-bold text-yellow-800">Crawler Already Running!</h4>
              <p class="text-yellow-700 text-sm">A crawler was detected running in the background. This may be from a previous session.</p>
            </div>
            <button 
              @click="forceStopCrawl"
              class="px-4 py-2 bg-red-500 text-white font-semibold rounded-lg hover:bg-red-600 transition-all"
            >
              ⏹ Force Stop
            </button>
          </div>
        </div>
        
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
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Days Back</label>
            <input 
              type="number" 
              v-model="crawlDaysBack" 
              min="1" 
              max="30"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Concurrency</label>
            <input 
              type="number" 
              v-model="crawlConcurrency" 
              min="1" 
              max="10"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Delay (sec)</label>
            <input 
              type="number" 
              v-model="crawlDelay" 
              min="0.5" 
              max="10"
              step="0.5"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
            />
          </div>
          <div class="flex items-end">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="crawlRotateUA" class="w-4 h-4 text-amber-600" />
              <span class="text-sm text-gray-700">Rotate User-Agent</span>
            </label>
          </div>
        </div>
        
        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-1">Keywords (optional)</label>
          <input 
            type="text" 
            v-model="crawlKeywords" 
            placeholder="inflation, fed, rate cut"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500"
          />
          <p class="text-xs text-gray-500 mt-1">Filter articles by keywords (comma-separated)</p>
        </div>

        <!-- Proxy Pool Configuration -->
        <div class="mb-4">
          <div class="flex items-center justify-between mb-1">
            <label class="block text-sm font-medium text-gray-700">Proxy Pool (optional)</label>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="useProxy" class="w-4 h-4 text-amber-600" />
              <span class="text-xs text-gray-600">Enable Proxies</span>
            </label>
          </div>
          <textarea 
            v-model="proxyList" 
            :disabled="!useProxy"
            placeholder="http://proxy1:8080&#10;socks5://user:pass@proxy2:1080&#10;http://192.168.1.100:3128"
            rows="3"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 font-mono text-sm disabled:bg-gray-100 disabled:text-gray-400"
          ></textarea>
          <p class="text-xs text-gray-500 mt-1">One proxy per line. Supports http/https/socks5. Format: protocol://[user:pass@]host:port</p>
        </div>

        <!-- Start/Stop Buttons -->
        <div class="flex gap-4">
          <button
            v-if="!crawling"
            @click="startCrawl"
            :disabled="selectedSources.length === 0"
            class="flex-1 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-lg hover:from-green-600 hover:to-emerald-600 disabled:opacity-50 transition-all shadow-lg"
          >
            <span class="flex items-center justify-center gap-2">
              <span>▶️</span>
              <span>Start Crawl ({{ selectedSources.length }} sources)</span>
            </span>
          </button>
          
          <button
            v-if="crawling"
            @click="stopCrawl"
            class="flex-1 py-3 bg-gradient-to-r from-red-500 to-rose-500 text-white font-semibold rounded-lg hover:from-red-600 hover:to-rose-600 transition-all shadow-lg"
          >
            <span class="flex items-center justify-center gap-2">
              <span>⏹</span>
              <span>Stop Crawl</span>
            </span>
          </button>
        </div>

        <!-- Status Display -->
        <div v-if="crawling || crawlMessage" class="mt-4 p-4 rounded-lg border" :class="crawlError ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'">
          <div class="flex items-center justify-between mb-2">
            <span class="font-medium" :class="crawlError ? 'text-red-700' : 'text-amber-800'">
              {{ crawlError ? '❌ Error' : (crawling ? '🔄 Crawling...' : '✅ Done') }}
            </span>
            <span v-if="crawling" class="text-sm text-amber-600">
              {{ crawlProgress }}% ({{ crawlStatusMessage }})
            </span>
          </div>
          <div v-if="crawling" class="h-2 bg-amber-200 rounded-full overflow-hidden mb-2">
            <div class="h-full bg-amber-500 transition-all" :style="{width: crawlProgress + '%'}"></div>
          </div>
          <p class="text-sm" :class="crawlError ? 'text-red-600' : 'text-amber-700'">{{ crawlMessage }}</p>
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
        <!-- Header with Search and Filters -->
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-semibold">📰 News Articles</h3>
            <span class="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              {{ articles.length }} articles
            </span>
          </div>
          
          <div class="flex flex-wrap gap-2 items-center">
            <!-- Search Box -->
            <div class="relative">
              <input 
                type="text" 
                v-model="articleSearchQuery"
                @input="filterArticlesLocally"
                placeholder="🔍 Search articles..."
                class="w-64 px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent text-sm"
              />
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
            </div>
            
            <!-- Source Filter -->
            <select 
              v-model="filterSource"
              @change="loadArticles"
              class="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Sources</option>
              <option v-for="source in uniqueSources" :key="source" :value="source">
                {{ source }}
              </option>
            </select>
            
            <!-- Sentiment Filter -->
            <select 
              v-model="filterSentiment"
              @change="loadArticles"
              class="px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              <option value="">All Sentiments</option>
              <option value="bullish">🟢 Bullish</option>
              <option value="bearish">🔴 Bearish</option>
              <option value="neutral">⚪ Neutral</option>
            </select>
            
            <!-- Refresh Button -->
            <button 
              @click="loadArticles" 
              :disabled="loadingArticles"
              class="px-3 py-2 bg-amber-100 text-amber-700 rounded-lg hover:bg-amber-200 transition-colors flex items-center gap-1"
            >
              <span :class="{'animate-spin': loadingArticles}">🔄</span>
              <span class="hidden md:inline">Refresh</span>
            </button>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="loadingArticles" class="text-center py-12">
          <div class="animate-spin w-10 h-10 border-4 border-amber-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p class="text-gray-500">Loading articles...</p>
        </div>
        
        <!-- Empty State -->
        <div v-else-if="filteredArticles.length === 0" class="text-center py-12">
          <div class="text-6xl mb-4">📭</div>
          <p class="text-gray-500 text-lg">No articles found.</p>
          <p class="text-gray-400 text-sm mt-2">Try adjusting your filters or crawl more news sources.</p>
        </div>
        
        <!-- Articles Grouped by Source -->
        <div v-else class="space-y-6">
          <div 
            v-for="(groupArticles, sourceName) in articlesBySource" 
            :key="sourceName"
            class="border border-gray-200 rounded-xl overflow-hidden"
          >
            <!-- Source Header (Collapsible) -->
            <button 
              @click="toggleSourceGroup(sourceName)"
              class="w-full px-4 py-3 bg-gradient-to-r from-gray-50 to-gray-100 flex items-center justify-between hover:from-gray-100 hover:to-gray-150 transition-colors"
            >
              <div class="flex items-center gap-3">
                <span class="text-lg">{{ getSourceEmoji(sourceName) }}</span>
                <span class="font-semibold text-gray-800">{{ sourceName }}</span>
                <span class="text-sm text-gray-500 bg-white px-2 py-0.5 rounded-full border">
                  {{ groupArticles.length }} articles
                </span>
              </div>
              <span class="text-gray-400 transition-transform" :class="{'rotate-180': expandedSources.includes(sourceName)}">
                ▼
              </span>
            </button>
            
            <!-- Articles in Group -->
            <div v-if="expandedSources.includes(sourceName)" class="divide-y divide-gray-100">
              <div 
                v-for="article in groupArticles.slice(0, 10)" 
                :key="article.id"
                class="p-4 hover:bg-amber-50 transition-colors"
              >
                <div class="flex items-start gap-3">
                  <span class="text-lg mt-0.5">
                    {{ getSentimentEmoji(article.annotation?.sentiment?.label) }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <h4 class="font-medium text-gray-900 line-clamp-2">{{ article.title }}</h4>
                    <p class="text-sm text-gray-500 mt-1 line-clamp-2">{{ article.summary?.substring(0, 150) }}...</p>
                    <div class="flex items-center flex-wrap gap-3 mt-2 text-xs text-gray-400">
                      <span class="flex items-center gap-1">
                        📅 {{ formatDate(article.published_date) }}
                      </span>
                      <span v-if="article.annotation" class="flex items-center gap-1">
                        🎯 {{ (article.annotation.sentiment?.score * 100).toFixed(0) }}% confidence
                      </span>
                      <a 
                        :href="article.url" 
                        target="_blank" 
                        class="text-amber-600 hover:text-amber-700 hover:underline flex items-center gap-1"
                      >
                        View Source ↗
                      </a>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- Show More Button -->
              <div v-if="groupArticles.length > 10" class="p-3 bg-gray-50 text-center">
                <span class="text-sm text-gray-500">
                  + {{ groupArticles.length - 10 }} more articles from {{ sourceName }}
                </span>
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

    <!-- Tasks Tab -->
    <div v-if="activeTab === 'tasks'" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 class="text-lg font-semibold mb-4">📋 Task Manager</h3>
        
        <!-- Active Task -->
        <div v-if="currentTask" class="mb-6 bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-xl p-6">
          <div class="flex items-center gap-4 mb-4">
            <div class="relative">
              <div class="w-16 h-16 border-4 border-amber-200 border-t-amber-600 rounded-full animate-spin"></div>
              <div class="absolute inset-0 flex items-center justify-center text-2xl">
                {{ currentTask.type === 'crawl' ? '📰' : '🤖' }}
              </div>
            </div>
            <div class="flex-1">
              <h4 class="text-lg font-bold text-amber-900">{{ currentTask.name }}</h4>
              <p class="text-amber-700 text-sm">{{ currentTask.message }}</p>
            </div>
            <div class="text-right">
              <div class="text-3xl font-bold text-amber-600">{{ currentTask.progress }}%</div>
            </div>
          </div>
          
          <div class="space-y-2">
            <div class="h-4 bg-amber-200 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-amber-500 to-orange-500 transition-all duration-500 rounded-full"
                :style="{width: currentTask.progress + '%'}"
              ></div>
            </div>
            
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
              <div class="bg-white/50 rounded-lg p-3">
                <div class="text-gray-500">Current Source</div>
                <div class="font-semibold">{{ currentTask.currentSource || '-' }}</div>
              </div>
              <div class="bg-white/50 rounded-lg p-3">
                <div class="text-gray-500">Sources Progress</div>
                <div class="font-semibold">{{ currentTask.completedSources }} / {{ currentTask.totalSources }}</div>
              </div>
              <div class="bg-white/50 rounded-lg p-3">
                <div class="text-gray-500">Articles Found</div>
                <div class="font-semibold">{{ currentTask.articlesFound || 0 }}</div>
              </div>
              <div class="bg-white/50 rounded-lg p-3">
                <div class="text-gray-500">Started At</div>
                <div class="font-semibold">{{ formatTime(currentTask.startedAt) }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- No Active Task -->
        <div v-else class="mb-6 bg-gray-50 border-2 border-gray-200 border-dashed rounded-xl p-8 text-center">
          <div class="text-6xl mb-4">😴</div>
          <p class="text-gray-500 text-lg">No active tasks</p>
          <p class="text-gray-400 text-sm mt-2">Start a crawl or annotation from the "Crawl News" tab</p>
        </div>
        
        <!-- Task History -->
        <h4 class="font-semibold text-gray-700 mb-3">📜 Task History</h4>
        <div v-if="taskHistory.length === 0" class="text-gray-500 text-center py-8">
          No task history yet.
        </div>
        <div v-else class="space-y-3">
          <div 
            v-for="task in taskHistory.slice(0, 10)" 
            :key="task.id"
            class="flex items-center gap-4 p-4 bg-gray-50 rounded-lg"
          >
            <span class="text-2xl">{{ task.success ? '✅' : '❌' }}</span>
            <div class="flex-1">
              <div class="font-medium">{{ task.name }}</div>
              <div class="text-sm text-gray-500">{{ task.message }}</div>
            </div>
            <div class="text-right text-sm text-gray-400">
              <div>{{ formatTime(task.completedAt) }}</div>
              <div v-if="task.articlesFound">{{ task.articlesFound }} articles</div>
            </div>
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
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import { API_BASE as API_ROOT } from '@/services/api'

const API_BASE = `${API_ROOT}/api/sentiment`

// State
const activeTab = ref('dashboard')
const stats = ref({})
const recentArticles = ref([])
const articles = ref([])
const loadingArticles = ref(false)
const filterSentiment = ref('')
const filterSource = ref('')
const articleSearchQuery = ref('')
const expandedSources = ref([])  // For collapsible source groups

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
const crawlConcurrency = ref(3)
const crawlDelay = ref(1.0)
const crawlRotateUA = ref(true)
const useProxy = ref(false)
const proxyList = ref('')
const detectedRunningCrawl = ref(false)

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

// Computed - Filter articles by search query
const filteredArticles = computed(() => {
  let result = articles.value
  
  // Filter by search query
  if (articleSearchQuery.value) {
    const query = articleSearchQuery.value.toLowerCase()
    result = result.filter(a => 
      a.title?.toLowerCase().includes(query) ||
      a.summary?.toLowerCase().includes(query)
    )
  }
  
  return result
})

// Computed - Get unique sources from articles
const uniqueSources = computed(() => {
  const sources = [...new Set(articles.value.map(a => a.source))]
  return sources.sort()
})

// Computed - Group articles by source
const articlesBySource = computed(() => {
  const groups = {}
  filteredArticles.value.forEach(article => {
    const source = article.source || 'Unknown'
    if (!groups[source]) {
      groups[source] = []
    }
    groups[source].push(article)
  })
  
  // Sort groups by article count (descending)
  return Object.fromEntries(
    Object.entries(groups).sort((a, b) => b[1].length - a[1].length)
  )
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
    let url = `${API_BASE}/articles?limit=500`  // Increased limit to load all articles
    if (filterSentiment.value) {
      url = `${API_BASE}/annotations?sentiment_label=${filterSentiment.value}&limit=500`
    }
    if (filterSource.value) {
      url += `&source=${filterSource.value}`
    }
    const response = await axios.get(url)
    articles.value = response.data.articles || response.data.annotations?.map(a => ({
      id: a.article_id,
      title: a.article_title,
      source: a.article_source,
      url: a.article_url,
      annotation: { sentiment: { label: a.sentiment?.label, score: a.sentiment?.score } }
    })) || []
    
    // Default: keep all groups collapsed (empty array)
    expandedSources.value = []
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

// Toggle source group expansion
const toggleSourceGroup = (sourceName) => {
  const idx = expandedSources.value.indexOf(sourceName)
  if (idx > -1) {
    expandedSources.value.splice(idx, 1)
  } else {
    expandedSources.value.push(sourceName)
  }
}

// Get emoji for news source
const getSourceEmoji = (source) => {
  const sourceEmojis = {
    'bloomberg': '📈',
    'reuters': '🌍',
    'wsj': '📰',
    'ft': '💼',
    'bbc': '🇬🇧',
    'guardian': '📝',
    'cnbc': '📺',
    'yahoo_finance': '💹',
    'economictimes': '🇮🇳',
    'nikkei': '🇯🇵',
    'xinhua': '🇨🇳',
    'chinadaily': '🇨🇳',
    'caixin': '🇨🇳',
    'dw': '🇩🇪',
    'koreaherald': '🇰🇷',
    'afr': '🇦🇺',
    'globeandmail': '🇨🇦',
    'marketwatch': '📊',
    'japantimes': '🇯🇵',
  }
  return sourceEmojis[source?.toLowerCase()] || '📰'
}

// Local filter function (no API call)
const filterArticlesLocally = () => {
  // The filtering is handled by the computed property
  // This function is just for input event binding
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
    params.append('max_concurrent', crawlConcurrency.value)
    params.append('delay_seconds', crawlDelay.value)
    params.append('rotate_ua', crawlRotateUA.value)
    
    if (crawlKeywords.value) {
      crawlKeywords.value.split(',').forEach(k => params.append('keywords', k.trim()))
    }
    
    // Add proxies if enabled
    if (useProxy.value && proxyList.value.trim()) {
      proxyList.value.split('\n').filter(p => p.trim()).forEach(p => params.append('proxies', p.trim()))
    }
    
    // Clear detected running crawl flag since we're starting our own
    detectedRunningCrawl.value = false
    
    const response = await axios.post(`${API_BASE}/crawl?${params.toString()}`)
    
    if (!response.data.success) {
      crawlMessage.value = response.data.message || 'Crawl already in progress'
      crawling.value = false
      return
    }
    
    crawlMessage.value = response.data.message || 'Crawl started!'
    
    // Poll for real progress from backend
    const pollStatus = async () => {
      try {
        const statusRes = await axios.get(`${API_BASE}/crawl/status`)
        const status = statusRes.data.status
        const progress = statusRes.data.progress
        
        crawlProgress.value = progress
        crawlStatusMessage.value = status.message || 'Crawling...'
        crawlMessage.value = `${status.completed_sources}/${status.total_sources} sources • ${status.articles_found} articles found`
        
        // If still crawling, continue polling
        if (status.is_crawling) {
          setTimeout(pollStatus, 1000)
        } else {
          // Crawl completed
          crawlProgress.value = 100
          crawlMessage.value = status.message
          crawling.value = false
          
          // Refresh data
          loadStats()
          loadRecentArticles()
        }
      } catch (error) {
        console.error('Failed to get crawl status:', error)
        if (crawling.value) {
          setTimeout(pollStatus, 2000)
        }
      }
    }
    
    // Start polling
    setTimeout(pollStatus, 500)
    
  } catch (error) {
    crawlError.value = true
    crawlMessage.value = error.response?.data?.detail || 'Failed to start crawl'
    crawlProgress.value = 0
    crawling.value = false
  }
}

const stopCrawl = async () => {
  try {
    crawlStatusMessage.value = 'Stopping crawl...'
    const response = await axios.post(`${API_BASE}/crawl/stop`)
    crawlMessage.value = response.data.message || 'Stop signal sent'
    
    // Verify stop with polling (up to 15 seconds)
    let attempts = 0
    const verifyStop = async () => {
      try {
        const statusRes = await axios.get(`${API_BASE}/crawl/status`)
        if (!statusRes.data.status?.is_crawling) {
          crawling.value = false
          crawlProgress.value = 100
          crawlMessage.value = '✅ Crawler stopped successfully'
          crawlStatusMessage.value = 'Stopped'
          loadStats()
          loadRecentArticles()
          return
        }
        
        attempts++
        crawlStatusMessage.value = `Stopping... (${attempts}/15)`
        
        if (attempts < 15) {
          setTimeout(verifyStop, 1000)
        } else {
          crawlMessage.value = '⚠ Crawler might still be finishing current source. Check status again.'
          crawlError.value = true
        }
      } catch (error) {
        // If can't get status, assume stopped
        crawling.value = false
        crawlMessage.value = 'Crawler status unknown. Assuming stopped.'
      }
    }
    
    setTimeout(verifyStop, 1000)
    
  } catch (error) {
    console.error('Failed to stop crawl:', error)
    crawlMessage.value = 'Failed to send stop signal'
    crawlError.value = true
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
  // Check if a crawler is already running (from previous session)
  try {
    const statusRes = await axios.get(`${API_BASE}/crawl/status`)
    if (statusRes.data.status?.is_crawling) {
      detectedRunningCrawl.value = true
      console.warn('⚠ Detected running crawler from previous session')
    }
  } catch (error) {
    console.log('Could not check crawler status')
  }
  
  await Promise.all([
    loadStats(),
    loadSources(),
    loadRecentArticles(),
    loadHotTerms()
  ])
})

// Force stop crawler (for detected running crawls)
const forceStopCrawl = async () => {
  try {
    await axios.post(`${API_BASE}/crawl/stop`)
    
    // Verify stop with polling (up to 10 seconds)
    let attempts = 0
    const verifyStop = async () => {
      const statusRes = await axios.get(`${API_BASE}/crawl/status`)
      if (!statusRes.data.status?.is_crawling) {
        detectedRunningCrawl.value = false
        crawlMessage.value = '✅ Crawler stopped successfully'
        return
      }
      attempts++
      if (attempts < 10) {
        setTimeout(verifyStop, 1000)
      } else {
        crawlMessage.value = '⚠ Crawler may still be running. Refresh page to check.'
        crawlError.value = true
      }
    }
    setTimeout(verifyStop, 1000)
  } catch (error) {
    console.error('Failed to force stop crawler:', error)
    crawlMessage.value = 'Failed to stop crawler'
    crawlError.value = true
  }
}

// Watch for tab changes - auto-refresh articles when switching to articles tab
watch(activeTab, async (newTab) => {
  if (newTab === 'articles') {
    loadArticles()
  }
  // Check crawler status when switching to crawl tab
  if (newTab === 'crawl') {
    try {
      const statusRes = await axios.get(`${API_BASE}/crawl/status`)
      if (statusRes.data.status?.is_crawling && !crawling.value) {
        detectedRunningCrawl.value = true
      }
    } catch (error) {}
  }
})
</script>
