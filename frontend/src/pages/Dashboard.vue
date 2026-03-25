<script setup>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import TimeFilter from '../components/TimeFilter.vue'
import dayjs from 'dayjs'
import { getCurrentTheme } from '../utils/theme'
import { API_BASE } from '../config'

const bills = ref([])
const isLoading = ref(false)

const stats = ref([
  { title: '期间支出', value: '¥0', desc: '暂无数据', icon: 'expense', trend: 'neutral', type: 'expense' },
  { title: '期间收入', value: '¥0', desc: '暂无数据', icon: 'income', trend: 'neutral', type: 'income' },
  { title: '期间结余', value: '¥0', desc: '结余率 0%', icon: 'balance', trend: 'neutral', type: 'balance' },
  { title: '账单笔数', value: '0', desc: '暂无数据', icon: 'count', trend: 'neutral', type: 'neutral' },
])

const trendSeries = ref([
  { name: '收入', data: [] },
  { name: '支出', data: [] }
])

const trendCategories = ref([])

const categoryType = ref('expense')
const expenseSeries = ref([])
const expenseLabels = ref([])
const incomeSeries = ref([])
const incomeLabels = ref([])
const totalExpense = ref(0)
const totalIncome = ref(0)

const comparisonSeries = ref([
  { name: '收入', data: [] },
  { name: '支出', data: [] }
])
const comparisonCategories = ref([])

const currentTheme = ref(getCurrentTheme())

const getTextColor = () => currentTheme.value === 'dark' ? '#ffffff' : '#1f2937'

window.addEventListener('themechange', (e) => {
  currentTheme.value = e.detail.theme
})

const categorySeries = computed(() => categoryType.value === 'expense' ? expenseSeries.value : incomeSeries.value)
const categoryLabels = computed(() => categoryType.value === 'expense' ? expenseLabels.value : incomeSeries.value)

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
        style: { colors: Array(50).fill(textColor) },
        rotate: 0,
        hideOverlappingLabels: true,
        trim: false,
        formatter: (value) => value || ''
      }
    },
    yaxis: {
      labels: {
        style: { colors: Array(50).fill(textColor) },
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
      x: { formatter: (value, { dataPointIndex }) => trendCategories.value[dataPointIndex] || value },
      y: { formatter: (value) => '¥' + value.toLocaleString() }
    }
  }
})

const categoryOptions = computed(() => {
  const textColor = getTextColor()
  return {
    chart: { type: 'donut', fontFamily: 'inherit' },
    labels: categoryLabels.value,
    colors: categoryType.value === 'expense'
      ? ['#f97316', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#10b981', '#f59e0b', '#06b6d4']
      : ['#22c55e', '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#f59e0b', '#06b6d4'],
    plotOptions: {
      pie: {
        donut: {
          size: '65%',
          labels: {
            show: true,
            name: { show: true, color: textColor },
            value: { show: true, color: textColor },
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
    legend: { position: 'bottom', labels: { colors: textColor } },
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
  }
})

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
      bar: { horizontal: false, columnWidth: '60%', borderRadius: 4 }
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
  }
})

const fetchBills = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE}/bills`)
    if (response.ok) {
      bills.value = await response.json()
    }
  } catch (error) {
    console.error('获取账单失败:', error)
  } finally {
    isLoading.value = false
  }
}

const onTimeFilterChange = (data) => {
  console.log('筛选变化:', data)
  processBillsData(data.type, data.range)
}

const processBillsData = (filterType, range) => {
  const start = dayjs(range.start)
  const end = dayjs(range.end)
  
  const filteredBills = bills.value.filter(bill => {
    const billDate = dayjs(bill.date)
    return billDate.isAfter(start.subtract(1, 'day')) && billDate.isBefore(end.add(1, 'day'))
  })
  
  const periodExpense = filteredBills.filter(b => b.amount < 0).reduce((sum, b) => sum + Math.abs(b.amount), 0)
  const periodIncome = filteredBills.filter(b => b.amount >= 0).reduce((sum, b) => sum + b.amount, 0)
  const periodBalance = periodIncome - periodExpense
  const billCount = filteredBills.length
  
  const prevStart = start.subtract(end.diff(start, 'day') + 1, 'day')
  const prevEnd = start.subtract(1, 'day')
  const prevBills = bills.value.filter(bill => {
    const billDate = dayjs(bill.date)
    return billDate.isAfter(prevStart.subtract(1, 'day')) && billDate.isBefore(prevEnd.add(1, 'day'))
  })
  const prevExpense = prevBills.filter(b => b.amount < 0).reduce((sum, b) => sum + Math.abs(b.amount), 0)
  const prevIncome = prevBills.filter(b => b.amount >= 0).reduce((sum, b) => sum + b.amount, 0)
  
  const expenseChange = prevExpense > 0 ? ((periodExpense - prevExpense) / prevExpense * 100).toFixed(0) : 0
  const incomeChange = prevIncome > 0 ? ((periodIncome - prevIncome) / prevIncome * 100).toFixed(0) : 0
  
  stats.value = [
    { 
      title: '期间支出', 
      value: `¥${periodExpense.toLocaleString()}`, 
      desc: prevExpense > 0 ? `较上期 ${expenseChange >= 0 ? '+' : ''}${expenseChange}%` : '暂无对比数据',
      icon: 'expense', 
      trend: expenseChange >= 0 ? 'up' : 'down', 
      type: 'expense' 
    },
    { 
      title: '期间收入', 
      value: `¥${periodIncome.toLocaleString()}`, 
      desc: prevIncome > 0 ? `较上期 ${incomeChange >= 0 ? '+' : ''}${incomeChange}%` : '暂无对比数据',
      icon: 'income', 
      trend: incomeChange >= 0 ? 'up' : 'down', 
      type: 'income' 
    },
    { 
      title: '期间结余', 
      value: `¥${periodBalance.toLocaleString()}`, 
      desc: `结余率 ${periodIncome > 0 ? ((periodBalance / periodIncome) * 100).toFixed(0) : 0}%`,
      icon: 'balance', 
      trend: 'neutral', 
      type: 'balance' 
    },
    { 
      title: '账单笔数', 
      value: String(billCount), 
      desc: `筛选自 ${filteredBills.length} 条`,
      icon: 'count', 
      trend: 'neutral', 
      type: 'neutral' 
    },
  ]
  
  generateTrendData(filteredBills, filterType, start, end)
  generateCategoryData(filteredBills)
  generateComparisonData(filterType, start, end)
}

const generateTrendData = (filteredBills, filterType, start, end) => {
  const days = end.diff(start, 'day') + 1
  const dailyData = {}
  
  trendCategories.value = []
  
  if (filterType === '周报') {
    for (let i = 0; i < 7; i++) {
      const date = start.add(i, 'day')
      const key = date.format('YYYY-MM-DD')
      dailyData[key] = { income: 0, expense: 0 }
      trendCategories.value.push(date.format('ddd'))
    }
  } else if (filterType === '月报') {
    for (let i = 0; i < days && i <= 31; i++) {
      const date = start.add(i, 'day')
      const key = date.format('YYYY-MM-DD')
      dailyData[key] = { income: 0, expense: 0 }
      const dayNum = date.date()
      trendCategories.value.push(dayNum % 3 === 1 || i === days - 1 ? String(dayNum) : '')
    }
  } else if (filterType === '季报' || filterType === '年报') {
    const monthCount = filterType === '季报' ? 3 : 12
    for (let i = 0; i < monthCount; i++) {
      const month = start.month() + i
      const key = `month-${month}`
      dailyData[key] = { income: 0, expense: 0 }
      trendCategories.value.push(`${(month % 12) + 1}月`)
    }
  } else {
    for (let i = 0; i < days && i <= 31; i++) {
      const date = start.add(i, 'day')
      const key = date.format('YYYY-MM-DD')
      dailyData[key] = { income: 0, expense: 0 }
      trendCategories.value.push(i % 3 === 0 || i === days - 1 ? date.format('MM-DD') : '')
    }
  }
  
  filteredBills.forEach(bill => {
    let key
    if (filterType === '季报' || filterType === '年报') {
      const month = dayjs(bill.date).month()
      key = `month-${month}`
    } else {
      key = bill.date
    }
    
    if (dailyData[key]) {
      if (bill.amount >= 0) {
        dailyData[key].income += bill.amount
      } else {
        dailyData[key].expense += Math.abs(bill.amount)
      }
    }
  })
  
  const incomeData = []
  const expenseData = []
  
  Object.keys(dailyData).forEach(key => {
    incomeData.push(dailyData[key].income)
    expenseData.push(dailyData[key].expense)
  })
  
  trendSeries.value = [
    { name: '收入', data: incomeData },
    { name: '支出', data: expenseData }
  ]
}

const generateCategoryData = (filteredBills) => {
  const expenseByCategory = {}
  const incomeByCategory = {}
  
  filteredBills.forEach(bill => {
    const category = bill.category || '其他'
    if (bill.amount < 0) {
      expenseByCategory[category] = (expenseByCategory[category] || 0) + Math.abs(bill.amount)
    } else {
      incomeByCategory[category] = (incomeByCategory[category] || 0) + bill.amount
    }
  })
  
  const sortedExpense = Object.entries(expenseByCategory).sort((a, b) => b[1] - a[1])
  const sortedIncome = Object.entries(incomeByCategory).sort((a, b) => b[1] - a[1])
  
  const totalExp = sortedExpense.reduce((sum, [, val]) => sum + val, 0)
  const totalInc = sortedIncome.reduce((sum, [, val]) => sum + val, 0)
  
  expenseLabels.value = sortedExpense.map(([label]) => label)
  expenseSeries.value = sortedExpense.map(([, value]) => totalExp > 0 ? Math.round((value / totalExp) * 100) : 0)
  totalExpense.value = totalExp
  
  incomeLabels.value = sortedIncome.map(([label]) => label)
  incomeSeries.value = sortedIncome.map(([, value]) => totalInc > 0 ? Math.round((value / totalInc) * 100) : 0)
  totalIncome.value = totalInc
}

const generateComparisonData = (filterType, start, end) => {
  const periods = []
  const days = end.diff(start, 'day') + 1
  
  if (filterType === '周报') {
    for (let i = 3; i >= 0; i--) {
      const periodStart = start.subtract(i * 7, 'day')
      const periodEnd = periodStart.add(6, 'day')
      periods.push({
        label: i === 0 ? '本周' : `前${i}周`,
        start: periodStart,
        end: periodEnd
      })
    }
  } else if (filterType === '月报') {
    const currentMonth = start.month()
    for (let i = 3; i >= 0; i--) {
      const month = currentMonth - i
      const periodStart = start.subtract(i, 'month').startOf('month')
      const periodEnd = periodStart.endOf('month')
      periods.push({
        label: `${(month + 12) % 12 + 1}月`,
        start: periodStart,
        end: periodEnd
      })
    }
  } else if (filterType === '季报') {
    const quarterNames = ['第一季度', '第二季度', '第三季度', '第四季度']
    const currentQuarter = Math.floor(start.month() / 3)
    for (let i = 3; i >= 0; i--) {
      const q = (currentQuarter - i + 4) % 4
      periods.push({
        label: quarterNames[q],
        start: start.startOf('year').add(q * 3, 'month'),
        end: start.startOf('year').add((q + 1) * 3 - 1, 'month').endOf('month')
      })
    }
  } else if (filterType === '年报') {
    const currentYear = start.year()
    for (let i = 3; i >= 0; i--) {
      const year = currentYear - i
      periods.push({
        label: `${year}年`,
        start: dayjs(`${year}-01-01`),
        end: dayjs(`${year}-12-31`)
      })
    }
  } else {
    if (days <= 14) {
      const dayCount = Math.min(days, 7)
      for (let i = dayCount - 1; i >= 0; i--) {
        const periodStart = start.subtract(i, 'day')
        periods.push({
          label: periodStart.format('MM-DD'),
          start: periodStart,
          end: periodStart
        })
      }
    } else if (days <= 60) {
      const weekCount = Math.min(Math.ceil(days / 7), 6)
      for (let i = weekCount - 1; i >= 0; i--) {
        const periodStart = start.subtract(i * 7, 'day')
        periods.push({
          label: `第${weekCount - i}周`,
          start: periodStart,
          end: periodStart.add(6, 'day')
        })
      }
    } else {
      const monthCount = Math.min(Math.ceil(days / 30), 6)
      for (let i = monthCount - 1; i >= 0; i--) {
        const periodStart = start.subtract(i, 'month').startOf('month')
        periods.push({
          label: periodStart.format('M月'),
          start: periodStart,
          end: periodStart.endOf('month')
        })
      }
    }
  }
  
  comparisonCategories.value = periods.map(p => p.label)
  const incomeData = []
  const expenseData = []
  
  periods.forEach(period => {
    const periodBills = bills.value.filter(bill => {
      const billDate = dayjs(bill.date)
      return billDate.isAfter(period.start.subtract(1, 'day')) && billDate.isBefore(period.end.add(1, 'day'))
    })
    
    const income = periodBills.filter(b => b.amount >= 0).reduce((sum, b) => sum + b.amount, 0)
    const expense = periodBills.filter(b => b.amount < 0).reduce((sum, b) => sum + Math.abs(b.amount), 0)
    
    incomeData.push(income)
    expenseData.push(expense)
  })
  
  comparisonSeries.value = [
    { name: '收入', data: incomeData },
    { name: '支出', data: expenseData }
  ]
}

onMounted(async () => {
  await fetchBills()
})
</script>

<template>
  <div class="p-6 lg:p-8 max-w-[1600px] mx-auto">
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight">Dashboard</h1>
      <p class="text-sm text-base-content/60 mt-2 font-medium">数据概览与统计</p>
    </div>

    <div v-if="isLoading" class="py-20 text-center">
      <svg class="w-10 h-10 mx-auto animate-spin text-primary" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-sm text-base-content/40 mt-4">加载数据中...</p>
    </div>

    <div v-else-if="bills.length === 0" class="py-20 text-center">
      <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-base-200/50 flex items-center justify-center">
        <svg class="w-10 h-10 text-base-content/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <p class="text-lg font-medium text-base-content/60">暂无账单数据</p>
      <p class="text-sm text-base-content/40 mt-2">请先在「账单」页面导入账单文件</p>
    </div>

    <template v-else>
      <TimeFilter @change="onTimeFilterChange" />

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
            <div class="flex items-start justify-between mb-4">
              <div class="w-14 h-14 rounded-2xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110" :class="{
                'bg-gradient-to-br from-error/20 to-error/5 text-error': stat.type === 'expense',
                'bg-gradient-to-br from-success/20 to-success/5 text-success': stat.type === 'income',
                'bg-gradient-to-br from-info/20 to-info/5 text-info': stat.type === 'balance',
                'bg-gradient-to-br from-primary/20 to-primary/5 text-primary': stat.type === 'neutral'
              }">
                <svg v-if="stat.icon === 'expense'" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <svg v-else-if="stat.icon === 'income'" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <svg v-else-if="stat.icon === 'balance'" xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-7 w-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              
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
            
            <div class="text-sm font-medium text-base-content/60 mb-2">{{ stat.title }}</div>
            <div class="text-3xl font-bold tracking-tight mb-2">{{ stat.value }}</div>
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

      <div class="grid gap-6">
        <div class="grid gap-6 lg:grid-cols-2">
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
              
              <div v-if="categorySeries.length === 0" class="py-10 text-center text-base-content/40">
                暂无{{ categoryType === 'expense' ? '支出' : '收入' }}数据
              </div>
              <VueApexCharts
                v-else
                type="donut"
                height="250"
                :options="categoryOptions"
                :series="categorySeries"
              />
            </div>
          </div>
        </div>

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
    </template>
  </div>
</template>
