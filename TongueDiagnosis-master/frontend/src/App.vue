<script setup>
import { RouterView } from 'vue-router'
import Header from '@/components/Header.vue'
import { onMounted } from 'vue'
import { useStateStore } from '@/stores/stateStore'

const stateStore = useStateStore()

onMounted(() => {
  document.documentElement.setAttribute('data-theme', stateStore.theme)
})
</script>
<template>
  <div class="app-container">
    <Header></Header>
    <main class="main-content">
      <router-view></router-view>
    </main>
  </div>
</template>

<style>
@import '@/assets/theme.css';

#app {
  padding: 0;
  margin: 0;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--bg-primary);
}

.main-content {
  padding-top: 72px;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.main-content > * {
  min-height: calc(100vh - 72px);
}
</style>
