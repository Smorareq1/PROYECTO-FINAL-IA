<script setup lang="ts">
defineProps<{
  title?: string
  eyebrow?: string
  padding?: 'sm' | 'md' | 'lg' | 'none'
  variant?: 'default' | 'inverse' | 'plain'
  bordered?: boolean
}>()
</script>

<template>
  <section
    class="card"
    :class="[
      `card--${padding ?? 'md'}`,
      `card--${variant ?? 'default'}`,
      bordered === false ? 'card--no-border' : '',
    ]"
  >
    <header v-if="eyebrow || title" class="card__head">
      <span v-if="eyebrow" class="eyebrow card__eyebrow">{{ eyebrow }}</span>
      <h2 v-if="title" class="card__title">{{ title }}</h2>
      <slot name="actions" />
    </header>
    <div class="card__body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.card--no-border { border-color: transparent; }

.card--inverse {
  background: var(--color-inverse);
  color: var(--color-text-on-inverse);
  border-color: var(--color-inverse);
}
.card--inverse :deep(.card__title)   { color: var(--color-text-on-inverse); }
.card--inverse :deep(.card__eyebrow) { color: rgba(250, 250, 250, 0.55); }

.card--plain {
  background: transparent;
  border-color: transparent;
}

.card--none .card__body { padding: 0; }
.card--sm   .card__body { padding: 1rem; }
.card--md   .card__body { padding: 1.25rem 1.5rem; }
.card--lg   .card__body { padding: 2rem 2.25rem; }

.card__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border-subtle);
}
.card--lg .card__head { padding: 1.25rem 2.25rem; }
.card--sm .card__head { padding: 0.75rem 1rem; }

.card__eyebrow { display: block; }

.card__title {
  font-family: var(--font-serif);
  font-size: 1.05rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  color: var(--color-text);
  margin-top: 0.15rem;
}

.card__body { flex: 1; }
</style>
