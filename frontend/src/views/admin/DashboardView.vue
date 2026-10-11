<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { statsApi } from '../../api'
import { apiError } from '../../api/client'
import type { Overview, TrendItem } from '../../types'
import { ElMessage } from 'element-plus'

const overview = ref<Overview | null>(null)
const granularity = ref<'day' | 'week' | 'month'>('day')
const trendItems = ref<TrendItem[]>([])
const chartEl = ref<HTMLDivElement>()
let chart: echarts.ECharts | null = null

async function loadOverview() {
  try {
    const { data } = await statsApi.overview()
    overview.value = data
  } catch (e) {
    ElMessage.error(apiError(e))
  }
}

async function loadTrend() {
  try {
    const { data } = await statsApi.borrowTrend(granularity.value)
    trendItems.value = data.items
    renderChart()
  } catch (e) {
    ElMessage.error(apiError(e))
  }
}

function renderChart() {
  if (!chartEl.value) return
  if (!chart) {
    chart = echarts.init(chartEl.value)
  }
  chart.setOption({
    grid: { left: 48, right: 24, top: 32, bottom: 48 },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: trendItems.value.map((t) => t.label),
      axisLine: { lineStyle: { color: '#e0e0e0' } },
      axisLabel: { color: '#7a7a7a', fontSize: 12 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#7a7a7a', fontSize: 12 },
    },
    series: [
      {
        name: '借阅量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { color: '#0066cc', width: 2.5 },
        itemStyle: { color: '#0066cc' },
        areaStyle: { color: 'rgba(0, 102, 204, 0.08)' },
        data: trendItems.value.map((t) => t.count),
      },
    ],
  })
}

function onGranularityChange() {
  loadTrend()
}

function onResize() {
  chart?.resize()
}

onMounted(async () => {
  await loadOverview()
  await loadTrend()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  chart?.dispose()
})
</script>

<template>
  <div>
    <div class="stat-grid" style="margin-bottom: 32px">
      <div class="stat-card">
        <div class="label">图书种类</div>
        <div class="value">{{ overview?.totalBooks ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">馆藏总量 / 在馆可借</div>
        <div class="value">{{ overview ? `${overview.totalCopies} / ${overview.availableCopies}` : '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">注册用户</div>
        <div class="value">{{ overview?.totalUsers ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">借阅中</div>
        <div class="value">{{ overview?.borrowing ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">逾期未还</div>
        <div class="value" :style="{ color: overview?.overdue ? 'var(--c-danger)' : undefined }">
          {{ overview?.overdue ?? '—' }}
        </div>
      </div>
      <div class="stat-card">
        <div class="label">评论总数</div>
        <div class="value">{{ overview?.totalReviews ?? '—' }}</div>
      </div>
      <div class="stat-card">
        <div class="label">系统消息</div>
        <div class="value">{{ overview?.totalMessages ?? '—' }}</div>
      </div>
    </div>

    <div style="background: #fff; border: 1px solid var(--c-hairline); border-radius: 18px; padding: 24px">
      <div class="toolbar" style="margin-bottom: 8px">
        <span class="t-body-strong">借阅历史趋势</span>
        <div class="grow"></div>
        <el-radio-group v-model="granularity" size="small" @change="onGranularityChange">
          <el-radio-button value="day">按天</el-radio-button>
          <el-radio-button value="week">按周</el-radio-button>
          <el-radio-button value="month">按月</el-radio-button>
        </el-radio-group>
      </div>
      <div ref="chartEl" style="width: 100%; height: 380px"></div>
    </div>
  </div>
</template>
