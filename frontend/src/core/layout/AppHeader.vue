<script setup lang="ts">
import { computed } from 'vue'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import { storeToRefs } from 'pinia'

const { arduinoConnected, modelsLoaded, wsConnected } = storeToRefs(useSystemStore())

const allOnline = computed(
  () => arduinoConnected.value && modelsLoaded.value && wsConnected.value,
)
const liveLabel = computed(() => (wsConnected.value ? 'Live' : 'Offline'))
</script>

<template>
  <header class="hdr">
    <div class="hdr__inner">
      <div class="hdr__brand">
        <div class="hdr__mark" aria-hidden="true">
          <span class="hdr__mark-dot" />
        </div>
        <div class="hdr__brand-text">
          <span class="eyebrow">Issue n&deg;01 &middot; 2026</span>
          <h1 class="hdr__title">
            <span class="hdr__title-serif">Asistente</span>
            <span class="hdr__title-italic">Robotico</span>
          </h1>
        </div>
      </div>

      <div class="hdr__status">
        <div class="hdr__live" :class="{ 'hdr__live--off': !wsConnected }">
          <span class="hdr__live-dot" />
          <span class="hdr__live-label">{{ liveLabel }}</span>
        </div>
        <div class="hdr__pillrow">
          <span class="pill" :class="wsConnected ? 'pill--on' : 'pill--off'">
            <span class="pill__dot" /> WebSocket
          </span>
          <span class="pill" :class="arduinoConnected ? 'pill--on' : 'pill--off'">
            <span class="pill__dot" /> Arduino
          </span>
          <span class="pill" :class="modelsLoaded ? 'pill--on' : 'pill--off'">
            <span class="pill__dot" /> Modelos
          </span>
        </div>
        <div class="hdr__health" :class="{ 'hdr__health--ok': allOnline }">
          {{ allOnline ? 'Sistema operativo' : 'Atencion requerida' }}
        </div>
      </div>
    </div>
    <div class="hdr__rule" />
  </header>
</template>

<style scoped>
.hdr { background: var(--color-bg); }

.hdr__inner {
  max-width: 1680px;
  margin: 0 auto;
  padding: 1.75rem 2.5rem 1rem;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 2rem;
  flex-wrap: wrap;
}

.hdr__brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.hdr__mark {
  width: 56px;
  height: 56px;
  background: var(--color-inverse);
  display: grid;
  place-items: center;
  position: relative;
}
.hdr__mark-dot {
  width: 14px;
  height: 14px;
  background: var(--color-accent);
  border-radius: 50%;
}

.hdr__brand-text { display: flex; flex-direction: column; gap: 0.15rem; }

.hdr__title {
  font-family: var(--font-serif);
  font-size: 2.75rem;
  line-height: 1;
  font-weight: 400;
  letter-spacing: -0.025em;
  color: var(--color-text);
  display: flex;
  gap: 0.6rem;
  align-items: baseline;
}
.hdr__title-italic {
  font-style: italic;
  font-weight: 300;
  color: var(--color-text-secondary);
}

.hdr__status {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.hdr__live {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--color-inverse);
  color: var(--color-text-on-inverse);
  padding: 0.4rem 0.75rem;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.hdr__live--off { background: var(--color-text-muted); }
.hdr__live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-accent);
  animation: blink 1.4s ease-in-out infinite;
}
.hdr__live--off .hdr__live-dot { background: #fafafa; animation: none; opacity: 0.6; }
@keyframes blink {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%      { opacity: 0.3; transform: scale(0.85); }
}

.hdr__pillrow { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.32rem 0.6rem;
  font-family: var(--font-mono);
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text-secondary);
}
.pill__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-muted);
}
.pill--on  .pill__dot { background: var(--color-success); }
.pill--off .pill__dot { background: var(--color-danger); }
.pill--on  { color: var(--color-text); border-color: var(--color-text); }

.hdr__health {
  font-family: var(--font-serif);
  font-style: italic;
  font-size: 0.95rem;
  color: var(--color-text-muted);
  border-left: 1px solid var(--color-border);
  padding-left: 1rem;
}
.hdr__health--ok { color: var(--color-success); }

.hdr__rule {
  height: 1px;
  background: var(--color-border-strong);
  max-width: 1680px;
  margin: 0 auto;
  margin-left: auto;
  margin-right: auto;
}
</style>
