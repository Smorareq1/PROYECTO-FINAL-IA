<script setup lang="ts">
import AppHeader from './AppHeader.vue'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-shell__main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg, #0f172a);
  color: var(--color-text, #f1f5f9);
}
.app-shell__main {
  flex: 1;
  padding: 1.5rem 2rem;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}
</style>
