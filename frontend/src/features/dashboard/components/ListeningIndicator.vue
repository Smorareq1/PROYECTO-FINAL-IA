<script setup lang="ts">
import { computed } from 'vue'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import { storeToRefs } from 'pinia'

const { wsConnected, arduinoConnected, modelsLoaded, pipelineRunning } = storeToRefs(useSystemStore())

const status = computed(() => {
  if (!wsConnected.value) return { label: 'Desconectado', tone: 'off' as const, hint: 'WebSocket caido' }
  if (!modelsLoaded.value) return { label: 'Cargando modelos', tone: 'wait' as const, hint: 'CNN + LSTM' }
  if (!arduinoConnected.value) return { label: 'Sin Arduino', tone: 'wait' as const, hint: 'Esperando puerto serial' }
  return { label: 'Escuchando', tone: 'live' as const, hint: 'Microfono activo' }
})
</script>

<template>
  <article class="listen" :class="`listen--${status.tone}`">
    <header class="listen__head">
      <span class="eyebrow">Estado del sistema</span>
    </header>

    <div class="listen__body">
      <div class="listen__viz" aria-hidden="true">
        <span v-for="i in 5" :key="i" class="listen__bar" :style="{ animationDelay: `${i * 80}ms` }" />
      </div>
      <div class="listen__text">
        <h3 class="listen__title">{{ status.label }}</h3>
        <p class="listen__hint">{{ status.hint }}</p>
      </div>
    </div>

    <footer class="listen__foot">
      <div class="listen__row">
        <span class="listen__row-label">Pipeline</span>
        <span class="listen__row-val" :class="pipelineRunning ? 'is-on' : 'is-off'">
          {{ pipelineRunning ? 'Activo' : 'Detenido' }}
        </span>
      </div>
      <div class="listen__row">
        <span class="listen__row-label">Modelos</span>
        <span class="listen__row-val" :class="modelsLoaded ? 'is-on' : 'is-off'">
          {{ modelsLoaded ? 'Listos' : 'Cargando' }}
        </span>
      </div>
      <div class="listen__row">
        <span class="listen__row-label">Arduino</span>
        <span class="listen__row-val" :class="arduinoConnected ? 'is-on' : 'is-off'">
          {{ arduinoConnected ? 'Conectado' : 'Sin enlace' }}
        </span>
      </div>
    </footer>
  </article>
</template>

<style scoped>
.listen {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
}
.listen__head {
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid var(--color-border-subtle);
}

.listen__body {
  padding: 1.5rem 1.25rem 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.1rem;
}

.listen__viz {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 6px;
  height: 56px;
  width: 100%;
}
.listen__bar {
  width: 8px;
  height: 100%;
  background: var(--color-text-muted);
  transform-origin: bottom;
  transform: scaleY(0.2);
  transition: background var(--duration-base) var(--ease-out);
}
.listen--live .listen__bar {
  background: var(--color-success);
  animation: wave 1.1s ease-in-out infinite;
}
.listen--wait .listen__bar { background: var(--color-warning); }
.listen--off .listen__bar  { background: var(--color-danger); opacity: 0.6; }

@keyframes wave {
  0%, 100% { transform: scaleY(0.25); }
  50%      { transform: scaleY(1); }
}

.listen__text { text-align: center; }
.listen__title {
  font-family: var(--font-serif);
  font-size: 1.5rem;
  letter-spacing: -0.02em;
  font-weight: 500;
}
.listen--live .listen__title { color: var(--color-success); }
.listen--wait .listen__title { color: var(--color-warning); }
.listen--off  .listen__title { color: var(--color-danger); }
.listen__hint {
  margin-top: 0.25rem;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.listen__foot {
  border-top: 1px solid var(--color-border-subtle);
  padding: 0.75rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.listen__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.listen__row-label { color: var(--color-text-muted); }
.listen__row-val   { color: var(--color-text); font-weight: 500; }
.listen__row-val.is-on  { color: var(--color-success); }
.listen__row-val.is-off { color: var(--color-danger); }
</style>
