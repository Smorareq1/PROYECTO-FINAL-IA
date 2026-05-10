<script setup lang="ts">
import type { CommandMeta } from '@core/types/commands'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'

const props = defineProps<{
  meta: CommandMeta
}>()

const emit = defineEmits<{
  press: [cmd: string]
}>()

const color = colors.command[props.meta.name as CommandColor] ?? colors.accent.default
</script>

<template>
  <button
    class="cmd-btn"
    :class="{ 'cmd-btn--compound': meta.type === 'compound' }"
    :style="{ '--cmd-color': color }"
    @click="emit('press', meta.name)"
  >
    {{ meta.label }}
  </button>
</template>

<style scoped>
.cmd-btn {
  padding: 0.7rem 0.5rem;
  border: 1px solid var(--color-border, #334155);
  border-radius: 8px;
  background: var(--color-card-hover, #334155);
  color: var(--color-text, #f1f5f9);
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  transition: all 200ms;
}
.cmd-btn:hover {
  border-color: var(--cmd-color);
  background: color-mix(in srgb, var(--cmd-color) 10%, transparent);
}
.cmd-btn:active {
  transform: scale(0.95);
}
.cmd-btn--compound {
  border-color: rgba(129, 140, 248, 0.3);
}
</style>
