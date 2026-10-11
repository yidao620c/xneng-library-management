<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { booksApi, categoriesApi } from '../../api'
import { apiError } from '../../api/client'
import type { Book, Category, Page } from '../../types'
import CoverImage from '../../components/CoverImage.vue'
import StarDisplay from '../../components/StarDisplay.vue'

const keyword = ref('')
const categoryId = ref<number | null>(null)
const page = ref(1)
const size = 10
const total = ref(0)
const items = ref<Book[]>([])
const categories = ref<Category[]>([])
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
    const { data } = await booksApi.list({
      keyword: keyword.value || undefined,
      categoryId: categoryId.value ?? undefined,
      page: page.value,
      size,
    })
    const p: Page<Book> = data
    items.value = p.items
    total.value = p.total
  } finally {
    loading.value = false
  }
}

/* ---------- 编辑 / 新建 ---------- */
const dialogVisible = ref(false)
const editing = ref<Book | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  title: '',
  author: '',
  isbn: '',
  publisher: '',
  description: '',
  categoryId: null as number | null,
  tags: '',
  totalCopies: 1,
  availableCopies: 1,
})

function openCreate() {
  editing.value = null
  Object.assign(form, {
    title: '', author: '', isbn: '', publisher: '', description: '',
    categoryId: null, tags: '', totalCopies: 1, availableCopies: 1,
  })
  dialogVisible.value = true
}

function openEdit(b: Book) {
  editing.value = b
  Object.assign(form, {
    title: b.title,
    author: b.author,
    isbn: b.isbn,
    publisher: b.publisher,
    description: b.description,
    categoryId: b.categoryId,
    tags: b.tags.join(','),
    totalCopies: b.totalCopies,
    availableCopies: b.availableCopies,
  })
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.title.trim() || !form.isbn.trim()) {
    ElMessage.warning('请填写书名和 ISBN')
    return
  }
  if (form.availableCopies > form.totalCopies) {
    ElMessage.warning('在馆数量不能超过馆藏总量')
    return
  }
  const payload = {
    title: form.title.trim(),
    author: form.author.trim(),
    isbn: form.isbn.trim(),
    publisher: form.publisher.trim(),
    description: form.description.trim(),
    categoryId: form.categoryId,
    tags: form.tags.trim(),
    totalCopies: form.totalCopies,
    availableCopies: form.availableCopies,
  }
  try {
    if (editing.value) {
      await booksApi.update(editing.value.id, payload)
      ElMessage.success('图书已更新')
    } else {
      await booksApi.create(payload)
      ElMessage.success('图书已添加，可在列表中继续上传封面')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(apiError(e))
  }
}

async function remove(b: Book) {
  try {
    await ElMessageBox.confirm(`确定删除《${b.title}》吗？`, '删除图书', { type: 'warning' })
    await booksApi.remove(b.id)
    ElMessage.success('图书已删除')
    load()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(apiError(e))
  }
}

/* ---------- 封面上传 ---------- */
const coverBook = ref<Book | null>(null)
const coverPreview = ref<string | null>(null)
const coverInput = ref<HTMLInputElement>()
const coverUploading = ref(false)

function openCover(b: Book) {
  coverBook.value = b
  coverPreview.value = b.cover
}

function pickCover() {
  coverInput.value?.click()
}

async function onCoverChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !coverBook.value) return
  const okTypes = ['image/webp', 'image/png', 'image/jpeg']
  if (!okTypes.includes(file.type)) {
    ElMessage.error('封面仅支持 webp、png、jpeg 格式')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('封面大小不能超过 2M')
    return
  }
  coverUploading.value = true
  try {
    const { data } = await booksApi.uploadCover(coverBook.value.id, file)
    coverPreview.value = data.cover
    ElMessage.success('封面已上传')
    load()
  } catch (err) {
    ElMessage.error(apiError(err))
  } finally {
    coverUploading.value = false
  }
}

onMounted(async () => {
  const { data } = await categoriesApi.list()
  categories.value = data
  load()
})
</script>

<template>
  <div>
    <div class="toolbar" style="margin-bottom: 20px">
      <el-input
        v-model="keyword"
        placeholder="搜索书名 / 作者 / ISBN"
        clearable
        style="width: 280px"
        @input="onKeyword"
        @clear="page = 1; load()"
      />
      <el-select
        v-model="categoryId"
        placeholder="全部分类"
        clearable
        style="width: 160px"
        @change="page = 1; load()"
      >
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <div class="grow"></div>
      <el-button type="primary" @click="openCreate">新增图书</el-button>
    </div>

    <div v-loading="loading" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 8px 24px 24px">
      <el-table :data="items" style="width: 100%">
        <el-table-column label="封面" width="70">
          <template #default="{ row }">
            <div style="width: 44px">
              <CoverImage :cover="row.cover" :title="row.title" :radius="8" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="书名" min-width="180" show-overflow-tooltip />
        <el-table-column prop="author" label="作者" width="140" show-overflow-tooltip />
        <el-table-column prop="isbn" label="ISBN" width="140" />
        <el-table-column prop="categoryName" label="分类" width="110" />
        <el-table-column label="评分" width="120">
          <template #default="{ row }">
            <StarDisplay :value="row.ratingAvg" :show-value="row.ratingCount > 0" />
          </template>
        </el-table-column>
        <el-table-column label="在馆/总量" width="100">
          <template #default="{ row }">{{ row.availableCopies }} / {{ row.totalCopies }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" class="btn-utility" @click="openCover(row)">封面</el-button>
            <el-button text size="small" class="btn-utility" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editing ? `编辑：${editing.title}` : '新增图书'"
      width="560px"
    >
      <el-form ref="formRef" :model="form" label-width="92px">
        <el-form-item label="书名" required>
          <el-input v-model="form.title" maxlength="200" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="form.author" maxlength="100" />
        </el-form-item>
        <el-form-item label="ISBN" required>
          <el-input v-model="form.isbn" maxlength="20" />
        </el-form-item>
        <el-form-item label="出版社">
          <el-input v-model="form.publisher" maxlength="100" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.categoryId" placeholder="选择分类" clearable style="width: 100%">
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="多个标签用英文逗号分隔，如：科幻,雨果奖" />
        </el-form-item>
        <el-form-item label="馆藏总量">
          <el-input-number v-model="form.totalCopies" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="在馆数量">
          <el-input-number v-model="form.availableCopies" :min="0" :max="999" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="form.description" type="textarea" :rows="3" maxlength="5000" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button class="btn-utility" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog
      :model-value="coverBook !== null"
      :title="coverBook ? `封面：${coverBook.title}` : ''"
      width="400px"
      @update:model-value="coverBook = null; coverPreview = null"
    >
      <div v-loading="coverUploading" style="display: flex; flex-direction: column; align-items: center; gap: 20px">
        <div style="width: 240px">
          <CoverImage :cover="coverPreview" :title="coverBook?.title ?? '书'" :radius="18" />
        </div>
        <div>
          <el-button type="primary" @click="pickCover">选择图片上传</el-button>
        </div>
        <div class="t-caption t-muted" style="text-align: center">
          支持 webp / png / jpeg，2M 以内；不上传则展示书名首字封面。
        </div>
      </div>
      <input
        ref="coverInput"
        type="file"
        accept="image/webp,image/png,image/jpeg"
        style="display: none"
        @change="onCoverChange"
      />
    </el-dialog>
  </div>
</template>
