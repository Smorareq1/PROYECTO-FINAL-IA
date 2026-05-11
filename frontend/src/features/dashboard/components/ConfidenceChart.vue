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

const labels = computed(() => ALL_COMMANDS.map(c => c.replace(/_/g, ' ')))

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      data: store.getCountForCommands(),
      backgroundColor: ALL_COMMANDS.map(
        cmd => colors.command[cmd as CommandColor] ?? '#a3a3a3',
      ),
      borderWidth: 0,
      borderRadius: 0,
      barPercentage: 0.78,
      categoryPercentage: 0.85,
    },
  ],
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      enabled: true,
      backgroundColor: '#0a0a0a',
      padding: 10,
      titleFont: { family: 'JetBrains Mono', size: 11 },
      bodyFont:  { family: 'JetBrains Mono', size: 11 },
      cornerRadius: 2,
      displayColors: false,
    },
  },
  scales: {
    x: {
      ticks: {
        color: '#525252',
        font: { family: 'JetBrains Mono', size: 9 },
        maxRotation: 45,
        minRotation: 30,
      },
      grid: { display: false },
      border: { color: '#0a0a0a', width: 1 },
    },
    y: {
      ticks: {
        color: '#a3a3a3',
        font: { family: 'JetBrains Mono', size: 10 },
        precision: 0,
      },
      grid: { color: '#ececec', drawBorder: false },
      border: { display: false },
      beginAtZero: true,
    },
  },
} as const
</script>

<template>
  <BaseCard eyebrow="Distribucion" title="Predicciones por clase">
    <div class="chart">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </BaseCard>
</template>

<style scoped>
.chart { height: 240px; }
</style>
