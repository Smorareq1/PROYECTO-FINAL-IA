<script setup lang="ts">
import BaseBadge from '@core/design-system/components/BaseBadge.vue'
import { useSystemStore } from '@features/system/stores/useSystemStore'
import { storeToRefs } from 'pinia'

const { arduinoConnected, modelsLoaded, wsConnected } = storeToRefs(useSystemStore())
</script>

<template>
  <header class="app-header">
    <h1 class="app-header__title">Asistente Robotico por Comandos de Voz</h1>
    <div class="app-header__status">
      <BaseBadge :active="wsConnected" label="WebSocket" />
      <BaseBadge :active="arduinoConnected" label="Arduino" />
      <BaseBadge :active="modelsLoaded" label="Modelos" />
    </div>
  </header>
</template>

<style scoped>
.app-header {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-bottom: 1px solid var(--color-border, #334155);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.app-header__title {
  font-size: 1.5rem;
  font-weight: 600;
  background: linear-gradient(90deg, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.app-header__status {
  display: flex;
  gap: 1.5rem;
}
</style>
