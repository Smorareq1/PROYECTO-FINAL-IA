<script setup lang="ts">
defineProps<{
  size?: 'sm' | 'md' | 'lg'
}>()
</script>

<template>
  <div class="spinner" :class="`spinner--${size ?? 'md'}`" role="status" aria-label="Cargando">
    <div class="spinner__bar" />
    <div class="spinner__bar" />
    <div class="spinner__bar" />
    <div class="spinner__bar" />
  </div>
</template>

<style scoped>
.spinner {
  display: inline-flex;
  gap: 3px;
  align-items: flex-end;
  height: 16px;
}
.spinner--sm { height: 12px; }
.spinner--lg { height: 24px; }

.spinner__bar {
  width: 3px;
  background: var(--color-inverse);
  animation: bounce 1s ease-in-out infinite;
  height: 100%;
}
.spinner__bar:nth-child(2) { animation-delay: 0.12s; }
.spinner__bar:nth-child(3) { animation-delay: 0.24s; }
.spinner__bar:nth-child(4) { animation-delay: 0.36s; }

@keyframes bounce {
  0%, 100% { transform: scaleY(0.4); }
  50%      { transform: scaleY(1); }
}
</style>
