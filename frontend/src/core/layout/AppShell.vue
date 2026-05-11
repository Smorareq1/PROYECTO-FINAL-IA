<script setup lang="ts">
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="shell">
    <AppHeader />
    <main class="shell__main">
      <RouterView />
    </main>
    <footer class="shell__footer">
      <span class="eyebrow">Asistente Robotico v1.0</span>
      <span class="eyebrow shell__footer-meta">Voice Command Lab &middot; Universidad Rafael Landivar</span>
    </footer>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  display: grid;
  grid-template-rows: auto 1fr auto;
  background: var(--color-bg);
  color: var(--color-text);
}

.shell__main {
  width: 100%;
  max-width: 1680px;
  margin: 0 auto;
  padding: 1.5rem 2.5rem 2.5rem;
}

.shell__footer {
  border-top: 1px solid var(--color-border);
  padding: 1rem 2.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1680px;
  width: 100%;
  margin: 0 auto;
}

.shell__footer-meta { color: var(--color-text-secondary); }

@media (max-width: 1024px) {
  .shell__main, .shell__footer { padding-left: 1.25rem; padding-right: 1.25rem; }
}
</style>
