<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import { storeToRefs } from 'pinia'
import {
  listDevices,
  startListening,
  stopListening,
  type MicDevice,
} from '../services/listeningService'

const systemStore = useSystemStore()
const { wsConnected, arduinoConnected, modelsLoaded, pipelineRunning, isListening, micDeviceName } =
  storeToRefs(systemStore)

const busy = ref(false)
const localError = ref<string | null>(null)
const devices = ref<MicDevice[]>([])
const selectedDevice = ref<number | null>(null)

const isActive = computed(() => isListening.value)

const status = computed(() => {
  if (!wsConnected.value) return { label: 'Desconectado', tone: 'off' as const, hint: 'WebSocket caido' }
  if (!modelsLoaded.value) return { label: 'Cargando modelos', tone: 'wait' as const, hint: 'CNN listo' }
  if (!arduinoConnected.value) return { label: 'Sin Arduino', tone: 'wait' as const, hint: 'Esperando puerto serial' }
  if (isActive.value)
    return {
      label: 'Escuchando',
      tone: 'live' as const,
      hint: micDeviceName.value ?? 'Microfono activo',
    }
  return { label: 'En pausa', tone: 'idle' as const, hint: 'Selecciona micrófono y presiona el boton' }
})

async function refreshDevices() {
  try {
    const data = await listDevices()
    devices.value = data.devices
    if (selectedDevice.value === null) {
      const def = data.devices.find((d) => d.is_default)
      selectedDevice.value = def?.index ?? data.devices[0]?.index ?? null
    }
  } catch (e: unknown) {
    console.warn('[listening] no se pudo cargar lista de mics:', e)
  }
}

onMounted(() => {
  void refreshDevices()
})

async function toggle() {
  if (busy.value) return
  busy.value = true
  localError.value = null
  try {
    if (isActive.value) {
      console.log('[listening] toggle OFF')
      await stopListening()
      systemStore.isListening = false
      systemStore.micDeviceName = null
    } else {
      console.log('[listening] toggle ON · device=', selectedDevice.value)
      const res = await startListening(selectedDevice.value)
      systemStore.isListening = true
      systemStore.micDevice = res.device
      systemStore.micDeviceName = res.device_name
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'No se pudo cambiar el estado'
    console.error('[listening] toggle falló:', msg)
    localError.value = msg
    try {
      await stopListening()
    } catch {
      // swallow
    }
    systemStore.isListening = false
  } finally {
    busy.value = false
  }
}
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

    <div class="listen__cta">
      <label class="listen__field">
        <span class="listen__field-label">Micrófono</span>
        <select
          v-model="selectedDevice"
          class="listen__select"
          :disabled="busy || isActive"
        >
          <option v-if="devices.length === 0" :value="null">Sin micrófonos detectados</option>
          <option
            v-for="d in devices"
            :key="d.index"
            :value="d.index"
          >
            {{ d.name }}{{ d.is_default ? ' · default' : '' }}
          </option>
        </select>
      </label>

      <button
        type="button"
        class="listen__btn"
        :class="isActive ? 'listen__btn--stop' : 'listen__btn--start'"
        :disabled="busy || !modelsLoaded || (devices.length === 0 && !isActive)"
        @click="toggle"
      >
        <span v-if="busy">...</span>
        <span v-else-if="isActive">Detener escucha</span>
        <span v-else>Comenzar a escuchar</span>
      </button>

      <p v-if="micDeviceName && isActive" class="listen__current">
        En vivo: <strong>{{ micDeviceName }}</strong>
      </p>
      <p v-if="localError" class="listen__err">{{ localError }}</p>
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
.listen--idle .listen__bar { background: var(--color-text-muted); opacity: 0.5; }

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
.listen--idle .listen__title { color: var(--color-text); }
.listen__hint {
  margin-top: 0.25rem;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.listen__cta {
  padding: 0 1.25rem 1rem;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 0.6rem;
}
.listen__field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.listen__field-label {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.listen__select {
  width: 100%;
  padding: 0.55rem 0.7rem;
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  cursor: pointer;
}
.listen__select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.listen__current {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  text-align: center;
  margin: 0;
}
.listen__current strong {
  color: var(--color-success);
  font-weight: 500;
}
.listen__btn {
  width: 100%;
  padding: 0.7rem 1rem;
  border-radius: var(--radius-sm, 6px);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-mono);
  font-size: 0.72rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
}
.listen__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.listen__btn--start:not(:disabled):hover {
  border-color: var(--color-success);
  color: var(--color-success);
}
.listen__btn--stop {
  border-color: var(--color-danger);
  color: var(--color-danger);
}
.listen__btn--stop:not(:disabled):hover {
  background: var(--color-danger);
  color: var(--color-bg);
}
.listen__err {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  color: var(--color-danger);
  text-align: center;
  margin: 0;
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
