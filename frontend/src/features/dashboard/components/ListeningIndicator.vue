<script setup lang="ts">
import { computed } from 'vue'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import { storeToRefs } from 'pinia'

const { wsConnected } = storeToRefs(useSystemStore())

const ledClass = computed(() => wsConnected.value ? 'led--active' : '')
const label = computed(() => wsConnected.value ? 'Escuchando' : 'Desconectado')
</script>

<template>
  <div class="indicator">
    <div class="led" :class="ledClass" />
    <span class="label">{{ label }}</span>
  </div>
</template>

<style scoped>
.indicator { display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }
.led {
  width: 60px; height: 60px;
  border-radius: 50%;
  background: var(--color-danger, #f87171);
  transition: all 300ms;
}
.led--active {
  background: var(--color-success, #4ade80);
  box-shadow: 0 0 30px rgba(74, 222, 128, 0.5);
}
.label {
  font-size: 0.85rem;
  color: var(--color-text-secondary, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
</style>
