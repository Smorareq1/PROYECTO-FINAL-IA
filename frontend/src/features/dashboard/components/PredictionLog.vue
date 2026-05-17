<script setup lang="ts">
import { computed, ref } from 'vue'
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { useDashboardStore } from '../stores/useDashboardStore'
import { storeToRefs } from 'pinia'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'
import { formatConfidence, formatLatency, formatCommandLabel } from '@core/utils/formatters'

const { log } = storeToRefs(useDashboardStore())

const filter = ref<'all' | 'accepted' | 'rejected' | 'manual' | 'system'>('all')

const visibleLog = computed(() => {
  const items = log.value
  if (filter.value === 'all')      return items
  if (filter.value === 'system')   return items.filter(e => e.kind === 'system')
  if (filter.value === 'accepted') return items.filter(e => e.kind === 'prediction' && !e.rejected)
  if (filter.value === 'rejected') return items.filter(e => e.kind === 'prediction' &&  e.rejected)
  if (filter.value === 'manual')   return items.filter(e => e.kind === 'prediction' &&  e.manual)
  return items
})

function commandColor(cmd: string, rejected: boolean): string {
  if (rejected) return colors.danger.default
  return colors.command[cmd as CommandColor] ?? colors.text.secondary
}

const SYSTEM_EVENT_LABEL: Record<string, string> = {
  mic_start: 'Mic ON',
  mic_stop: 'Mic OFF',
  mic_chunks: 'Front → audio',
  audio_ws_open: 'WS audio ↑',
  audio_ws_close: 'WS audio ↓',
  audio_recv: 'Back ← audio',
  vad_trigger: 'VAD disparó',
  error: 'Error',
}

function systemDotClass(ev: string): string {
  if (ev === 'vad_trigger') return 'is-vad'
  if (ev === 'error' || ev.endsWith('_close')) return 'is-bad'
  if (ev === 'mic_chunks' || ev === 'audio_recv') return 'is-flow'
  return 'is-ok'
}
</script>

<template>
  <BaseCard eyebrow="Bitacora" title="Eventos y predicciones" padding="none">
    <template #actions>
      <div class="filters" role="tablist">
        <button
          v-for="opt in (['all','accepted','rejected','manual','system'] as const)"
          :key="opt"
          class="filters__btn"
          :class="{ 'filters__btn--active': filter === opt }"
          @click="filter = opt"
        >
          {{
            opt === 'all' ? 'Todos'
            : opt === 'accepted' ? 'Aceptados'
            : opt === 'rejected' ? 'Rechazados'
            : opt === 'manual' ? 'Manuales'
            : 'Sistema'
          }}
        </button>
      </div>
    </template>

    <div class="log">
      <div class="log__head">
        <span>Hora</span>
        <span>Evento</span>
        <span>Confianza</span>
        <span>Latencia</span>
        <span>Origen</span>
      </div>

      <div class="log__scroll">
        <template v-for="(entry, i) in visibleLog" :key="i">
          <div
            v-if="entry.kind === 'prediction'"
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

          <div v-else class="log__row log__row--system">
            <span class="log__time tnum">{{ entry.timestamp }}</span>
            <span class="log__sys">
              <span class="log__cmd-chip" :class="`dot--${systemDotClass(entry.event)}`" />
              <span class="log__sys-tag">{{ SYSTEM_EVENT_LABEL[entry.event] ?? entry.event }}</span>
              <span class="log__sys-msg">{{ entry.message }}</span>
            </span>
            <span class="log__conf log__sys-dim">—</span>
            <span class="log__lat log__sys-dim">—</span>
            <span class="log__status">
              <span class="log__origin-pill" :class="`origin--${entry.origin}`">
                {{ entry.origin === 'front' ? 'FRONT' : 'BACK' }}
              </span>
            </span>
          </div>
        </template>

        <div v-if="visibleLog.length === 0" class="log__empty">
          <span class="eyebrow">Sin registros</span>
          <p>Aun no hay eventos para este filtro.</p>
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

.log__row--system { color: var(--color-text-secondary); }
.log__sys {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}
.log__sys-tag {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text);
  white-space: nowrap;
}
.log__sys-msg {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  color: var(--color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.log__sys-dim { color: var(--color-text-muted); opacity: 0.5; }

.log__cmd-chip.dot--is-ok   { background: var(--color-success); }
.log__cmd-chip.dot--is-bad  { background: var(--color-danger); }
.log__cmd-chip.dot--is-vad  { background: var(--color-info, #4f8cff); }
.log__cmd-chip.dot--is-flow { background: var(--color-text-muted); }

.log__origin-pill {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  letter-spacing: 0.16em;
  padding: 0.1rem 0.4rem;
  border-radius: 2px;
  border: 1px solid var(--color-border);
}
.log__origin-pill.origin--front {
  color: var(--color-info, #4f8cff);
  border-color: var(--color-info, #4f8cff);
}
.log__origin-pill.origin--back {
  color: var(--color-success);
  border-color: var(--color-success);
}

.log__empty {
  padding: 3rem 1.5rem;
  text-align: center;
  color: var(--color-text-muted);
}
.log__empty p { margin-top: 0.5rem; font-family: var(--font-serif); font-style: italic; }
</style>
