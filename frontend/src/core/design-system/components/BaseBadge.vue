<script setup lang="ts">
defineProps<{
  active?: boolean
  label?: string
  tone?: 'success' | 'danger' | 'warning' | 'info' | 'neutral'
}>()
</script>

<template>
  <div class="badge" :class="`badge--${tone ?? (active === undefined ? 'neutral' : (active ? 'success' : 'danger'))}`">
    <span class="badge__dot" :class="{ 'badge__dot--pulse': active }" />
    <span v-if="label" class="badge__label">{{ label }}</span>
    <slot />
  </div>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-text-secondary);
}
.badge__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--color-text-muted);
  position: relative;
}
.badge__dot--pulse::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 1px solid currentColor;
  opacity: 0.5;
  animation: ping 1.6s ease-out infinite;
}
@keyframes ping {
  0%   { transform: scale(0.8); opacity: 0.6; }
  100% { transform: scale(1.8); opacity: 0; }
}

.badge--success .badge__dot { background: var(--color-success); }
.badge--success            { color: var(--color-success); }

.badge--danger .badge__dot { background: var(--color-danger); }
.badge--danger             { color: var(--color-danger); }

.badge--warning .badge__dot { background: var(--color-warning); }
.badge--warning             { color: var(--color-warning); }

.badge--info .badge__dot { background: var(--color-info); }
.badge--info             { color: var(--color-info); }
</style>
