<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '../api'
import { apiError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)

const presets = [
  { label: '管理员', username: 'admin', password: 'admin123' },
  { label: '普通用户', username: 'user', password: 'user123' },
  { label: 'VIP 用户', username: 'vip', password: 'vip123' },
]

function fill(u: string, p: string) {
  form.username = u
  form.password = p
}

async function submit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { data } = await authApi.login(form)
    auth.setSession(data)
    auth.fetchUnread()
    ElMessage.success(`欢迎回来，${data.user.nickname || data.user.username}`)
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch (e) {
    ElMessage.error(apiError(e))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="bg-parchment" style="padding: 64px 0 80px">
    <div class="container-narrow">
      <div style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 48px 40px">
        <h1 class="t-display-md" style="margin: 0 0 8px; text-align: center">登录</h1>
        <p class="t-caption t-muted" style="text-align: center; margin: 0 0 32px">
          欢迎回到图书管理系统
        </p>
        <el-form label-position="top" size="large" @submit.prevent="submit">
          <el-form-item label="用户名">
            <el-input v-model="form.username" placeholder="请输入用户名" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              placeholder="请输入密码"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%; margin-top: 8px"
            :loading="loading"
            @click="submit"
          >
            登录
          </el-button>
        </el-form>
        <div class="t-caption" style="margin-top: 24px; text-align: center">
          还没有账号？
          <router-link :to="{ name: 'register' }">立即注册</router-link>
        </div>
        <el-divider />
        <div class="t-caption t-muted" style="text-align: center; margin-bottom: 12px">
          测试账号（点击快速填入）
        </div>
        <div class="toolbar" style="justify-content: center">
          <span
            v-for="p in presets"
            :key="p.username"
            class="chip"
            style="padding: 8px 14px"
            @click="fill(p.username, p.password)"
          >
            {{ p.label }} · {{ p.username }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>
