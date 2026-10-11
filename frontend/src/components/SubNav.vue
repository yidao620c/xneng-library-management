<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <div class="sub-nav">
    <div class="inner">
      <div class="title">{{ title }}</div>
      <div class="toolbar">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>
