<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { borrowsApi } from '../api'
import { apiError } from '../api/client'
import type { Borrow, Page } from '../types'
import SubNav from '../components/SubNav.vue'
import CoverImage from '../components/CoverImage.vue'
import { BORROW_STATUS_TEXT, fmtDate } from '../utils/format'

const route = useRoute()
const status = ref((route.query.status as string) || 'active')
const page = ref(1)
const size = 10
const total = ref(0)
const items = ref<Borrow[]>([])
const summary = ref({ borrowing: 0, overdue: 0, returned: 0 })
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [list, sum] = await Promise.all([
      borrowsApi.my({ status: status.value || undefined, page: page.value, size }),
      borrowsApi.mySummary(),
    ])
    const data: Page<Borrow> = list.data
    items.value = data.items
    total.value = data.total
    summary.value = sum.data
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

async function requestReturn(b: Borrow) {
  try {
    await ElMessageBox.confirm(
      `确认归还《${b.book.title}》吗？提交后请等待管理员确认。`,
      '申请归还',
      { type: 'info' },
    )
    await borrowsApi.requestReturn(b.id)
    ElMessage.success('归还申请已提交，等待管理员确认')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(apiError(e))
  }
}

function onStatusChange() {
  page.value = 1
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <SubNav title="我的借阅">
      <template #actions>
        <el-select :model-value="status" style="width: 160px" @update:model-value="status = $event; onStatusChange()">
          <el-option label="借阅中（含待确认）" value="active" />
          <el-option label="已逾期" value="overdue" />
          <el-option label="归还待确认" value="returning" />
          <el-option label="已归还" value="returned" />
          <el-option label="全部记录" value="" />
        </el-select>
      </template>
    </SubNav>

    <section class="section-tight">
      <div class="container">
        <div class="stat-grid" style="margin-bottom: 32px">
          <div class="stat-card">
            <div class="label">借阅中</div>
            <div class="value">{{ summary.borrowing }}</div>
          </div>
          <div class="stat-card">
            <div class="label">已逾期</div>
            <div class="value" :style="{ color: summary.overdue ? 'var(--c-danger)' : undefined }">
              {{ summary.overdue }}
            </div>
          </div>
          <div class="stat-card">
            <div class="label">累计已归还</div>
            <div class="value">{{ summary.returned }}</div>
          </div>
        </div>

        <div v-loading="loading" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 8px 24px 24px">
          <el-table :data="items" style="width: 100%">
            <el-table-column label="图书" min-width="260">
              <template #default="{ row }">
                <div class="toolbar" style="gap: 12px">
                  <div style="width: 44px; flex-shrink: 0">
                    <CoverImage :cover="row.book.cover" :title="row.book.title" :radius="8" />
                  </div>
                  <router-link :to="{ name: 'book-detail', params: { id: row.bookId } }">
                    {{ row.book.title }}
                  </router-link>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="borrowedAt" label="借出日期" width="120">
              <template #default="{ row }">{{ fmtDate(row.borrowedAt) }}</template>
            </el-table-column>
            <el-table-column prop="dueDate" label="预计归还日期" width="130">
              <template #default="{ row }">
                <span :style="row.overdue ? 'color: var(--c-danger)' : ''">{{ fmtDate(row.dueDate) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="returnedAt" label="实际归还" width="120">
              <template #default="{ row }">{{ fmtDate(row.returnedAt) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="150">
              <template #default="{ row }">
                <el-tag :type="statusType(row)" effect="light">{{ statusText(row) }}</el-tag>
                <el-tooltip v-if="row.remindedAt && row.status !== 'returned'" content="管理员已发送催还通知">
                  <el-tag style="margin-left: 6px" type="danger" effect="plain" size="small">已催还</el-tag>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'borrowed'"
                  type="primary"
                  size="small"
                  @click="requestReturn(row)"
                >
                  申请归还
                </el-button>
                <span v-else-if="row.status === 'returning'" class="t-caption t-muted">待管理员确认</span>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="!items.length && !loading" class="empty-hint">这里还没有借阅记录，去<a href="/">图书检索</a>逛逛吧。</div>
          <el-pagination
            v-model:current-page="page"
            :total="total"
            :page-size="size"
            layout="prev, pager, next"
            background
            hide-on-single-page
            style="margin-top: 24px"
            @current-change="load"
          />
        </div>
      </div>
    </section>
  </div>
</template>
