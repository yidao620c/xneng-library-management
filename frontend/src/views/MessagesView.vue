<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { messagesApi } from '../api'
import { apiError } from '../api/client'
import type { Message, Page } from '../types'
import { useAuthStore } from '../stores/auth'
import SubNav from '../components/SubNav.vue'
import { fmtDateTime } from '../utils/format'

const auth = useAuthStore()
const page = ref(1)
const size = 10
const total = ref(0)
const items = ref<Message[]>([])
const expanded = ref<Set<number>>(new Set())
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await messagesApi.list({ page: page.value, size })
    items.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

async function open(m: Message) {
  if (expanded.value.has(m.id)) {
    expanded.value.delete(m.id)
  } else {
    expanded.value.add(m.id)
    if (!m.isRead) {
      try {
        await messagesApi.markRead(m.id)
        m.isRead = true
        auth.fetchUnread()
      } catch (e) {
        ElMessage.error(apiError(e))
      }
    }
  }
}

async function markAll() {
  try {
    await messagesApi.markAllRead()
    ElMessage.success('全部消息已标记为已读')
    await load()
    auth.fetchUnread()
  } catch (e) {
    ElMessage.error(apiError(e))
  }
}

onMounted(load)
</script>

<template>
  <div>
    <SubNav title="消息中心">
      <template #actions>
        <span class="t-caption t-muted">{{ auth.unreadCount }} 条未读</span>
        <el-button size="small" class="btn-utility" @click="markAll">全部已读</el-button>
      </template>
    </SubNav>

    <section class="section-tight">
      <div class="container-narrow" v-loading="loading">
        <div v-if="items.length" style="display: grid; gap: 12px">
          <div
            v-for="m in items"
            :key="m.id"
            class="message-card"
            :class="{ unread: !m.isRead }"
            style="border-radius: 18px; border: 1px solid var(--c-hairline); padding: 20px 24px; cursor: pointer"
            :style="{ background: m.isRead ? '#fff' : 'var(--c-pearl)' }"
            @click="open(m)"
          >
            <div class="toolbar">
              <span
                v-if="!m.isRead"
                style="width: 8px; height: 8px; border-radius: 50%; background: var(--c-primary); flex-shrink: 0"
              ></span>
              <span class="t-body-strong">{{ m.title }}</span>
              <span v-if="m.targetUserId" class="el-tag el-tag--primary el-tag--plain" style="height: auto; padding: 2px 8px">个人消息</span>
              <div class="grow"></div>
              <span class="t-caption t-muted">{{ fmtDateTime(m.createdAt) }}</span>
            </div>
            <div v-if="expanded.has(m.id)" style="margin-top: 12px; color: var(--c-ink-80)">
              {{ m.content }}
            </div>
          </div>
          <el-pagination
            v-model:current-page="page"
            :total="total"
            :page-size="size"
            layout="prev, pager, next"
            background
            hide-on-single-page
            @current-change="load"
          />
        </div>
        <div v-else class="empty-hint">暂无消息。</div>
      </div>
    </section>
  </div>
</template>
