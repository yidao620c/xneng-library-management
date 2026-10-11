<script setup lang="ts">
import { onMounted } from 'vue'
import GlobalNav from '../components/GlobalNav.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
onMounted(() => {
  auth.fetchUnread()
})
</script>

<template>
  <div>
    <GlobalNav />
    <main>
      <router-view />
    </main>
    <footer class="site-footer">
      <div class="inner">
        <div class="t-caption">图书管理系统 — 前后端分离演示项目（Vue 3 · FastAPI）</div>
        <div class="legal">本地测试环境 · © 2026 图书管理系统</div>
      </div>
    </footer>
  </div>
</template>
