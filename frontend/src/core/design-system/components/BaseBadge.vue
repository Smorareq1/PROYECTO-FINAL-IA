<script setup lang="ts">
defineProps<{
  active?: boolean
  label?: string
}>()
</script>

<template>
  <div class="base-badge">
    <span class="base-badge__dot" :class="{ 'base-badge__dot--active': active }" />
    <span v-if="label" class="base-badge__label">{{ label }}</span>
    <slot />
  </div>
</template>

<style scoped>
.base-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-secondary, #94a3b8);
}
.base-badge__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-danger, #f87171);
  transition: all 300ms;
}
.base-badge__dot--active {
  background: var(--color-success, #4ade80);
  box-shadow: 0 0 8px rgba(74, 222, 128, 0.5);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
