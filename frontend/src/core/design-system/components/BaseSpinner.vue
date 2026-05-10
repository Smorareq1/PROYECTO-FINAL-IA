<script setup lang="ts">
defineProps<{
  size?: 'sm' | 'md' | 'lg'
}>()
</script>

<template>
  <div class="base-spinner" :class="`base-spinner--${size ?? 'md'}`" />
</template>

<style scoped>
.base-spinner {
  border: 2px solid var(--color-border, #334155);
  border-top-color: var(--color-accent, #38bdf8);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.base-spinner--sm { width: 16px; height: 16px; }
.base-spinner--md { width: 24px; height: 24px; }
.base-spinner--lg { width: 40px; height: 40px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
