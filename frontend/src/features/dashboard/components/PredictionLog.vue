<script setup lang="ts">
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { useDashboardStore } from '../stores/useDashboardStore'
import { storeToRefs } from 'pinia'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'
import { formatConfidence, formatLatency } from '@core/utils/formatters'

const { log } = storeToRefs(useDashboardStore())

function cmdColor(cmd: string, rejected: boolean): string {
  if (rejected) return colors.danger.default
  return colors.command[cmd as CommandColor] ?? colors.accent.default
}
</script>

<template>
  <BaseCard title="Log de Predicciones">
    <div class="log-scroll">
      <div
        v-for="(entry, i) in log"
        :key="i"
        class="log-entry"
        :class="{ 'log-entry--rejected': entry.rejected }"
      >
        <span class="time">{{ entry.timestamp }}</span>
        <span class="cmd" :style="{ color: cmdColor(entry.command, entry.rejected) }">
          {{ entry.command }}{{ entry.manual ? ' [MANUAL]' : '' }}
        </span>
        <span class="conf">{{ formatConfidence(entry.confidence) }}</span>
        <span class="lat">{{ formatLatency(entry.latency_ms) }}</span>
        <span class="status" :style="{ color: entry.rejected ? colors.danger.default : colors.success.default }">
          {{ entry.rejected ? 'RECHAZADO' : 'OK' }}
        </span>
      </div>
      <div v-if="log.length === 0" class="log-empty">Sin predicciones aun...</div>
    </div>
  </BaseCard>
</template>

<style scoped>
.log-scroll {
  max-height: 220px;
  overflow-y: auto;
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 0.8rem;
  line-height: 1.6;
}
.log-scroll::-webkit-scrollbar { width: 6px; }
.log-scroll::-webkit-scrollbar-track { background: var(--color-bg, #0f172a); }
.log-scroll::-webkit-scrollbar-thumb { background: var(--color-border, #334155); border-radius: 3px; }

.log-entry {
  padding: 0.25rem 0.5rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
  display: flex;
  gap: 1rem;
}
.time { color: var(--color-text-secondary, #94a3b8); white-space: nowrap; }
.cmd { font-weight: 600; min-width: 140px; }
.conf { min-width: 60px; }
.lat { color: var(--color-text-secondary, #94a3b8); min-width: 70px; }

.log-empty { color: var(--color-text-muted, #64748b); text-align: center; padding: 2rem; }
</style>
