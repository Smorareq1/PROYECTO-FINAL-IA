<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useDashboardStore } from '../stores/useDashboardStore'
import { storeToRefs } from 'pinia'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'
import { formatConfidence, formatLatency, formatCommandLabel } from '@core/utils/formatters'

const store = useDashboardStore()
const { lastEvent, totalPredictions, acceptedPredictions, avgLatency } = storeToRefs(store)

const flashKey = ref(0)
watch(lastEvent, () => { flashKey.value++ })

const acceptanceRate = computed(() => {
  if (totalPredictions.value === 0) return 0
  return (acceptedPredictions.value / totalPredictions.value) * 100
})

const accentColor = computed(() => {
  if (!lastEvent.value) return '#a3a3a3'
  if (lastEvent.value.rejected) return colors.danger.default
  return colors.command[lastEvent.value.command as CommandColor] ?? colors.accent.default
})

const displayLabel = computed(() => {
  if (!lastEvent.value) return 'En espera'
  if (lastEvent.value.rejected) return 'Rechazado'
  return formatCommandLabel(lastEvent.value.command)
})

const statusLine = computed(() => {
  if (!lastEvent.value) return 'Sin entrada de audio'
  if (lastEvent.value.rejected) return 'Por debajo del umbral de confianza'
  return 'Comando aceptado &middot; enviado al Arduino'
})
</script>

<template>
  <article class="hero">
    <header class="hero__head">
      <div class="hero__head-left">
        <span class="eyebrow">Comando reconocido</span>
        <span class="hero__index tnum">#{{ String(totalPredictions).padStart(4, '0') }}</span>
      </div>
      <div class="hero__head-right">
        <span class="eyebrow">{{ lastEvent?.rejected ? 'Rejected' : 'Accepted' }}</span>
        <span class="hero__chip" :style="{ background: accentColor }" />
      </div>
    </header>

    <div class="hero__body">
      <div class="hero__rule" :style="{ background: accentColor }" />

      <div class="hero__display">
        <transition name="flip" mode="out-in">
          <h2
            :key="flashKey"
            class="hero__title"
            :class="{ 'hero__title--idle': !lastEvent }"
            :style="{ color: lastEvent ? 'var(--color-text)' : 'var(--color-text-muted)' }"
          >
            <span class="hero__title-italic">&laquo;</span>
            {{ displayLabel }}
            <span class="hero__title-italic">&raquo;</span>
          </h2>
        </transition>
        <p class="hero__status" v-html="statusLine" />
      </div>

      <dl class="hero__metrics">
        <div class="metric">
          <dt class="eyebrow">Confianza</dt>
          <dd class="metric__value tnum">
            {{ lastEvent ? formatConfidence(lastEvent.confidence) : '—' }}
          </dd>
          <div class="metric__bar">
            <div
              class="metric__bar-fill"
              :style="{
                width: lastEvent ? `${(lastEvent.confidence * 100).toFixed(1)}%` : '0%',
                background: accentColor,
              }"
            />
          </div>
        </div>

        <div class="metric">
          <dt class="eyebrow">Latencia</dt>
          <dd class="metric__value tnum">
            {{ lastEvent ? formatLatency(lastEvent.latency_ms) : '—' }}
          </dd>
          <span class="metric__sub">end-to-end</span>
        </div>

        <div class="metric metric--divider">
          <dt class="eyebrow">Total</dt>
          <dd class="metric__value tnum">{{ totalPredictions }}</dd>
          <span class="metric__sub">predicciones</span>
        </div>

        <div class="metric">
          <dt class="eyebrow">Aceptacion</dt>
          <dd class="metric__value tnum">{{ acceptanceRate.toFixed(0) }}%</dd>
          <span class="metric__sub tnum">{{ acceptedPredictions }} aceptados</span>
        </div>

        <div class="metric">
          <dt class="eyebrow">Lat. promedio</dt>
          <dd class="metric__value tnum">{{ formatLatency(avgLatency) }}</dd>
          <span class="metric__sub">ventana movil</span>
        </div>
      </dl>
    </div>
  </article>
</template>

<style scoped>
.hero {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 380px;
  position: relative;
  overflow: hidden;
}

.hero__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.75rem;
  border-bottom: 1px solid var(--color-border-subtle);
}
.hero__head-left,
.hero__head-right { display: inline-flex; align-items: center; gap: 0.75rem; }
.hero__index {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  color: var(--color-text-muted);
}
.hero__chip {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  background: var(--color-text-muted);
  transition: background var(--duration-base) var(--ease-out);
}

.hero__body {
  display: grid;
  grid-template-columns: 1fr;
  flex: 1;
}

.hero__rule {
  height: 4px;
  background: var(--color-text-muted);
  transition: background var(--duration-base) var(--ease-out);
}

.hero__display {
  padding: 2.5rem 2.25rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: flex-start;
}

.hero__title {
  font-family: var(--font-serif);
  font-weight: 400;
  font-size: clamp(3rem, 7vw, 6rem);
  line-height: 0.92;
  letter-spacing: -0.04em;
  color: var(--color-text);
  text-transform: capitalize;
  display: inline-flex;
  align-items: baseline;
  gap: 0.4rem;
}
.hero__title-italic {
  font-style: italic;
  font-weight: 300;
  color: var(--color-accent);
}
.hero__title--idle .hero__title-italic { color: var(--color-text-muted); }

.hero__status {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
  text-transform: uppercase;
}

/* metrics */
.hero__metrics {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0;
  border-top: 1px solid var(--color-border-subtle);
}
.metric {
  padding: 1.1rem 1.5rem 1.25rem;
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  position: relative;
}
.metric:last-child { border-right: none; }
.metric__value {
  font-family: var(--font-serif);
  font-weight: 500;
  font-size: 1.85rem;
  line-height: 1;
  letter-spacing: -0.02em;
  color: var(--color-text);
}
.metric__sub {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.metric__bar {
  margin-top: auto;
  height: 3px;
  background: var(--color-surface);
  position: relative;
  overflow: hidden;
}
.metric__bar-fill {
  height: 100%;
  transition: width var(--duration-base) var(--ease-out), background var(--duration-base) var(--ease-out);
}

@media (max-width: 900px) {
  .hero__metrics { grid-template-columns: repeat(2, 1fr); }
  .metric { border-bottom: 1px solid var(--color-border-subtle); }
  .metric:nth-child(2n) { border-right: none; }
}

/* flip transition */
.flip-enter-active, .flip-leave-active { transition: all 280ms var(--ease-out); }
.flip-enter-from { opacity: 0; transform: translateY(12px); }
.flip-leave-to   { opacity: 0; transform: translateY(-12px); }
</style>
