<script setup lang="ts">
import BaseCard from '@core/design-system/components/BaseCard.vue'
import CommandButton from './CommandButton.vue'
import { COMMAND_META } from '@core/types/commands'
import type { Command, CommandMeta } from '@core/types/commands'
import { useControlsStore } from '../stores/useControlsStore'

const controlsStore = useControlsStore()

const simpleCommands = COMMAND_META.filter((c: CommandMeta) => c.type === 'simple')
const compoundCommands = COMMAND_META.filter((c: CommandMeta) => c.type === 'compound')

function handlePress(cmd: string) {
  controlsStore.sendCommand(cmd as Command)
}
</script>

<template>
  <BaseCard title="Controles Manuales">
    <div class="cmd-grid">
      <CommandButton
        v-for="cmd in simpleCommands"
        :key="cmd.name"
        :meta="cmd"
        @press="handlePress"
      />
    </div>
    <div class="cmd-grid cmd-grid--compound">
      <CommandButton
        v-for="cmd in compoundCommands"
        :key="cmd.name"
        :meta="cmd"
        @press="handlePress"
      />
    </div>
  </BaseCard>
</template>

<style scoped>
.cmd-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}
.cmd-grid--compound {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--color-border, #334155);
}
</style>
