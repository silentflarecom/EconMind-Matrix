<script setup>
/**
 * TrendChart.vue
 * D3.js based trend visualization component
 * Shows sentiment trend over time with area chart
 */
import { ref, onMounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  trendData: {
    type: Array,
    default: () => []
  },
  term: {
    type: String,
    default: ''
  }
})

const chartContainer = ref(null)
const chartWidth = ref(300)
const chartHeight = 160

// Draw chart when data changes
watch(() => props.trendData, (newData) => {
  if (newData && newData.length > 0) {
    nextTick(() => drawChart(newData))
  }
}, { immediate: true })

onMounted(() => {
  if (props.trendData && props.trendData.length > 0) {
    drawChart(props.trendData)
  }
})

const drawChart = (data) => {
  if (!chartContainer.value || !data || data.length === 0) return
  
  // Clear previous chart
  d3.select(chartContainer.value).selectAll('*').remove()
  
  const margin = { top: 20, right: 20, bottom: 30, left: 35 }
  const width = chartContainer.value.clientWidth - margin.left - margin.right
  const height = chartHeight - margin.top - margin.bottom
  
  const svg = d3.select(chartContainer.value)
    .append('svg')
    .attr('width', width + margin.left + margin.right)
    .attr('height', height + margin.top + margin.bottom)
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)
  
  // Parse dates
  const parseDate = d3.timeParse('%Y-%m-%d')
  const chartData = data.map(d => ({
    date: parseDate(d.date) || new Date(d.date),
    sentiment: d.avg_sentiment || 0,
    mentions: d.mention_count || 0,
    bullish: d.bullish_count || 0,
    bearish: d.bearish_count || 0,
    neutral: d.neutral_count || 0
  }))
  
  // Scales
  const x = d3.scaleTime()
    .domain(d3.extent(chartData, d => d.date))
    .range([0, width])
  
  const y = d3.scaleBand()
    .domain(['bearish', 'neutral', 'bullish'])
    .range([height, 0])
    .padding(0.1)
  
  const yMentions = d3.scaleLinear()
    .domain([0, d3.max(chartData, d => d.mentions) || 1])
    .range([height, 0])
  
  // Add gradient for area
  const defs = svg.append('defs')
  
  const gradient = defs.append('linearGradient')
    .attr('id', 'sentiment-gradient')
    .attr('x1', '0%')
    .attr('y1', '0%')
    .attr('x2', '0%')
    .attr('y2', '100%')
  
  gradient.append('stop')
    .attr('offset', '0%')
    .attr('stop-color', '#10b981')
    .attr('stop-opacity', 0.8)
  
  gradient.append('stop')
    .attr('offset', '50%')
    .attr('stop-color', '#6b7280')
    .attr('stop-opacity', 0.5)
  
  gradient.append('stop')
    .attr('offset', '100%')
    .attr('stop-color', '#ef4444')
    .attr('stop-opacity', 0.8)
  
  // Draw area for sentiment
  const sentimentY = d3.scaleLinear()
    .domain([-1, 1])
    .range([height, 0])
  
  const area = d3.area()
    .x(d => x(d.date))
    .y0(sentimentY(0))
    .y1(d => sentimentY(d.sentiment))
    .curve(d3.curveMonotoneX)
  
  svg.append('path')
    .datum(chartData)
    .attr('fill', 'url(#sentiment-gradient)')
    .attr('d', area)
    .attr('opacity', 0.6)
  
  // Line for sentiment
  const line = d3.line()
    .x(d => x(d.date))
    .y(d => sentimentY(d.sentiment))
    .curve(d3.curveMonotoneX)
  
  svg.append('path')
    .datum(chartData)
    .attr('fill', 'none')
    .attr('stroke', '#8b5cf6')
    .attr('stroke-width', 2)
    .attr('d', line)
  
  // Bars for mentions (optional overlay)
  svg.selectAll('.mention-bar')
    .data(chartData)
    .enter()
    .append('rect')
    .attr('class', 'mention-bar')
    .attr('x', d => x(d.date) - 3)
    .attr('y', d => yMentions(d.mentions))
    .attr('width', 6)
    .attr('height', d => height - yMentions(d.mentions))
    .attr('fill', '#6366f1')
    .attr('opacity', 0.3)
  
  // Zero line
  svg.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', sentimentY(0))
    .attr('y2', sentimentY(0))
    .attr('stroke', '#9ca3af')
    .attr('stroke-dasharray', '4,2')
    .attr('stroke-width', 1)
  
  // X Axis
  svg.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x)
      .ticks(5)
      .tickFormat(d3.timeFormat('%m/%d')))
    .attr('font-size', '9px')
    .attr('color', '#9ca3af')
  
  // Y Axis labels
  svg.append('text')
    .attr('x', -10)
    .attr('y', 5)
    .attr('font-size', '8px')
    .attr('fill', '#10b981')
    .text('📈')
  
  svg.append('text')
    .attr('x', -10)
    .attr('y', height)
    .attr('font-size', '8px')
    .attr('fill', '#ef4444')
    .text('📉')
  
  // Add dots with tooltips
  svg.selectAll('.dot')
    .data(chartData)
    .enter()
    .append('circle')
    .attr('class', 'dot')
    .attr('cx', d => x(d.date))
    .attr('cy', d => sentimentY(d.sentiment))
    .attr('r', 4)
    .attr('fill', d => d.sentiment > 0 ? '#10b981' : d.sentiment < 0 ? '#ef4444' : '#6b7280')
    .attr('stroke', 'white')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('mouseover', function(event, d) {
      d3.select(this).attr('r', 6)
      
      // Show tooltip
      const tooltip = d3.select(chartContainer.value)
        .append('div')
        .attr('class', 'chart-tooltip')
        .style('position', 'absolute')
        .style('background', 'rgba(0,0,0,0.8)')
        .style('color', 'white')
        .style('padding', '6px 10px')
        .style('border-radius', '6px')
        .style('font-size', '11px')
        .style('pointer-events', 'none')
        .style('left', `${event.offsetX + 10}px`)
        .style('top', `${event.offsetY - 30}px`)
        .html(`
          <strong>${d3.timeFormat('%Y-%m-%d')(d.date)}</strong><br/>
          Mentions: ${d.mentions}<br/>
          Sentiment: ${d.sentiment.toFixed(2)}
        `)
    })
    .on('mouseout', function() {
      d3.select(this).attr('r', 4)
      d3.selectAll('.chart-tooltip').remove()
    })
}
</script>

<template>
  <div class="trend-chart-container">
    <div ref="chartContainer" class="w-full h-40 relative"></div>
    <div v-if="!trendData || trendData.length === 0" class="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
      No trend data available
    </div>
  </div>
</template>

<style scoped>
.trend-chart-container {
  position: relative;
  width: 100%;
  min-height: 160px;
}
</style>
