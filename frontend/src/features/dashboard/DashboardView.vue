<script setup lang="ts">
import CommandDisplay from './components/CommandDisplay.vue'
import ListeningIndicator from './components/ListeningIndicator.vue'
import ConfidenceChart from './components/ConfidenceChart.vue'
import LatencyChart from './components/LatencyChart.vue'
import PredictionLog from './components/PredictionLog.vue'
import CommandGrid from '@features/controls/components/CommandGrid.vue'
import { useInferenceStream } from './composables/useInferenceStream'
import { usePolling } from '@core/composables/usePolling'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import { POLL_INTERVAL_MS } from '@core/utils/constants'

useInferenceStream()

const systemStore = useSystemStore()
usePolling(() => systemStore.refresh(), POLL_INTERVAL_MS)
</script>

<template>
  <div class="dashboard-grid">
    <div class="dashboard-grid__main">
      <CommandDisplay />
    </div>

    <div class="dashboard-grid__sidebar">
      <ListeningIndicator />
      <CommandGrid />
    </div>

    <div class="dashboard-grid__chart-left">
      <ConfidenceChart />
    </div>

    <div class="dashboard-grid__chart-right">
      <LatencyChart />
    </div>

    <div class="dashboard-grid__log">
      <PredictionLog />
    </div>
  </div>
</template>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 320px;
  grid-template-rows: auto auto 1fr;
  gap: 1.25rem;
}
.dashboard-grid__main      { grid-column: 1 / 3; }
.dashboard-grid__sidebar   { grid-column: 3 / 4; grid-row: 1 / 3; display: flex; flex-direction: column; gap: 1.25rem; }
.dashboard-grid__chart-left  { grid-column: 1 / 2; }
.dashboard-grid__chart-right { grid-column: 2 / 3; }
.dashboard-grid__log       { grid-column: 1 / 4; }
</style>
