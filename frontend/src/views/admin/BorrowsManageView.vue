<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { borrowsApi } from '../../api'
import { apiError } from '../../api/client'
import type { Borrow, Page } from '../../types'
import { BORROW_STATUS_TEXT, fmtDate, fmtDateTime } from '../../utils/format'

const status = ref('')
const keyword = ref('')
const page = ref(1)
const size = 10
const total = ref(0)
const items = ref<Borrow[]>([])
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
    const { data } = await borrowsApi.list({
      status: status.value || undefined,
      keyword: keyword.value || undefined,
      page: page.value,
      size,
    })
    const p: Page<Borrow> = data
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

function statusType(b: Borrow): 'primary' | 'warning' | 'info' | 'danger' {
  if (b.status === 'returned') return 'info'
  if (b.overdue) return 'danger'
  if (b.status === 'returning') return 'warning'
  return 'primary'
}

function statusText(b: Borrow): string {
  if (b.status === 'returned') return '已归还'
  if (b.overdue) return '已逾期'
  return BORROW_STATUS_TEXT[b.status]
}

async function confirmReturn(b: Borrow) {
  try {
    await ElMessageBox.confirm(
      `确认《${b.book.title}》已归还吗？确认后在馆数量 +1。`,
      '归还确认',
      { type: 'info' },
    )
    await borrowsApi.confirmReturn(b.id)
    ElMessage.success('已确认归还')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(apiError(e))
  }
}

async function remind(b: Borrow) {
  try {
    await ElMessageBox.confirm(
      `向 ${b.user.nickname || b.user.username} 发送《${b.book.title}》催还通知吗？`,
      '催还提醒',
      { type: 'warning' },
    )
    await borrowsApi.remind(b.id)
    ElMessage.success('催还通知已发送到用户消息中心')
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
        placeholder="搜索用户名 / 昵称 / 书名"
        clearable
        style="width: 260px"
        @input="onKeyword"
        @clear="page = 1; load()"
      />
      <el-select v-model="status" placeholder="全部状态" clearable style="width: 160px" @change="page = 1; load()">
        <el-option label="借阅中" value="borrowed" />
        <el-option label="归还待确认" value="returning" />
        <el-option label="已归还" value="returned" />
        <el-option label="已逾期" value="overdue" />
      </el-select>
      <div class="grow"></div>
      <span class="t-caption t-muted">共 {{ total }} 条记录</span>
    </div>

    <div v-loading="loading" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 8px 24px 24px">
      <el-table :data="items" style="width: 100%">
        <el-table-column label="用户" min-width="140">
          <template #default="{ row }">{{ row.user.nickname || row.user.username }}</template>
        </el-table-column>
        <el-table-column label="图书" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <router-link :to="{ name: 'book-detail', params: { id: row.bookId } }">
              {{ row.book.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="borrowedAt" label="借出时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.borrowedAt) }}</template>
        </el-table-column>
        <el-table-column prop="dueDate" label="应还日期" width="120">
          <template #default="{ row }">
            <span :style="row.overdue && row.status !== 'returned' ? 'color: var(--c-danger)' : ''">
              {{ fmtDate(row.dueDate) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="returnedAt" label="归还时间" width="150">
          <template #default="{ row }">{{ fmtDateTime(row.returnedAt) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="160">
          <template #default="{ row }">
            <el-tag :type="statusType(row)" effect="light">{{ statusText(row) }}</el-tag>
            <el-tooltip v-if="row.remindedAt && row.status !== 'returned'" :content="`最后催还：${fmtDateTime(row.remindedAt)}`">
              <el-tag style="margin-left: 6px" type="danger" effect="plain" size="small">已催还</el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status !== 'returned'">
              <el-button text size="small" class="btn-utility" @click="remind(row)">催还</el-button>
              <el-button text size="small" class="btn-utility" type="primary" @click="confirmReturn(row)">
                归还确认
              </el-button>
            </template>
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
