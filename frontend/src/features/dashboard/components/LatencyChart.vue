<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
} from 'chart.js'
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { useDashboardStore } from '../stores/useDashboardStore'
import { storeToRefs } from 'pinia'
import { formatLatency } from '@core/utils/formatters'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip)

const store = useDashboardStore()
const { latencies, latencyLabels, avgLatency } = storeToRefs(store)

const last = computed(() => latencies.value[latencies.value.length - 1] ?? 0)
const peak = computed(() => latencies.value.length ? Math.max(...latencies.value) : 0)

const chartData = computed(() => ({
  labels: [...latencyLabels.value],
  datasets: [
    {
      data: [...latencies.value],
      borderColor: '#0a0a0a',
      backgroundColor: 'rgba(230, 57, 70, 0.06)',
      fill: true,
      tension: 0.32,
      pointRadius: 0,
      pointHoverRadius: 4,
      pointHoverBackgroundColor: '#e63946',
      pointHoverBorderColor: '#0a0a0a',
      pointHoverBorderWidth: 1,
      borderWidth: 1.5,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0a0a0a',
      padding: 10,
      titleFont: { family: 'JetBrains Mono', size: 11 },
      bodyFont:  { family: 'JetBrains Mono', size: 11 },
      cornerRadius: 2,
      displayColors: false,
      callbacks: { label: (ctx: any) => `${ctx.parsed.y.toFixed(1)} ms` },
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#a3a3a3',
        font: { family: 'JetBrains Mono', size: 9 },
        maxTicksLimit: 8,
      },
      grid: { display: false },
      border: { color: '#0a0a0a', width: 1 },
    },
    y: {
      ticks: { color: '#a3a3a3', font: { family: 'JetBrains Mono', size: 10 } },
      grid: { color: '#ececec', drawBorder: false },
      border: { display: false },
      beginAtZero: true,
    },
  },
} as const
</script>

<template>
  <BaseCard eyebrow="Tiempo real" title="Latencia end-to-end">
    <template #actions>
      <div class="lat-meta">
        <span class="lat-meta__pair"><em>last</em> <strong class="tnum">{{ formatLatency(last) }}</strong></span>
        <span class="lat-meta__pair"><em>avg</em>  <strong class="tnum">{{ formatLatency(avgLatency) }}</strong></span>
        <span class="lat-meta__pair"><em>peak</em> <strong class="tnum">{{ formatLatency(peak) }}</strong></span>
      </div>
    </template>
    <div class="chart">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </BaseCard>
</template>

<style scoped>
.chart { height: 240px; }

.lat-meta {
  display: inline-flex;
  gap: 1rem;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.05em;
}
.lat-meta__pair { color: var(--color-text-muted); display: inline-flex; gap: 0.4rem; }
.lat-meta__pair em { font-style: normal; text-transform: uppercase; letter-spacing: 0.14em; }
.lat-meta__pair strong { color: var(--color-text); font-weight: 500; }
</style>
