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
  <div class="dash">
    <section class="dash__hero">
      <CommandDisplay />
    </section>

    <aside class="dash__side">
      <ListeningIndicator />
      <CommandGrid />
    </aside>

    <section class="dash__chart dash__chart--left">
      <ConfidenceChart />
    </section>

    <section class="dash__chart dash__chart--right">
      <LatencyChart />
    </section>

    <section class="dash__log">
      <PredictionLog />
    </section>
  </div>
</template>

<style scoped>
.dash {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.55fr);
  grid-template-areas:
    'hero  side'
    'chL   side'
    'chR   side'
    'log   log';
  gap: 1.25rem;
  margin-top: 1.5rem;
}

.dash__hero  { grid-area: hero; }
.dash__side  { grid-area: side; display: flex; flex-direction: column; gap: 1.25rem; }
.dash__chart--left  { grid-area: chL; }
.dash__chart--right { grid-area: chR; }
.dash__log   { grid-area: log; }

@media (min-width: 1280px) {
  .dash {
    grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr) minmax(320px, 0.5fr);
    grid-template-areas:
      'hero hero side'
      'chL  chR  side'
      'log  log  log';
  }
}

@media (max-width: 900px) {
  .dash {
    grid-template-columns: 1fr;
    grid-template-areas:
      'hero'
      'side'
      'chL'
      'chR'
      'log';
  }
}
</style>
