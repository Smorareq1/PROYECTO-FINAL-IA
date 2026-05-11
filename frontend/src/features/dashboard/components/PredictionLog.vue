<script setup lang="ts">
import { computed, ref } from 'vue'
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { useDashboardStore } from '../stores/useDashboardStore'
import { storeToRefs } from 'pinia'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'
import { formatConfidence, formatLatency, formatCommandLabel } from '@core/utils/formatters'

const { log } = storeToRefs(useDashboardStore())

const filter = ref<'all' | 'accepted' | 'rejected' | 'manual'>('all')

const visibleLog = computed(() => {
  if (filter.value === 'all')      return log.value
  if (filter.value === 'accepted') return log.value.filter(e => !e.rejected)
  if (filter.value === 'rejected') return log.value.filter(e =>  e.rejected)
  if (filter.value === 'manual')   return log.value.filter(e =>  e.manual)
  return log.value
})

function commandColor(cmd: string, rejected: boolean): string {
  if (rejected) return colors.danger.default
  return colors.command[cmd as CommandColor] ?? colors.text.secondary
}
</script>

<template>
  <BaseCard eyebrow="Bitacora" title="Log de predicciones" padding="none">
    <template #actions>
      <div class="filters" role="tablist">
        <button
          v-for="opt in (['all','accepted','rejected','manual'] as const)"
          :key="opt"
          class="filters__btn"
          :class="{ 'filters__btn--active': filter === opt }"
          @click="filter = opt"
        >
          {{ opt === 'all' ? 'Todos' : opt === 'accepted' ? 'Aceptados' : opt === 'rejected' ? 'Rechazados' : 'Manuales' }}
        </button>
      </div>
    </template>

    <div class="log">
      <div class="log__head">
        <span>Hora</span>
        <span>Comando</span>
        <span>Confianza</span>
        <span>Latencia</span>
        <span>Estado</span>
      </div>

      <div class="log__scroll">
        <div
          v-for="(entry, i) in visibleLog"
          :key="i"
          class="log__row"
          :class="{ 'log__row--rejected': entry.rejected, 'log__row--manual': entry.manual }"
        >
          <span class="log__time tnum">{{ entry.timestamp }}</span>
          <span class="log__cmd">
            <span class="log__cmd-chip" :style="{ background: commandColor(entry.command, entry.rejected) }" />
            <span class="log__cmd-label">{{ formatCommandLabel(entry.command) }}</span>
            <span v-if="entry.manual" class="log__tag">Manual</span>
          </span>
          <span class="log__conf tnum">{{ formatConfidence(entry.confidence) }}</span>
          <span class="log__lat tnum">{{ formatLatency(entry.latency_ms) }}</span>
          <span class="log__status">
            <span class="log__status-dot" :class="entry.rejected ? 'is-bad' : 'is-ok'" />
            {{ entry.rejected ? 'Rechazado' : 'OK' }}
          </span>
        </div>

        <div v-if="visibleLog.length === 0" class="log__empty">
          <span class="eyebrow">Sin registros</span>
          <p>Aun no hay predicciones para este filtro.</p>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.filters {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.filters__btn {
  padding: 0.32rem 0.7rem;
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
  background: var(--color-bg);
  border-right: 1px solid var(--color-border);
  transition: all var(--duration-fast) var(--ease-out);
}
.filters__btn:last-child { border-right: none; }
.filters__btn:hover { color: var(--color-text); }
.filters__btn--active {
  background: var(--color-inverse);
  color: var(--color-text-on-inverse);
}

.log { display: flex; flex-direction: column; max-height: 320px; }

.log__head, .log__row {
  display: grid;
  grid-template-columns: 110px 1fr 110px 110px 130px;
  gap: 1rem;
  align-items: center;
  padding: 0.55rem 1.5rem;
  font-family: var(--font-mono);
  font-size: 0.78rem;
}
.log__head {
  font-size: 0.65rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  position: sticky;
  top: 0;
  z-index: 1;
}

.log__scroll { overflow-y: auto; flex: 1; }

.log__row {
  border-bottom: 1px solid var(--color-border-subtle);
  transition: background var(--duration-fast) var(--ease-out);
}
.log__row:hover { background: var(--color-surface); }
.log__row--rejected { color: var(--color-text-muted); }

.log__time { color: var(--color-text-secondary); }
.log__cmd  { display: inline-flex; align-items: center; gap: 0.55rem; }
.log__cmd-chip {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  flex-shrink: 0;
}
.log__cmd-label {
  font-family: var(--font-serif);
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--color-text);
  text-transform: capitalize;
}
.log__row--rejected .log__cmd-label { color: var(--color-text-muted); text-decoration: line-through; }

.log__tag {
  font-size: 0.6rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  padding: 0.1rem 0.35rem;
  background: var(--color-info-soft);
  color: var(--color-info);
  border-radius: 2px;
}

.log__status { display: inline-flex; align-items: center; gap: 0.5rem; color: var(--color-text-secondary); }
.log__status-dot { width: 6px; height: 6px; border-radius: 50%; }
.log__status-dot.is-ok  { background: var(--color-success); }
.log__status-dot.is-bad { background: var(--color-danger); }

.log__empty {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
}
.log__empty p { margin-top: 0.5rem; font-family: var(--font-serif); font-style: italic; }
</style>
