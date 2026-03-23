<script setup>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import TimeFilter from '../components/TimeFilter.vue'
import dayjs from 'dayjs'
import { getCurrentTheme } from '../utils/theme'

// 统计卡片数据（预留 API 接口）
const stats = ref([
  { title: '期间支出', value: '¥3,245', desc: '较上期 +5%', icon: 'expense', trend: 'up', type: 'expense' },
  { title: '期间收入', value: '¥12,000', desc: '较上期 +8%', icon: 'income', trend: 'up', type: 'income' },
  { title: '期间结余', value: '¥8,755', desc: '结余率 73%', icon: 'balance', trend: 'neutral', type: 'balance' },
  { title: '账单笔数', value: '46', desc: '较上期 +12%', icon: 'count', trend: 'up', type: 'neutral' },
])

// 收支趋势图配置
const trendSeries = ref([
  { name: '收入', data: [] },
  { name: '支出', data: [] }
])

const trendOptions = computed(() => {
  const textColor = getTextColor()
  return {
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
    categories: trendCategories.value,
    labels: {
      style: {
        colors: Array(50).fill(textColor)
      },
      rotate: 0,
      hideOverlappingLabels: true,
      trim: false,
      formatter: (value) => value || ''  // 过滤空字符串
    }
  },
  yaxis: {
    labels: {
      style: {
        colors: Array(50).fill(textColor)
      },
      formatter: (value) => '¥' + (value / 1000) + 'k'
    }
  },
  grid: { borderColor: currentTheme.value === 'dark' ? '#374151' : '#e5e7eb', padding: { top: 0 } },
  legend: {
    labels: { colors: textColor },
    position: 'top',
    horizontalAlign: 'right',
    offsetY: -5,
    itemMargin: { horizontal: 15 }
  },
  tooltip: {
    theme: 'dark',
    x: {
      formatter: (value, { dataPointIndex }) => trendCategories.value[dataPointIndex] || value
    },
    y: { formatter: (value) => '¥' + value.toLocaleString() }
  }
}})

// 趋势图X轴标签
const trendCategories = ref([])

// 分类统计类型（支出/收入）
const categoryType = ref('expense')

// 分类支出图数据（支出）
const expenseSeries = ref([])
const expenseLabels = ref([])

// 分类收入图数据（收入）
const incomeSeries = ref([])
const incomeLabels = ref([])

// 当前显示的系列和标签（根据categoryType切换）
const categorySeries = computed(() => categoryType.value === 'expense' ? expenseSeries.value : incomeSeries.value)
const categoryLabels = computed(() => categoryType.value === 'expense' ? expenseLabels.value : incomeLabels.value)
const totalExpense = ref(0)
const totalIncome = ref(0)

const categoryOptions = computed(() => {
  const textColor = getTextColor()
  return {
  chart: {
    type: 'donut',
    fontFamily: 'inherit'
  },
  labels: categoryLabels.value,
  colors: categoryType.value === 'expense'
    ? ['#f97316', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#10b981', '#f59e0b']
    : ['#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#f59e0b', '#06b6d4'],
  plotOptions: {
    pie: {
      donut: {
        size: '65%',
        labels: {
          show: true,
          name: {
            show: true,
            color: textColor
          },
          value: {
            show: true,
            color: textColor
          },
          total: {
            show: true,
            label: categoryType.value === 'expense' ? '总支出' : '总收入',
            color: textColor,
            formatter: () => '¥' + (categoryType.value === 'expense' ? totalExpense.value : totalIncome.value).toLocaleString()
          }
        }
      }
    }
  },
  dataLabels: { enabled: false },
  legend: {
    position: 'bottom',
    labels: { colors: textColor }
  },
  tooltip: {
    theme: 'dark',
    y: {
      formatter: (value) => {
        const total = categorySeries.value.reduce((a, b) => a + b, 0)
        const percent = ((value / total) * 100).toFixed(1)
        return `${value}% (¥${Math.round(total * value / 100).toLocaleString()})`
      }
    }
  }
}})

// 柱状图配置（对比图）
const comparisonSeries = ref([
  { name: '收入', data: [] },
  { name: '支出', data: [] }
])

const comparisonOptions = computed(() => {
  const textColor = getTextColor()
  return {
  chart: {
    type: 'bar',
    fontFamily: 'inherit',
    toolbar: { show: false },
    animations: { enabled: true }
  },
  colors: ['#22c55e', '#ef4444'],
  plotOptions: {
    bar: {
      horizontal: false,
      columnWidth: '60%',
      borderRadius: 4
    }
  },
  dataLabels: { enabled: false },
  xaxis: {
    categories: comparisonCategories.value,
    labels: { style: { colors: Array(50).fill(textColor) } }
  },
  yaxis: {
    labels: {
      style: { colors: Array(50).fill(textColor) },
      formatter: (value) => '¥' + (value / 1000) + 'k'
    }
  },
  grid: { borderColor: currentTheme.value === 'dark' ? '#374151' : '#e5e7eb' },
  legend: {
    labels: { colors: textColor },
    position: 'top',
    horizontalAlign: 'right',
    offsetY: -5,
    itemMargin: { horizontal: 15 }
  },
  tooltip: {
    theme: 'dark',
    y: { formatter: (value) => '¥' + value.toLocaleString() }
  }
}})

const comparisonCategories = ref([])

// 当前主题
const currentTheme = ref(getCurrentTheme())

// 获取文本颜色（根据主题）
const getTextColor = () => currentTheme.value === 'dark' ? '#ffffff' : '#1f2937'

// 监听主题变化
window.addEventListener('themechange', (e) => {
  currentTheme.value = e.detail.theme
})

// 时间筛选变化处理
const onTimeFilterChange = (data) => {
  console.log('筛选变化:', data)

  // 生成模拟数据
  generateMockData(data.type, data.range)
}

// 生成模拟数据
const generateMockData = (type, range) => {
  const start = dayjs(range.start)
  const end = dayjs(range.end)
  const days = end.diff(start, 'day') + 1

  // 根据报表类型生成趋势图数据
  trendCategories.value = []
  const incomeData = []
  const expenseData = []

  if (type === '周报') {
    for (let i = 0; i < 7; i++) {
      const date = start.add(i, 'day')
      trendCategories.value.push(date.format('ddd'))
      incomeData.push(Math.floor(Math.random() * 5000 + 1000))
      expenseData.push(Math.floor(Math.random() * 2000 + 500))
    }
  } else if (type === '月报') {
    for (let i = 0; i < days && i <= 31; i++) {
      const date = start.add(i, 'day')
      const dayNum = date.date()
      // 间隔显示：每3天显示一次（1号、4号、7号、10号...）
      trendCategories.value.push(dayNum % 3 === 1 || dayNum === days ? String(dayNum) : '')
      incomeData.push(Math.floor(Math.random() * 5000 + 1000))
      expenseData.push(Math.floor(Math.random() * 2000 + 500))
    }
  } else if (type === '季报') {
    const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    const quarterMonths = type === '季报' ? 3 : 12
    for (let i = 0; i < quarterMonths; i++) {
      trendCategories.value.push(months[i])
      incomeData.push(Math.floor(Math.random() * 50000 + 30000))
      expenseData.push(Math.floor(Math.random() * 20000 + 10000))
    }
  } else if (type === '年报') {
    const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    for (let i = 0; i < 12; i++) {
      trendCategories.value.push(months[i])
      incomeData.push(Math.floor(Math.random() * 50000 + 30000))
      expenseData.push(Math.floor(Math.random() * 20000 + 10000))
    }
  } else if (type === '自定义') {
    for (let i = 0; i < days && i <= 31; i++) {
      const date = start.add(i, 'day')
      const dayNum = i + 1
      // 间隔显示，每3天显示一次
      trendCategories.value.push(dayNum % 3 === 1 || dayNum === days ? date.format('MM-DD') : '')
      incomeData.push(Math.floor(Math.random() * 5000 + 1000))
      expenseData.push(Math.floor(Math.random() * 2000 + 500))
    }
  }

  trendSeries.value = [
    { name: '收入', data: incomeData },
    { name: '支出', data: expenseData }
  ]

  // 生成分类支出数据
  const expenseCategories = ['餐饮', '交通', '购物', '娱乐', '其他', '医疗', '教育']
  const expenseCategoryData = expenseCategories.map(() => Math.floor(Math.random() * 20 + 5))
  expenseSeries.value = expenseCategoryData
  expenseLabels.value = expenseCategories
  totalExpense.value = Math.floor(Math.random() * 10000 + 5000)

  // 生成分类收入数据
  const incomeCategories = ['工资', '奖金', '投资收益', '兼职收入', '其他']
  const incomeCategoryData = incomeCategories.map(() => Math.floor(Math.random() * 30 + 10))
  incomeSeries.value = incomeCategoryData
  incomeLabels.value = incomeCategories
  totalIncome.value = incomeCategoryData.reduce((a, b) => a + b, 0) * 1000

  // 更新统计卡片
  stats.value = [
    { title: '期间支出', value: `¥${totalExpense.value.toLocaleString()}`, desc: '较上期 +5%', icon: 'expense', trend: 'up', type: 'expense' },
    { title: '期间收入', value: `¥${(incomeData.reduce((a, b) => a + b, 0)).toLocaleString()}`, desc: '较上期 +8%', icon: 'income', trend: 'up', type: 'income' },
    { title: '期间结余', value: `¥${(incomeData.reduce((a, b) => a + b, 0) - totalExpense.value).toLocaleString()}`, desc: '结余率 73%', icon: 'balance', trend: 'neutral', type: 'balance' },
    { title: '账单笔数', value: String(Math.floor(Math.random() * 50 + 20)), desc: '较上期 +12%', icon: 'count', trend: 'up', type: 'neutral' },
  ]

  // 根据报表类型生成周期对比数据
  if (type === '周报') {
    // 周报：显示最近几周对比
    generateComparisonData([
      { label: '前3周' }, { label: '前2周' }, { label: '上周' },
      { label: '本周' }
    ])
  } else if (type === '月报') {
    // 月报：显示最近几月对比
    const currentMonth = start.month() + 1 // 1-12
    const comparisons = []
    for (let i = 3; i >= 0; i--) {
      let month = currentMonth - i
      if (month <= 0) {
        month += 12
      }
      comparisons.push({ label: `${month}月` })
    }
    generateComparisonData(comparisons)
  } else if (type === '季报') {
    // 季报：显示季度对比
    const quarterNames = ['第一季度', '第二季度', '第三季度', '第四季度']
    generateComparisonData(quarterNames.map(q => ({ label: q })))
  } else if (type === '年报') {
    // 年报：显示最近几年对比
    const currentYear = start.year()
    generateComparisonData([
      { label: `${currentYear - 3}年` }, { label: `${currentYear - 2}年` },
      { label: `${currentYear - 1}年` }, { label: `${currentYear}年` }
    ])
  } else if (type === '自定义') {
    // 自定义范围：根据天数决定对比维度
    if (days <= 14) {
      // 14天以内：按天对比，最多显示7天
      const dayCount = Math.min(days, 7)
      const comparisons = []
      for (let i = dayCount; i >= 1; i--) {
        comparisons.push({ label: `前${i}天` })
      }
      generateComparisonData(comparisons)
    } else if (days <= 60) {
      // 60天以内：按周对比
      const weekCount = Math.min(Math.ceil(days / 7), 6)
      const comparisons = []
      for (let i = weekCount; i >= 1; i--) {
        comparisons.push({ label: `前${i}周` })
      }
      generateComparisonData(comparisons)
    } else {
      // 超过60天：按月对比
      const monthCount = Math.min(Math.ceil(days / 30), 6)
      const currentMonth = start.month() + 1
      const comparisons = []
      for (let i = monthCount - 1; i >= 0; i--) {
        let month = currentMonth - i
        if (month <= 0) {
          month += 12
        }
        comparisons.push({ label: `${month}月` })
      }
      generateComparisonData(comparisons)
    }
  }
}

// 生成对比数据
const generateComparisonData = (comparisons) => {
  comparisonCategories.value = comparisons.map(c => c.label)
  const incomeData = comparisons.map(() => Math.floor(Math.random() * 50000 + 30000))
  const expenseData = comparisons.map(() => Math.floor(Math.random() * 20000 + 10000))
  comparisonSeries.value = [
    { name: '收入', data: incomeData },
    { name: '支出', data: expenseData }
  ]
}

// 初始化
onMounted(() => {
  // 初始化时默认使用周报对比
  generateComparisonData([
    { label: '前3周' }, { label: '前2周' }, { label: '上周' },
    { label: '本周' }
  ])
})
</script>

<template>
  <div class="p-6 lg:p-8 max-w-[1600px] mx-auto">
    <!-- 页面标题 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight">Dashboard</h1>
      <p class="text-sm text-base-content/60 mt-2 font-medium">数据概览与统计</p>
    </div>

    <!-- 时间筛选 -->
    <TimeFilter @change="onTimeFilterChange" />

    <!-- 统计卡片 -->
    <div class="grid gap-5 my-8" style="grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));">
      <div 
        v-for="(stat, index) in stats" 
        :key="index" 
        class="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/50 border border-base-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-xl hover:shadow-base-300/20 hover:-translate-y-1"
      >
        <div class="absolute inset-0 bg-gradient-to-br opacity-5" :class="{
          'from-error to-error/50': stat.type === 'expense',
          'from-success to-success/50': stat.type === 'income',
          'from-info to-info/50': stat.type === 'balance',
          'from-primary to-primary/50': stat.type === 'neutral'
        }"></div>
        
        <div class="relative p-6">
          <!-- 图标 -->
          <div class="flex items-start justify-between mb-4">
            <div class="w-14 h-14 rounded-2xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110" :class="{
              'bg-gradient-to-br from-error/20 to-error/5 text-error': stat.type === 'expense',
              'bg-gradient-to-br from-success/20 to-success/5 text-success': stat.type === 'income',
              'bg-gradient-to-br from-info/20 to-info/5 text-info': stat.type === 'balance',
              'bg-gradient-to-br from-primary/20 to-primary/5 text-primary': stat.type === 'neutral'
            }">
              <!-- 支出图标 -->
              <svg v-if="stat.icon === 'expense'" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <!-- 收入图标 -->
              <svg v-else-if="stat.icon === 'income'" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <!-- 结余图标 -->
              <svg v-else-if="stat.icon === 'balance'" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
              </svg>
              <!-- 账单数图标 -->
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            
            <!-- 趋势指示器 -->
            <div v-if="stat.trend !== 'neutral'" class="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold" :class="{
              'bg-success/10 text-success': stat.type === 'income',
              'bg-error/10 text-error': stat.type === 'expense',
              'bg-info/10 text-info': stat.type === 'balance'
            }">
              <svg v-if="stat.trend === 'up'" class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
              <svg v-else class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          
          <!-- 标题 -->
          <div class="text-sm font-medium text-base-content/60 mb-2">{{ stat.title }}</div>
          
          <!-- 数值 -->
          <div class="text-3xl font-bold tracking-tight mb-2">{{ stat.value }}</div>
          
          <!-- 描述 -->
          <div class="text-sm font-medium" :class="{
            'text-success': stat.type === 'income',
            'text-error': stat.type === 'expense',
            'text-info': stat.type === 'balance',
            'text-base-content/60': stat.type === 'neutral'
          }">
            {{ stat.desc }}
          </div>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="grid gap-6">
      <!-- 上排：折线图 + 饼图 -->
      <div class="grid gap-6 lg:grid-cols-2">
        <!-- 收支趋势图 -->
        <div class="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/30 border border-base-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-xl hover:shadow-base-300/20">
          <div class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-bold tracking-tight">收支趋势</h2>
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center">
                <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
              </div>
            </div>
            <VueApexCharts
              type="area"
              height="300"
              :options="trendOptions"
              :series="trendSeries"
            />
          </div>
        </div>

        <!-- 分类统计图 -->
        <div class="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/30 border border-base-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-xl hover:shadow-base-300/20">
          <div class="p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-xl font-bold tracking-tight">分类统计</h2>
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center">
                <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                </svg>
              </div>
            </div>
            
            <!-- Tab 切换 -->
            <div class="flex gap-2 mb-6 p-1.5 bg-base-200/50 rounded-2xl">
              <button
                class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300"
                :class="categoryType === 'expense' 
                  ? 'bg-base-100 text-base-content shadow-sm' 
                  : 'text-base-content/60 hover:text-base-content'"
                @click="categoryType = 'expense'"
              >
                支出分类
              </button>
              <button
                class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300"
                :class="categoryType === 'income' 
                  ? 'bg-base-100 text-base-content shadow-sm' 
                  : 'text-base-content/60 hover:text-base-content'"
                @click="categoryType = 'income'"
              >
                收入分类
              </button>
            </div>
            
            <VueApexCharts
              type="donut"
              height="250"
              :options="categoryOptions"
              :series="categorySeries"
            />
          </div>
        </div>
      </div>

      <!-- 下排：柱状图对比 -->
      <div class="group relative overflow-hidden rounded-3xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/30 border border-base-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-xl hover:shadow-base-300/20">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold tracking-tight">周期对比</h2>
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/10 to-primary/5 flex items-center justify-center">
              <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
          </div>
          <VueApexCharts
            type="bar"
            height="300"
            :options="comparisonOptions"
            :series="comparisonSeries"
          />
        </div>
      </div>
    </div>
  </div>
</template>

