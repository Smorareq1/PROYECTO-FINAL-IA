<script setup lang="ts">
import BaseCard from '@core/design-system/components/BaseCard.vue'
import { useSystemStore } from '../stores/useSystemStore'
import { storeToRefs } from 'pinia'

const { arduinoConnected, modelsLoaded, pipelineRunning, cnnModel, lstmModel, uptimeSeconds } = storeToRefs(useSystemStore())

function formatUptime(s: number): string {
  if (!s) return '00:00:00'
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = Math.floor(s % 60)
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`
}
</script>

<template>
  <BaseCard eyebrow="Infraestructura" title="Estado del sistema">
    <ul class="rows">
      <li>
        <span class="rows__k">Arduino</span>
        <span class="rows__v" :class="arduinoConnected ? 'is-on' : 'is-off'">
          {{ arduinoConnected ? 'Conectado' : 'Desconectado' }}
        </span>
      </li>
      <li>
        <span class="rows__k">Modelos</span>
        <span class="rows__v" :class="modelsLoaded ? 'is-on' : 'is-off'">
          {{ modelsLoaded ? 'Cargados' : 'No cargados' }}
        </span>
      </li>
      <li>
        <span class="rows__k">Pipeline</span>
        <span class="rows__v" :class="pipelineRunning ? 'is-on' : 'is-off'">
          {{ pipelineRunning ? 'Activo' : 'Detenido' }}
        </span>
      </li>
      <li>
        <span class="rows__k">CNN</span>
        <span class="rows__v rows__v--mono">{{ cnnModel || '—' }}</span>
      </li>
      <li>
        <span class="rows__k">LSTM</span>
        <span class="rows__v rows__v--mono">{{ lstmModel || '—' }}</span>
      </li>
      <li>
        <span class="rows__k">Uptime</span>
        <span class="rows__v rows__v--mono tnum">{{ formatUptime(uptimeSeconds) }}</span>
      </li>
    </ul>
  </BaseCard>
</template>

<style scoped>
.rows { list-style: none; display: flex; flex-direction: column; }
.rows li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.55rem 0;
  border-bottom: 1px dashed var(--color-border);
  font-family: var(--font-mono);
  font-size: 0.75rem;
}
.rows li:last-child { border-bottom: none; }
.rows__k { color: var(--color-text-muted); letter-spacing: 0.1em; text-transform: uppercase; font-size: 0.65rem; }
.rows__v { color: var(--color-text); font-weight: 500; }
.rows__v--mono { font-size: 0.72rem; color: var(--color-text-secondary); }
.rows__v.is-on  { color: var(--color-success); }
.rows__v.is-off { color: var(--color-danger); }
</style>
