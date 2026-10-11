<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { categoriesApi } from '../../api'
import { apiError } from '../../api/client'
import type { Category } from '../../types'
import { fmtDate } from '../../utils/format'

const items = ref<Category[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const editing = ref<Category | null>(null)
const form = reactive({ name: '', description: '' })

async function load() {
  loading.value = true
  try {
    const { data } = await categoriesApi.list()
    items.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, { name: '', description: '' })
  dialogVisible.value = true
}

function openEdit(c: Category) {
  editing.value = c
  Object.assign(form, { name: c.name, description: c.description })
  dialogVisible.value = true
}

async function submitForm() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写分类名称')
    return
  }
  try {
    if (editing.value) {
      await categoriesApi.update(editing.value.id, form)
      ElMessage.success('分类已更新')
    } else {
      await categoriesApi.create(form)
      ElMessage.success('分类已创建')
    }
    dialogVisible.value = false
    load()
  } catch (e) {
    ElMessage.error(apiError(e))
  }
}

async function remove(c: Category) {
  try {
    await ElMessageBox.confirm(`确定删除分类「${c.name}」吗？`, '删除分类', { type: 'warning' })
    await categoriesApi.remove(c.id)
    ElMessage.success('分类已删除')
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
      <span class="t-caption t-muted">共 {{ items.length }} 个分类</span>
      <div class="grow"></div>
      <el-button type="primary" @click="openCreate">新增分类</el-button>
    </div>

    <div v-loading="loading" style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 8px 24px 24px">
      <el-table :data="items" style="width: 100%">
        <el-table-column prop="name" label="分类名称" min-width="160" />
        <el-table-column prop="description" label="描述" min-width="240" show-overflow-tooltip />
        <el-table-column prop="bookCount" label="图书数量" width="110" />
        <el-table-column prop="createdAt" label="创建时间" width="130">
          <template #default="{ row }">{{ fmtDate(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" class="btn-utility" @click="openEdit(row)">编辑</el-button>
            <el-button text size="small" class="btn-utility" style="color: var(--c-danger)" @click="remove(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" :title="editing ? `编辑：${editing.name}` : '新增分类'" width="440px">
      <el-form label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" maxlength="50" placeholder="如：文学小说" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button class="btn-utility" @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
