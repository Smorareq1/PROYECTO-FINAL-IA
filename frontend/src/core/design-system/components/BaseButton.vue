<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
}>()
</script>

<template>
  <button
    class="base-btn"
    :class="[`base-btn--${variant ?? 'primary'}`, `base-btn--${size ?? 'md'}`]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.base-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  border-radius: var(--radius-md, 8px);
  font-weight: 500;
  cursor: pointer;
  transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--color-border, #334155);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.base-btn:active { transform: scale(0.95); }
.base-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.base-btn--sm { padding: 0.4rem 0.75rem; font-size: 0.75rem; }
.base-btn--md { padding: 0.6rem 1rem; font-size: 0.8rem; }
.base-btn--lg { padding: 0.8rem 1.5rem; font-size: 0.9rem; }

.base-btn--primary {
  background: var(--color-card-hover, #334155);
  color: var(--color-text, #f1f5f9);
}
.base-btn--primary:hover:not(:disabled) {
  border-color: var(--color-accent, #38bdf8);
  background: rgba(56, 189, 248, 0.1);
}

.base-btn--ghost {
  background: transparent;
  color: var(--color-text-secondary, #94a3b8);
}
.base-btn--ghost:hover:not(:disabled) {
  color: var(--color-text, #f1f5f9);
  background: rgba(255, 255, 255, 0.05);
}

.base-btn--danger {
  background: var(--color-card-hover, #334155);
  color: #f87171;
  border-color: rgba(248, 113, 113, 0.3);
}
.base-btn--danger:hover:not(:disabled) {
  background: rgba(248, 113, 113, 0.1);
  border-color: #f87171;
}
</style>
