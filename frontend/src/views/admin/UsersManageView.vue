<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usersApi } from '../../api'
import { apiError } from '../../api/client'
import type { Page, User } from '../../types'
import { useAuthStore } from '../../stores/auth'
import { ROLE_TEXT, fmtDate } from '../../utils/format'

const auth = useAuthStore()
const keyword = ref('')
const role = ref('')
const page = ref(1)
const size = 10
const total = ref(0)
const items = ref<User[]>([])
const loading = ref(false)

let debounce: ReturnType<typeof setTimeout> | null = null
function onKeyword() {
  if (debounce) clearTimeout(debounce)
  debounce = setTimeout(() => {
    page.value = 1
    load()
  }, 300)
}

async function load() {
  loading.value = true
  try {
    const { data } = await usersApi.list({
      keyword: keyword.value || undefined,
      role: role.value || undefined,
      page: page.value,
      size,
    })
    const p: Page<User> = data
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

async function changeRole(u: User, newRole: string) {
  if (u.id === auth.user?.id) {
    ElMessage.warning('不能修改自己的角色')
    load()
    return
  }
  try {
    await usersApi.updateRole(u.id, newRole)
    ElMessage.success(`已将 ${u.username} 的角色调整为 ${ROLE_TEXT[newRole]}`)
    load()
  } catch (e) {
    ElMessage.error(apiError(e))
    load()
  }
}

async function toggleStatus(u: User, active: boolean) {
  if (u.id === auth.user?.id) {
    ElMessage.warning('不能禁用自己的账号')
    load()
    return
  }
  try {
    await usersApi.updateStatus(u.id, active)
    ElMessage.success(active ? `已启用 ${u.username}` : `已禁用 ${u.username}`)
    load()
  } catch (e) {
    ElMessage.error(apiError(e))
    load()
  }
}

async function remove(u: User) {
  if (u.id === auth.user?.id) {
    ElMessage.warning('不能删除自己的账号')
    return
  }
  try {
    await ElMessageBox.confirm(`确定删除用户 ${u.username}（${u.nickname}）吗？其评论与已读记录将被一并删除。`, '删除用户', { type: 'warning' })
    await usersApi.remove(u.id)
    ElMessage.success('用户已删除')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(apiError(e))
  }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="toolbar" style="margin-bottom: 20px">
      <el-input
        v-model="keyword"
        placeholder="搜索用户名 / 昵称 / 邮箱"
        clearable
        style="width: 260px"
        @input="onKeyword"
        @clear="page = 1; load()"
      />
      <el-select v-model="role" placeholder="全部角色" clearable style="width: 150px" @change="page = 1; load()">
        <el-option label="管理员" value="admin" />
        <el-option label="普通用户" value="user" />
        <el-option label="VIP 用户" value="vip" />
      </el-select>
      <div class="grow"></div>
      <span class="t-caption t-muted">共 {{ total }} 位用户</span>
    </div>

    <div v-loading="loading" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 8px 24px 24px">
      <el-table :data="items" style="width: 100%">
        <el-table-column label="用户" min-width="180">
          <template #default="{ row }">
            <div class="toolbar" style="gap: 10px">
              <el-avatar :size="32" :src="row.avatar ?? undefined" style="background: #0066cc; flex-shrink: 0">
                {{ (row.nickname || row.username)[0] }}
              </el-avatar>
              <span>{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="nickname" label="昵称" min-width="120" show-overflow-tooltip />
        <el-table-column prop="email" label="邮箱" min-width="170" show-overflow-tooltip />
        <el-table-column prop="phone" label="手机号" width="130" />
        <el-table-column label="角色" width="140">
          <template #default="{ row }">
            <el-select
              v-if="row.id !== auth.user?.id"
              :model-value="row.role"
              size="small"
              style="width: 110px"
              @update:model-value="changeRole(row, $event)"
            >
              <el-option label="管理员" value="admin" />
              <el-option label="普通用户" value="user" />
              <el-option label="VIP 用户" value="vip" />
            </el-select>
            <el-tag v-else type="primary" effect="plain">管理员（我）</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-switch
              v-if="row.id !== auth.user?.id"
              :model-value="row.isActive"
              @update:model-value="toggleStatus(row, $event)"
            />
            <span v-else class="t-caption">正常</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="注册时间" width="120">
          <template #default="{ row }">{{ fmtDate(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.id !== auth.user?.id"
              text
              size="small"
              class="btn-utility"
              style="color: var(--c-danger)"
              @click="remove(row)"
            >
              删除
            </el-button>
            <span v-else class="t-caption t-muted">—</span>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination
        v-model:current-page="page"
        :total="total"
        :page-size="size"
        layout="total, prev, pager, next"
        background
        style="margin-top: 24px"
        @current-change="load"
      />
    </div>
  </div>
</template>
