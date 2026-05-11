<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  block?: boolean
}>()
</script>

<template>
  <button
    class="btn"
    :class="[
      `btn--${variant ?? 'primary'}`,
      `btn--${size ?? 'md'}`,
      block ? 'btn--block' : '',
    ]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-family: var(--font-mono);
  font-weight: 500;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    background var(--duration-fast) var(--ease-out),
    color var(--duration-fast) var(--ease-out),
    border-color var(--duration-fast) var(--ease-out),
    transform var(--duration-fast) var(--ease-snap);
}
.btn:active:not(:disabled) { transform: translateY(1px); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.btn--block { width: 100%; }

.btn--sm { padding: 0.45rem 0.85rem; font-size: 0.7rem; }
.btn--md { padding: 0.6rem 1.1rem;  font-size: 0.75rem; }
.btn--lg { padding: 0.85rem 1.5rem; font-size: 0.8rem; }

.btn--primary {
  background: var(--color-inverse);
  color: var(--color-text-on-inverse);
  border-color: var(--color-inverse);
}
.btn--primary:hover:not(:disabled) {
  background: var(--color-accent);
  border-color: var(--color-accent);
}

.btn--outline {
  background: transparent;
  color: var(--color-text);
  border-color: var(--color-border-strong);
}
.btn--outline:hover:not(:disabled) {
  background: var(--color-inverse);
  color: var(--color-text-on-inverse);
}

.btn--ghost {
  background: transparent;
  color: var(--color-text-secondary);
}
.btn--ghost:hover:not(:disabled) {
  background: var(--color-surface);
  color: var(--color-text);
}

.btn--danger {
  background: var(--color-bg);
  color: var(--color-danger);
  border-color: var(--color-danger);
}
.btn--danger:hover:not(:disabled) {
  background: var(--color-danger);
  color: var(--color-bg);
}
</style>
