<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { ALL_COMMANDS } from '@core/types/commands'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'
import { useDashboardStore } from '../stores/useDashboardStore'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const store = useDashboardStore()

const chartData = computed(() => ({
  labels: [...ALL_COMMANDS],
  datasets: [
    {
      data: store.getCountForCommands(),
      backgroundColor: ALL_COMMANDS.map(
        cmd => colors.command[cmd as CommandColor] ?? '#64748b'
      ),
      borderWidth: 0,
      borderRadius: 4,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { enabled: true } },
  scales: {
    x: { ticks: { color: '#94a3b8', font: { size: 9 }, maxRotation: 45 }, grid: { display: false } },
    y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(51,65,85,0.3)' }, beginAtZero: true },
  },
} as const
</script>

<template>
  <BaseCard title="Predicciones por Clase">
    <div class="chart-wrapper">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </BaseCard>
</template>

<style scoped>
.chart-wrapper { height: 200px; }
</style>
