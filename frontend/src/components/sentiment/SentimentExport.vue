<template>
  <div class="space-y-6">
    <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <h3 class="text-lg font-semibold mb-4">📥 Export Data</h3>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Articles Export -->
        <div class="border border-gray-200 rounded-lg p-4">
          <h4 class="font-medium mb-2">📰 Articles with Annotations</h4>
          <p class="text-sm text-gray-500 mb-4">Export all crawled articles with their sentiment annotations.</p>
          <div class="flex gap-2">
            <button 
              @click="$emit('export', 'articles', 'json')"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              JSON
            </button>
            <button 
              @click="$emit('export', 'articles', 'jsonl')"
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
              @click="$emit('export', 'sentiment', 'jsonl')"
              class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
            >
              JSONL
            </button>
            <button 
              @click="$emit('export', 'sentiment', 'csv')"
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
            @click="$emit('export', 'doccano', 'jsonl')"
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
            @click="$emit('downloadStats')"
            class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
          >
            Download JSON
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['export', 'downloadStats'])
</script>
