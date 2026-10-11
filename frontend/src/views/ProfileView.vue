<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { profileApi } from '../api'
import { apiError } from '../api/client'
import { useAuthStore } from '../stores/auth'
import SubNav from '../components/SubNav.vue'
import { ROLE_TEXT } from '../utils/format'

const auth = useAuthStore()
const fileInput = ref<HTMLInputElement>()

const form = reactive({
  nickname: auth.user?.nickname ?? '',
  email: auth.user?.email ?? '',
  phone: auth.user?.phone ?? '',
})
const saving = ref(false)
const uploading = ref(false)

/** 头像限制：webp / png / jpeg，100K 以内 */
function pickAvatar() {
  fileInput.value?.click()
}

async function onAvatarChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  const okTypes = ['image/webp', 'image/png', 'image/jpeg']
  if (!okTypes.includes(file.type)) {
    ElMessage.error('头像仅支持 webp、png、jpeg 格式')
    return
  }
  if (file.size > 100 * 1024) {
    ElMessage.error('头像大小不能超过 100K')
    return
  }
  uploading.value = true
  try {
    const { data } = await profileApi.uploadAvatar(file)
    auth.setUser(data)
    ElMessage.success('头像已更新')
  } catch (e) {
    ElMessage.error(apiError(e))
  } finally {
    uploading.value = false
  }
}

async function save() {
  if (!form.nickname.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }
  saving.value = true
  try {
    const { data } = await profileApi.update({
      nickname: form.nickname.trim(),
      email: form.email.trim(),
      phone: form.phone.trim(),
    })
    auth.setUser(data)
    ElMessage.success('个人信息已保存')
  } catch (e) {
    ElMessage.error(apiError(e))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <SubNav title="个人中心" />
    <section class="section-tight">
      <div class="container-narrow">
        <div style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 40px">
          <div style="display: flex; gap: 32px; align-items: center; margin-bottom: 40px; flex-wrap: wrap">
            <div style="position: relative; cursor: pointer" @click="pickAvatar">
              <el-avatar :size="96" :src="auth.user?.avatar ?? undefined" style="background: #0066cc; font-size: 36px">
                {{ (auth.user?.nickname || auth.user?.username || '读')[0] }}
              </el-avatar>
              <div
                v-loading="uploading"
                class="t-fine"
                style="position: absolute; inset: auto 0 0; text-align: center; background: rgba(0,0,0,0.45); color: #fff; border-radius: 0 0 47px 47px; padding: 4px 0"
              >
                更换头像
              </div>
            </div>
            <div>
              <div class="t-tagline">{{ auth.user?.nickname || auth.user?.username }}</div>
              <div class="t-caption t-muted" style="margin-top: 6px">
                {{ ROLE_TEXT[auth.user?.role ?? 'user'] }} · 头像支持 webp / png / jpeg，100K 以内
              </div>
            </div>
            <input
              ref="fileInput"
              type="file"
              accept="image/webp,image/png,image/jpeg"
              style="display: none"
              @change="onAvatarChange"
            />
          </div>

          <el-form label-position="top" size="large" style="max-width: 480px">
            <el-form-item label="用户名（不可修改）">
              <el-input :model-value="auth.user?.username" disabled />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="form.nickname" maxlength="50" placeholder="怎么称呼你" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="form.email" maxlength="120" placeholder="example@mail.com" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="form.phone" maxlength="20" placeholder="138xxxxxxxx" />
            </el-form-item>
            <el-button type="primary" size="large" :loading="saving" @click="save">保存修改</el-button>
          </el-form>
        </div>
      </div>
    </section>
  </div>
</template>
