<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { booksApi, categoriesApi } from '../api'
import type { Book, Category, Page } from '../types'
import BookCard from '../components/BookCard.vue'
import SubNav from '../components/SubNav.vue'

const filters = reactive({
  keyword: '',
  categoryId: null as number | null,
  status: '',
  tag: '',
})
const page = ref(1)
const size = 12
const total = ref(0)
const books = ref<Book[]>([])
const categories = ref<Category[]>([])
const tags = ref<string[]>([])
const loading = ref(false)

let debounceTimer: ReturnType<typeof setTimeout> | null = null
function onKeywordInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    page.value = 1
    load()
  }, 300)
}

function pickCategory(id: number | null) {
  filters.categoryId = filters.categoryId === id ? null : id
  page.value = 1
}

async function load() {
  loading.value = true
  try {
    const { data } = await booksApi.list({
      keyword: filters.keyword || undefined,
      categoryId: filters.categoryId ?? undefined,
      status: filters.status || undefined,
      tag: filters.tag || undefined,
      page: page.value,
      size,
    })
    books.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

watch([() => filters.categoryId, () => filters.status, () => filters.tag], () => load())
watch(page, () => load())

onMounted(async () => {
  const [cats, tgs] = await Promise.all([categoriesApi.list(), booksApi.tags()])
  categories.value = cats.data
  tags.value = tgs.data
  load()
})
</script>

<template>
  <div>
    <!-- 英雄区：羊皮纸画布 + 大标题 + 胶囊搜索 -->
    <section class="bg-parchment" style="padding: 80px 0 48px">
      <div class="container" style="text-align: center">
        <h1 class="t-hero" style="margin: 0 0 16px">阅读，从此开始。</h1>
        <p class="t-lead t-muted" style="margin: 0 auto 32px; max-width: 560px">
          检索馆藏图书，按分类、标签与在馆状态筛选，一键借阅。
        </p>
        <div style="max-width: 560px; margin: 0 auto">
          <el-input
            v-model="filters.keyword"
            size="large"
            placeholder="搜索书名、作者或 ISBN"
            :prefix-icon="Search"
            clearable
            @input="onKeywordInput"
            @clear="page = 1"
          />
        </div>
      </div>
    </section>

    <SubNav title="全部图书">
      <template #actions>
        <span class="t-caption t-muted">共 {{ total }} 种</span>
        <el-select
          v-model="filters.status"
          placeholder="在馆状态"
          clearable
          style="width: 140px"
        >
          <el-option label="可借" value="available" />
          <el-option label="已全部借出" value="unavailable" />
        </el-select>
        <el-select v-model="filters.tag" placeholder="标签" clearable style="width: 140px">
          <el-option v-for="t in tags" :key="t" :label="t" :value="t" />
        </el-select>
      </template>
    </SubNav>

    <section class="section-tight">
      <div class="container">
        <div class="toolbar" style="margin-bottom: 24px">
          <span
            class="chip"
            :class="{ selected: filters.categoryId === null }"
            @click="pickCategory(null)"
          >
            全部分类
          </span>
          <span
            v-for="c in categories"
            :key="c.id"
            class="chip"
            :class="{ selected: filters.categoryId === c.id }"
            @click="pickCategory(c.id)"
          >
            {{ c.name }}
            <span class="t-fine t-muted">{{ c.bookCount }}</span>
          </span>
        </div>

        <div v-loading="loading">
          <div v-if="books.length" class="book-grid">
            <BookCard v-for="b in books" :key="b.id" :book="b" />
          </div>
          <div v-else class="empty-hint">没有找到匹配的图书，试试更换关键词或筛选条件。</div>
        </div>

        <div style="margin-top: 48px">
          <el-pagination
            v-model:current-page="page"
            :total="total"
            :page-size="size"
            layout="prev, pager, next"
            background
            hide-on-single-page
          />
        </div>
      </div>
    </section>
  </div>
</template>
