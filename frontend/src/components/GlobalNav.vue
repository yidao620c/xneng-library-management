<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const avatarText = computed(() => auth.user?.nickname?.[0] ?? auth.user?.username?.[0] ?? '读')

function onCommand(cmd: string) {
  if (cmd === 'logout') {
    auth.logout()
    ElMessage.success('已退出登录')
    router.push({ name: 'login' })
  } else {
    router.push({ name: cmd })
  }
}
</script>

<template>
  <header class="global-nav">
    <div class="inner">
      <router-link :to="{ name: 'home' }" class="brand">
        <el-icon :size="16"><Notebook /></el-icon>
        图书管理系统
      </router-link>
      <nav class="nav-links">
        <router-link :to="{ name: 'home' }" class="nav-link">图书检索</router-link>
        <router-link :to="{ name: 'my-borrows' }" class="nav-link">我的借阅</router-link>
        <router-link :to="{ name: 'messages' }" class="nav-link">
          <el-badge :value="auth.unreadCount" :hidden="!auth.isLoggedIn || auth.unreadCount === 0" :max="99">
            消息中心
          </el-badge>
        </router-link>
        <router-link :to="{ name: 'profile' }" class="nav-link">个人中心</router-link>
      </nav>
      <template v-if="auth.isLoggedIn">
        <router-link
          v-if="auth.isAdmin"
          :to="{ name: 'admin-dashboard' }"
          class="nav-link"
          style="margin-right: 8px"
        >
          管理后台
        </router-link>
        <el-dropdown @command="onCommand">
          <span style="display: inline-flex; align-items: center; gap: 8px; cursor: pointer; outline: none">
            <el-avatar :size="28" :src="auth.user?.avatar ?? undefined" style="background: #0066cc">
              {{ avatarText }}
            </el-avatar>
            <span class="nav-link" style="color: #fff">{{ auth.user?.nickname || auth.user?.username }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人中心</el-dropdown-item>
              <el-dropdown-item command="my-borrows">我的借阅</el-dropdown-item>
              <el-dropdown-item command="messages">消息中心</el-dropdown-item>
              <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
      <template v-else>
        <router-link :to="{ name: 'login' }" class="nav-link">登录</router-link>
        <router-link :to="{ name: 'register' }" class="nav-link">注册</router-link>
      </template>
    </div>
  </header>
</template>
