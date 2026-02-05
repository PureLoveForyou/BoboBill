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
  <div class="p-4">
    <!-- 页面标题 -->
    <div class="mb-4">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <p class="text-sm opacity-60 mt-1">数据概览与统计</p>
    </div>

    <!-- 时间筛选 -->
    <TimeFilter @change="onTimeFilterChange" />

    <!-- 统计卡片 -->
    <div class="grid gap-3 sm:gap-4 my-6" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
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
    <div class="grid gap-4">
      <!-- 上排：折线图 + 饼图 -->
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

        <!-- 分类统计图 -->
        <div class="card bg-base-200">
          <div class="card-body py-4">
            <!-- Tab 切换 -->
            <div class="tabs tabs-boxed mb-4">
              <a
                class="tab text-lg font-bold"
                :class="{ 'tab-active': categoryType === 'expense' }"
                @click="categoryType = 'expense'"
              >
                支出分类
              </a>
              <a
                class="tab text-lg font-bold"
                :class="{ 'tab-active': categoryType === 'income' }"
                @click="categoryType = 'income'"
              >
                收入分类
              </a>
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
      <div class="card bg-base-200">
        <div class="card-body">
          <h2 class="card-title text-lg">周期对比</h2>
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

