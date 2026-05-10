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

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip)

const store = useDashboardStore()
const { latencies, latencyLabels } = storeToRefs(store)

const chartData = computed(() => ({
  labels: [...latencyLabels.value],
  datasets: [
    {
      data: [...latencies.value],
      borderColor: '#38bdf8',
      backgroundColor: 'rgba(56,189,248,0.1)',
      fill: true,
      tension: 0.3,
      pointRadius: 3,
      pointBackgroundColor: '#38bdf8',
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#94a3b8', font: { size: 9 }, maxTicksLimit: 10 }, grid: { display: false } },
    y: {
      ticks: { color: '#94a3b8' },
      grid: { color: 'rgba(51,65,85,0.3)' },
      beginAtZero: true,
      title: { display: true, text: 'ms', color: '#94a3b8' },
    },
  },
} as const
</script>

<template>
  <BaseCard title="Latencia en Tiempo Real">
    <div class="chart-wrapper">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </BaseCard>
</template>

<style scoped>
.chart-wrapper { height: 200px; }
</style>
