<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { borrowsApi, booksApi, reviewsApi } from '../api'
import { apiError } from '../api/client'
import type { Book, Borrow, Page, Review } from '../types'
import { useAuthStore } from '../stores/auth'
import CoverImage from '../components/CoverImage.vue'
import StarDisplay from '../components/StarDisplay.vue'
import SubNav from '../components/SubNav.vue'
import { fmtDate, fmtDateTime } from '../utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const bookId = Number(route.params.id)
const book = ref<Book | null>(null)
const reviews = ref<Page<Review> | null>(null)
const reviewPage = ref(1)
const myActiveBorrow = ref<Borrow | null>(null)
const borrowing = ref(false)

const reviewForm = ref({ rating: 0, content: '' })
const submittingReview = ref(false)

const canBorrow = computed(() => {
  if (!book.value) return false
  if (book.value.availableCopies <= 0) return false
  return !myActiveBorrow.value
})

async function loadBook() {
  const { data } = await booksApi.detail(bookId)
  book.value = data
}

async function loadReviews() {
  const { data } = await reviewsApi.list(bookId, { page: reviewPage.value, size: 8 })
  reviews.value = data
}

async function loadMyBorrow() {
  if (!auth.isLoggedIn) return
  const { data } = await borrowsApi.my({ status: 'active', size: 100 })
  myActiveBorrow.value = data.items.find((b) => b.bookId === bookId) ?? null
}

async function borrow() {
  if (!auth.isLoggedIn) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  borrowing.value = true
  try {
    const { data } = await borrowsApi.create(bookId)
    ElMessage.success(`借阅成功，请在 ${fmtDate(data.dueDate)} 前归还`)
    await Promise.all([loadBook(), loadMyBorrow()])
  } catch (e) {
    ElMessage.error(apiError(e))
  } finally {
    borrowing.value = false
  }
}

async function submitReview() {
  const content = reviewForm.value.content.trim()
  if (content.length <= 5) {
    ElMessage.warning('评论内容必须大于 5 个字')
    return
  }
  submittingReview.value = true
  try {
    await reviewsApi.create(bookId, { rating: reviewForm.value.rating, content })
    ElMessage.success('评论发布成功')
    reviewForm.value = { rating: 0, content: '' }
    reviewPage.value = 1
    await Promise.all([loadReviews(), loadBook()])
  } catch (e) {
    ElMessage.error(apiError(e))
  } finally {
    submittingReview.value = false
  }
}

async function removeReview(r: Review) {
  try {
    await ElMessageBox.confirm('确定删除这条评论吗？', '删除评论', { type: 'warning' })
    await reviewsApi.remove(r.id)
    ElMessage.success('评论已删除')
    await Promise.all([loadReviews(), loadBook()])
  } catch (e) {
    if (e !== 'cancel' && (e as { toString: () => string }).toString() !== 'cancel') {
      ElMessage.error(apiError(e))
    }
  }
}

onMounted(async () => {
  try {
    await loadBook()
  } catch {
    ElMessage.error('图书不存在')
    router.push({ name: 'home' })
    return
  }
  await Promise.all([loadReviews(), loadMyBorrow()])
})
</script>

<template>
  <div v-if="book">
    <SubNav :title="book.title">
      <template #actions>
        <span class="t-caption t-muted">{{ book.categoryName ?? '未分类' }}</span>
      </template>
    </SubNav>

    <section class="section-tight">
      <div class="container" style="display: flex; gap: 48px; align-items: flex-start; flex-wrap: wrap">
        <div style="width: 280px; flex-shrink: 0">
          <CoverImage :cover="book.cover" :title="book.title" :radius="18" />
          <div class="toolbar" style="margin-top: 24px; flex-direction: column; align-items: stretch; gap: 10px">
            <el-button
              v-if="myActiveBorrow"
              type="primary"
              size="large"
              @click="router.push({ name: 'my-borrows' })"
            >
              已在借阅中 · 查看我的借阅
            </el-button>
            <el-button
              v-else
              type="primary"
              size="large"
              :disabled="book.availableCopies <= 0"
              :loading="borrowing"
              @click="borrow"
            >
              {{ book.availableCopies > 0 ? '立即借阅' : '已全部借出' }}
            </el-button>
            <div class="t-caption t-muted" style="text-align: center">
              借期 14 天 · 在馆 {{ book.availableCopies }} / {{ book.totalCopies }} 册
            </div>
          </div>
        </div>

        <div style="flex: 1; min-width: 280px">
          <h1 class="t-display" style="margin: 0 0 12px">{{ book.title }}</h1>
          <div class="toolbar" style="margin-bottom: 20px">
            <StarDisplay :value="book.ratingAvg" :size="18" show-value />
            <span class="t-caption t-muted">{{ book.ratingCount }} 条评分</span>
          </div>
          <div class="t-caption" style="display: grid; gap: 8px; margin-bottom: 24px">
            <div><span class="t-muted">作者</span>　{{ book.author || '—' }}</div>
            <div><span class="t-muted">出版社</span>　{{ book.publisher || '—' }}</div>
            <div><span class="t-muted">ISBN</span>　{{ book.isbn }}</div>
            <div>
              <span class="t-muted">标签</span>
              <el-tag
                v-for="t in book.tags"
                :key="t"
                style="margin-left: 8px"
                effect="plain"
                size="small"
              >
                {{ t }}
              </el-tag>
              <span v-if="!book.tags.length" class="t-muted">　—</span>
            </div>
          </div>
          <p style="line-height: 1.6; margin: 0">{{ book.description || '暂无简介。' }}</p>
        </div>
      </div>
    </section>

    <!-- 评论区：羊皮纸分区，颜色变化即分隔 -->
    <section class="bg-parchment section-tight">
      <div class="container">
        <h2 class="t-display-md" style="margin: 0 0 8px">评分与评论</h2>
        <p class="t-caption t-muted" style="margin: 0 0 32px">
          评分为可选（默认 0 分），评论必填且须大于 5 个字；可多次评分，最终取平均分。
        </p>

        <div v-if="auth.isLoggedIn" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 24px; margin-bottom: 32px">
          <div class="toolbar" style="margin-bottom: 16px">
            <span class="t-caption-strong">我的评分</span>
            <el-rate
              v-model="reviewForm.rating"
              :max="5"
              void-color="#d2d2d7"
              disabled-void-color="#d2d2d7"
              :colors="['#0066cc', '#0066cc', '#0066cc']"
            />
          </div>
          <el-input
            v-model="reviewForm.content"
            type="textarea"
            :rows="3"
            maxlength="2000"
            show-word-limit
            placeholder="写下你的读后感（大于 5 个字）"
          />
          <div style="margin-top: 16px; text-align: right">
            <el-button type="primary" :loading="submittingReview" @click="submitReview">发布评论</el-button>
          </div>
        </div>
        <div v-else class="t-caption" style="margin-bottom: 32px">
          <router-link :to="{ name: 'login', query: { redirect: route.fullPath } }">登录</router-link>
          后即可评分与评论。
        </div>

        <div v-if="reviews?.items.length" style="display: grid; gap: 16px">
          <div
            v-for="r in reviews.items"
            :key="r.id"
            style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 20px 24px"
          >
            <div class="toolbar" style="margin-bottom: 8px">
              <el-avatar :size="32" :src="r.user.avatar ?? undefined" style="background: #0066cc; flex-shrink: 0">
                {{ (r.user.nickname || r.user.username)[0] }}
              </el-avatar>
              <span class="t-body-strong">{{ r.user.nickname || r.user.username }}</span>
              <StarDisplay :value="r.rating" />
              <span class="t-caption t-muted">{{ fmtDateTime(r.createdAt) }}</span>
              <div class="grow"></div>
              <el-button
                v-if="auth.user && (auth.user.id === r.user.id || auth.isAdmin)"
                text
                size="small"
                class="btn-utility"
                @click="removeReview(r)"
              >
                删除
              </el-button>
            </div>
            <div style="white-space: pre-wrap">{{ r.content }}</div>
          </div>
          <el-pagination
            v-model:current-page="reviewPage"
            :total="reviews.total"
            :page-size="8"
            layout="prev, pager, next"
            background
            hide-on-single-page
            @current-change="loadReviews"
          />
        </div>
        <div v-else class="empty-hint">还没有评论，来做第一个读者吧。</div>
      </div>
    </section>
  </div>
</template>
