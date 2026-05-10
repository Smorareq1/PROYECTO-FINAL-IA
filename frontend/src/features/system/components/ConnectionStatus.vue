<script setup lang="ts">
import BaseCard from '@core/design-system/components/BaseCard.vue'
import BaseBadge from '@core/design-system/components/BaseBadge.vue'
import { useSystemStore } from '../stores/useSystemStore'
import { storeToRefs } from 'pinia'

const { arduinoConnected, modelsLoaded, pipelineRunning } = storeToRefs(useSystemStore())
</script>

<template>
  <BaseCard title="Estado del Sistema">
    <div class="status-list">
      <BaseBadge :active="arduinoConnected" label="Arduino conectado" />
      <BaseBadge :active="modelsLoaded" label="Modelos cargados" />
      <BaseBadge :active="pipelineRunning" label="Pipeline activo" />
    </div>
  </BaseCard>
</template>

<style scoped>
.status-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
</style>
