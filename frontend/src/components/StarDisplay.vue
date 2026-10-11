<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    /** 0 - 5，支持小数（如平均分 4.3） */
    value: number
    size?: number
    showValue?: boolean
  }>(),
  { size: 14, showValue: false },
)

const STAR = '★'
const stars = computed(() => STAR.repeat(5))
const percent = computed(() => Math.max(0, Math.min(100, (props.value / 5) * 100)))
const font = computed(() => `${props.size}px`)
</script>

<template>
  <span class="stars" :style="{ fontSize: font }">
    <span class="row void-row">{{ stars }}</span>
    <span class="filled-row" :style="{ width: `${percent}%` }">{{ stars }}</span>
    <span v-if="showValue" class="t-caption t-muted" style="margin-left: 8px; letter-spacing: 0">
      {{ value.toFixed(1) }}
    </span>
  </span>
</template>
