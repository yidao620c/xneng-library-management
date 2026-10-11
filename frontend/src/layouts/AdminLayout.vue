<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import GlobalNav from '../components/GlobalNav.vue'
import { useAuthStore } from '../stores/auth'
import { ROLE_TEXT } from '../utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div>
    <GlobalNav />
    <div class="admin-layout">
      <aside class="admin-side">
        <router-link :to="{ name: 'admin-dashboard' }">仪表盘</router-link>
        <router-link :to="{ name: 'admin-books' }">图书管理</router-link>
        <router-link :to="{ name: 'admin-categories' }">分类管理</router-link>
        <router-link :to="{ name: 'admin-borrows' }">借阅管理</router-link>
        <router-link :to="{ name: 'admin-users' }">用户管理</router-link>
        <router-link :to="{ name: 'admin-messages' }">消息发布</router-link>
      </aside>
      <main class="admin-main">
        <div class="toolbar" style="margin-bottom: 16px">
          <h2>{{ route.meta.title }}</h2>
          <div class="grow"></div>
          <span class="t-caption t-muted">{{ auth.user?.nickname }}（{{ ROLE_TEXT[auth.user?.role ?? 'user'] }}）</span>
        </div>
        <router-view />
      </main>
    </div>
  </div>
</template>
