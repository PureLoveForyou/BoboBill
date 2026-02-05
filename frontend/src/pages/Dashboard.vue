<script setup>
import { ref, onMounted } from 'vue'

// 统计卡片数据（预留 API 接口）
const stats = ref([
  { title: '本月支出', value: '¥3,245', desc: '较上月 +5%', icon: 'expense', trend: 'up', type: 'expense' },
  { title: '本月收入', value: '¥12,000', desc: '较上月 +8%', icon: 'income', trend: 'up', type: 'income' },
  { title: '本月结余', value: '¥8,755', desc: '结余率 73%', icon: 'balance', trend: 'neutral', type: 'balance' },
  { title: '账单笔数', value: '46', desc: '较上月 +12%', icon: 'count', trend: 'up', type: 'neutral' },
])

// TODO: 后端 API 实现后，替换为真实数据
// const fetchStats = async () => {
//   const response = await fetch('/api/dashboard/stats')
//   const data = await response.json()
//   stats.value = data
// }

onMounted(() => {
  // 这里将来调用 fetchStats()
})
</script>

<template>
  <div class="p-4">
    <!-- 页面标题 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <p class="text-sm opacity-60 mt-1">数据概览与统计</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid gap-3 sm:gap-4" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
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
  </div>
</template>