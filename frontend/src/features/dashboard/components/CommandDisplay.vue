<script setup lang="ts">
import { ref, watch } from 'vue'
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { useDashboardStore } from '../stores/useDashboardStore'
import { storeToRefs } from 'pinia'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'
import { formatConfidence, formatLatency, formatCommandLabel } from '@core/utils/formatters'

const store = useDashboardStore()
const { lastEvent, totalPredictions, acceptedPredictions, avgLatency } = storeToRefs(store)

const flash = ref(false)
watch(lastEvent, () => {
  flash.value = false
  void document.body.offsetWidth
  flash.value = true
})

function commandColor(cmd: string): string {
  return colors.command[cmd as CommandColor] ?? colors.accent.default
}
</script>

<template>
  <BaseCard title="Comando Reconocido" padding="lg">
    <div class="command-display">
      <div
        class="command-text"
        :class="{ flash }"
        :style="{
          color: lastEvent
            ? lastEvent.rejected
              ? colors.danger.default
              : commandColor(lastEvent.command)
            : colors.text.secondary,
        }"
      >
        {{ lastEvent ? (lastEvent.rejected ? '—' : formatCommandLabel(lastEvent.command)) : 'Esperando...' }}
      </div>

      <div class="meta">
        <span>Confianza: <strong>{{ lastEvent ? formatConfidence(lastEvent.confidence) : '—' }}</strong></span>
        <span>Latencia: <strong>{{ lastEvent ? formatLatency(lastEvent.latency_ms) : '—' }}</strong></span>
      </div>

      <div class="stats">
        <div class="stat">
          <span class="stat-value">{{ totalPredictions }}</span>
          <span class="stat-label">Total</span>
        </div>
        <div class="stat">
          <span class="stat-value stat-value--success">{{ acceptedPredictions }}</span>
          <span class="stat-label">Aceptados</span>
        </div>
        <div class="stat">
          <span class="stat-value stat-value--warning">{{ formatLatency(avgLatency) }}</span>
          <span class="stat-label">Latencia Prom.</span>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.command-display { text-align: center; }

.command-text {
  font-size: 3.5rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  min-height: 4.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 200ms;
}
.command-text.flash { animation: flashIn 0.4s ease; }
@keyframes flashIn {
  0% { transform: scale(1.15); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

.meta {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 0.75rem;
  color: var(--color-text-secondary, #94a3b8);
  font-size: 1rem;
}
.meta strong { color: var(--color-accent, #38bdf8); }

.stats {
  display: flex;
  gap: 2rem;
  justify-content: center;
  margin-top: 1.5rem;
}
.stat { text-align: center; }
.stat-value { font-size: 1.8rem; font-weight: 700; color: var(--color-accent, #38bdf8); }
.stat-value--success { color: var(--color-success, #4ade80); }
.stat-value--warning { color: #fbbf24; }
.stat-label { display: block; font-size: 0.75rem; color: var(--color-text-secondary, #94a3b8); text-transform: uppercase; }
</style>
