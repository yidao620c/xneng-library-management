<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Book } from '../types'
import CoverImage from './CoverImage.vue'
import StarDisplay from './StarDisplay.vue'

const props = defineProps<{ book: Book }>()
const router = useRouter()

function open() {
  router.push({ name: 'book-detail', params: { id: props.book.id } })
}
</script>

<template>
  <article class="book-card" @click="open">
    <CoverImage :cover="book.cover" :title="book.title" />
    <h3>{{ book.title }}</h3>
    <div class="t-caption t-muted">{{ book.author || '佚名' }}</div>
    <StarDisplay :value="book.ratingAvg" :show-value="book.ratingCount > 0" />
    <div class="t-caption" style="margin-top: auto">
      <span v-if="book.availableCopies > 0" style="color: var(--c-primary)">可借 {{ book.availableCopies }} 册</span>
      <span v-else class="t-muted">已全部借出</span>
    </div>
  </article>
</template>
