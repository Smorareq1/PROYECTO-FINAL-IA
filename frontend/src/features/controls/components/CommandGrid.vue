<script setup lang="ts">
import BaseCard from '@core/design-system/components/BaseCard.vue'
import CommandButton from './CommandButton.vue'
import { COMMAND_META } from '@core/types/commands'
import type { Command, CommandMeta } from '@core/types/commands'
import { useControlsStore } from '../stores/useControlsStore'
import { storeToRefs } from 'pinia'

const controlsStore = useControlsStore()
const { sending, lastSent, error } = storeToRefs(controlsStore)

const simpleCommands   = COMMAND_META.filter((c: CommandMeta) => c.type === 'simple')
const compoundCommands = COMMAND_META.filter((c: CommandMeta) => c.type === 'compound')

function handlePress(cmd: string) {
  controlsStore.sendCommand(cmd as Command)
}
</script>

<template>
  <BaseCard eyebrow="Override" title="Controles manuales">
    <template #actions>
      <span v-if="sending" class="grid__hint">Enviando&hellip;</span>
      <span v-else-if="error" class="grid__hint grid__hint--err">Error: {{ error }}</span>
      <span v-else-if="lastSent" class="grid__hint">Ultimo: <strong>{{ lastSent }}</strong></span>
    </template>

    <div class="group">
      <span class="eyebrow group__title">Simples &middot; 1 byte</span>
      <div class="grid">
        <CommandButton
          v-for="cmd in simpleCommands"
          :key="cmd.name"
          :meta="cmd"
          :loading="sending"
          @press="handlePress"
        />
      </div>
    </div>

    <div class="group group--compound">
      <span class="eyebrow group__title">Compuestos &middot; secuencias</span>
      <div class="grid">
        <CommandButton
          v-for="cmd in compoundCommands"
          :key="cmd.name"
          :meta="cmd"
          :loading="sending"
          @press="handlePress"
        />
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.group { display: flex; flex-direction: column; gap: 0.55rem; }
.group--compound {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border-subtle);
}
.group__title { padding: 0 0.1rem; }

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.45rem;
}

.grid__hint {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.grid__hint strong { color: var(--color-text); font-weight: 500; }
.grid__hint--err   { color: var(--color-danger); }
</style>
