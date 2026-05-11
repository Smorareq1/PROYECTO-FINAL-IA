<script setup lang="ts">
import type { CommandMeta } from '@core/types/commands'
import { colors } from '@core/design-system/tokens'
import type { CommandColor } from '@core/design-system/tokens'

const props = defineProps<{
  meta: CommandMeta
  loading?: boolean
}>()

const emit = defineEmits<{
  press: [cmd: string]
}>()

const color = colors.command[props.meta.name as CommandColor] ?? colors.text.primary
const byteHex = `0x${props.meta.byte.toString(16).padStart(2, '0').toUpperCase()}`
</script>

<template>
  <button
    class="cmd"
    :class="{ 'cmd--compound': meta.type === 'compound', 'cmd--loading': loading }"
    :style="{ '--cmd-color': color }"
    :disabled="loading"
    @click="emit('press', meta.name)"
  >
    <span class="cmd__chip" />
    <span class="cmd__label">{{ meta.label }}</span>
    <span class="cmd__byte tnum">{{ byteHex }}</span>
  </button>
</template>

<style scoped>
.cmd {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.55rem;
  padding: 0.7rem 0.85rem;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  text-align: left;
  cursor: pointer;
  transition:
    border-color var(--duration-fast) var(--ease-out),
    background var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-snap);
  overflow: hidden;
}
.cmd::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--cmd-color);
  opacity: 0;
  transition: opacity var(--duration-fast) var(--ease-out);
  z-index: 0;
}
.cmd:hover { border-color: var(--cmd-color); }
.cmd:hover::before { opacity: 0.06; }
.cmd:active { transform: translateY(1px); }
.cmd:disabled { cursor: not-allowed; opacity: 0.6; }

.cmd__chip {
  width: 8px;
  height: 22px;
  background: var(--cmd-color);
  border-radius: 1px;
  position: relative;
  z-index: 1;
}

.cmd__label {
  position: relative;
  z-index: 1;
  font-family: var(--font-serif);
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--color-text);
  text-transform: capitalize;
}

.cmd__byte {
  position: relative;
  z-index: 1;
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
}
.cmd:hover .cmd__byte { color: var(--cmd-color); }

.cmd--compound { border-style: dashed; }
</style>
