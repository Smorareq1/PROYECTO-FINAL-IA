<script setup lang="ts">
defineProps<{
  title?: string
  padding?: 'sm' | 'md' | 'lg'
}>()
</script>

<template>
  <div class="base-card" :class="`base-card--${padding ?? 'md'}`">
    <h2 v-if="title" class="base-card__title">{{ title }}</h2>
    <slot />
  </div>
</template>

<style scoped>
.base-card {
  background: var(--color-card, #1e293b);
  border: 1px solid var(--color-border, #334155);
  border-radius: var(--radius-lg, 12px);
}
.base-card--sm { padding: 0.75rem; }
.base-card--md { padding: 1.25rem; }
.base-card--lg { padding: 2rem; }

.base-card__title {
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary, #94a3b8);
  margin-bottom: 1rem;
  font-weight: 600;
}
</style>
