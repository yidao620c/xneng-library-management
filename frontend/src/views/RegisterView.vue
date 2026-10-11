<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { authApi } from '../api'
import { apiError } from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const formRef = ref<FormInstance>()
const form = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  password: '',
  confirm: '',
})
const loading = ref(false)

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]{3,50}$/, message: '3-50 位字母、数字或下划线', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 64, message: '密码长度至少 6 位', trigger: 'blur' },
  ],
  confirm: [
    {
      validator: (_r, value: string, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
}

async function submit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const { data } = await authApi.register({
      username: form.username,
      password: form.password,
      nickname: form.nickname,
      email: form.email,
      phone: form.phone,
    })
    auth.setSession(data)
    ElMessage.success('注册成功，已自动登录')
    router.push({ name: 'home' })
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
        <h1 class="t-display-md" style="margin: 0 0 8px; text-align: center">注册</h1>
        <p class="t-caption t-muted" style="text-align: center; margin: 0 0 32px">
          创建账号，开始你的借阅之旅
        </p>
        <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="large">
          <el-form-item label="用户名（注册后不可修改）" prop="username">
            <el-input v-model="form.username" placeholder="3-50 位字母、数字或下划线" />
          </el-form-item>
          <el-form-item label="昵称">
            <el-input v-model="form.nickname" placeholder="怎么称呼你" />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="选填" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.phone" placeholder="选填" />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirm">
            <el-input v-model="form.confirm" type="password" show-password placeholder="再输入一次密码" />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%; margin-top: 8px"
            :loading="loading"
            @click="submit"
          >
            注册并登录
          </el-button>
        </el-form>
        <div class="t-caption" style="margin-top: 24px; text-align: center">
          已有账号？
          <router-link :to="{ name: 'login' }">直接登录</router-link>
        </div>
      </div>
    </div>
  </section>
</template>
