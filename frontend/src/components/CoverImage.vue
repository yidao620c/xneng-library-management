<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    cover?: string | null
    title: string
    radius?: number
  }>(),
  { cover: null, radius: 8 },
)

const fallbackChar = computed(() => props.title?.trim()?.[0] ?? '书')
</script>

<template>
  <div class="cover" :style="{ borderRadius: `${radius}px` }">
    <img v-if="cover" :src="cover" :alt="title" loading="lazy" />
    <span v-else class="fallback-char">{{ fallbackChar }}</span>
  </div>
</template>
