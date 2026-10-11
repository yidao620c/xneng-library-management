<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { messagesApi } from '../../api'
import { apiError } from '../../api/client'
import type { Message, Page } from '../../types'
import { fmtDateTime } from '../../utils/format'

const form = reactive({ title: '', content: '' })
const publishing = ref(false)
const items = ref<Message[]>([])
const page = ref(1)
const size = 10
const total = ref(0)
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await messagesApi.adminList({ page: page.value, size })
    const p: Page<Message> = data
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

async function publish() {
  if (!form.title.trim() || !form.content.trim()) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  publishing.value = true
  try {
    await messagesApi.create({ title: form.title.trim(), content: form.content.trim() })
    ElMessage.success('消息已发布给全体用户')
    Object.assign(form, { title: '', content: '' })
    page.value = 1
    load()
  } catch (e) {
    ElMessage.error(apiError(e))
  } finally {
    publishing.value = false
  }
}

async function remove(m: Message) {
  try {
    await ElMessageBox.confirm(`确定删除消息「${m.title}」吗？`, '删除消息', { type: 'warning' })
    await messagesApi.remove(m.id)
    ElMessage.success('消息已删除')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(apiError(e))
  }
}

onMounted(load)
</script>

<template>
  <div style="display: grid; grid-template-columns: 360px 1fr; gap: 24px; align-items: start">
    <div style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 24px">
      <div class="t-body-strong" style="margin-bottom: 16px">发布系统消息</div>
      <el-input v-model="form.title" maxlength="200" placeholder="消息标题" style="margin-bottom: 12px" />
      <el-input
        v-model="form.content"
        type="textarea"
        :rows="6"
        maxlength="5000"
        show-word-limit
        placeholder="消息内容，将发送给全体用户"
      />
      <el-button
        type="primary"
        style="width: 100%; margin-top: 16px"
        :loading="publishing"
        @click="publish"
      >
        发布
      </el-button>
      <div class="t-caption t-muted" style="margin-top: 12px">
        催还通知会在管理员执行「催还」时自动以个人消息发出。
      </div>
    </div>

    <div v-loading="loading" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 8px 24px 24px">
      <el-table :data="items" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column prop="content" label="内容" min-width="240" show-overflow-tooltip />
        <el-table-column label="接收方" width="130">
          <template #default="{ row }">
            <el-tag :type="row.targetUserId ? 'warning' : 'primary'" effect="plain" size="small">
              {{ row.targetUsername ?? '全体用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="发布时间" width="160">
          <template #default="{ row }">{{ fmtDateTime(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" class="btn-utility" style="color: var(--c-danger)" @click="remove(row)">
              删除
            </el-button>
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

<style scoped>
@media (max-width: 1024px) {
  .publish-grid {
    grid-template-columns: 1fr;
  }
}
</style>
