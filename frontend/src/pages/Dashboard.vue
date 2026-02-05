<script setup>
import { ref, onMounted, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'

// 时间筛选
const currentYear = new Date().getFullYear()
const currentMonth = new Date().getMonth() + 1
const selectedYear = ref(currentYear)
const selectedMonth = ref(currentMonth)

const years = Array.from({ length: 5 }, (_, i) => currentYear - i)
const months = Array.from({ length: 12 }, (_, i) => i + 1)

// 统计卡片数据（预留 API 接口）
const stats = ref([
  { title: '本月支出', value: '¥3,245', desc: '较上月 +5%', icon: 'expense', trend: 'up', type: 'expense' },
  { title: '本月收入', value: '¥12,000', desc: '较上月 +8%', icon: 'income', trend: 'up', type: 'income' },
  { title: '本月结余', value: '¥8,755', desc: '结余率 73%', icon: 'balance', trend: 'neutral', type: 'balance' },
  { title: '账单笔数', value: '46', desc: '较上月 +12%', icon: 'count', trend: 'up', type: 'neutral' },
])

// 收支趋势图配置
const trendSeries = ref([
  { name: '收入', data: [12000, 13500, 11000, 15000, 14000, 12000, 16000, 14500, 13000, 15500, 14000, 12000] },
  { name: '支出', data: [4500, 5200, 4800, 6100, 5500, 3245, 5800, 6200, 4900, 7100, 5600, 4800] }
])

const trendOptions = computed(() => ({
  chart: {
    type: 'area',
    fontFamily: 'inherit',
    toolbar: { show: false },
    animations: { enabled: true }
  },
  colors: ['#22c55e', '#ef4444'],
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.05,
      stops: [0, 100]
    }
  },
  stroke: { curve: 'smooth', width: 2 },
  dataLabels: { enabled: false },
  xaxis: {
    categories: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'],
    labels: { style: { colors: 'hsl(var(--bc))' } }
  },
  yaxis: {
    labels: {
      style: { colors: 'hsl(var(--bc))' },
      formatter: (value) => '¥' + (value / 1000) + 'k'
    }
  },
  grid: { borderColor: 'hsl(var(--b3))', padding: { top: 0 } },
  legend: {
    labels: { colors: 'hsl(var(--bc))' },
    position: 'top',
    horizontalAlign: 'right',
    offsetY: -5,
    itemMargin: { horizontal: 15 }
  },
  tooltip: {
    theme: 'dark',
    y: { formatter: (value) => '¥' + value.toLocaleString() }
  }
}))

// 分类支出图配置
const categorySeries = ref([35, 25, 20, 12, 8])
const categoryLabels = ['餐饮', '交通', '购物', '娱乐', '其他']

const categoryOptions = computed(() => ({
  chart: {
    type: 'donut',
    fontFamily: 'inherit'
  },
  labels: categoryLabels,
  colors: ['#f97316', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280'],
  plotOptions: {
    pie: {
      donut: {
        size: '65%',
        labels: {
          show: true,
          total: {
            show: true,
            label: '总支出',
            formatter: () => '¥3,245'
          }
        }
      }
    }
  },
  dataLabels: { enabled: false },
  legend: {
    position: 'bottom',
    labels: { colors: 'hsl(var(--bc))' }
  },
  tooltip: {
    theme: 'dark',
    y: { formatter: (value) => value + '%' }
  }
}))

// 筛选变化时更新数据
const onFilterChange = () => {
  // TODO: 调用 API 获取新数据
  console.log('筛选:', selectedYear.value, selectedMonth.value)
}

onMounted(() => {
  // 这里将来调用 fetchStats()
})
</script>

<template>
  <div class="p-4">
    <!-- 页面标题 + 时间筛选 -->
    <div class="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold">Dashboard</h1>
        <p class="text-sm opacity-60 mt-1">数据概览与统计</p>
      </div>
      <div class="flex gap-2">
        <select v-model="selectedYear" @change="onFilterChange" class="select select-bordered select-sm">
          <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
        </select>
        <select v-model="selectedMonth" @change="onFilterChange" class="select select-bordered select-sm">
          <option v-for="month in months" :key="month" :value="month">{{ month }}月</option>
        </select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="grid gap-3 sm:gap-4 mb-6" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
      <div v-for="(stat, index) in stats" :key="index" class="stat bg-base-200 rounded-box">
        <!-- 图标 -->
        <div class="stat-figure" :class="stat.type === 'expense' ? 'text-error' : stat.type === 'income' ? 'text-success' : 'text-primary'">
          <!-- 支出图标 -->
          <svg v-if="stat.icon === 'expense'" xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <!-- 收入图标 -->
          <svg v-else-if="stat.icon === 'income'" xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <!-- 结余图标 -->
          <svg v-else-if="stat.icon === 'balance'" xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
          </svg>
          <!-- 账单数图标 -->
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <!-- 标题 -->
        <div class="stat-title opacity-70">{{ stat.title }}</div>
        <!-- 数值 -->
        <div class="stat-value text-2xl">{{ stat.value }}</div>
        <!-- 描述 -->
        <div class="stat-desc">
          <span :class="{
            'text-success': stat.type === 'income',
            'text-error': stat.type === 'expense',
            'text-info': stat.type === 'balance',
            'text-base-content': stat.type === 'neutral'
          }">
            {{ stat.desc }}
          </span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid gap-4 lg:grid-cols-2">
      <!-- 收支趋势图 -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title text-lg">收支趋势</h2>
          <VueApexCharts
            type="area"
            height="300"
            :options="trendOptions"
            :series="trendSeries"
          />
        </div>
      </div>

      <!-- 分类支出图 -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title text-lg">支出分类</h2>
          <VueApexCharts
            type="donut"
            height="300"
            :options="categoryOptions"
            :series="categorySeries"
          />
        </div>
      </div>
    </div>
  </div>
</template>

