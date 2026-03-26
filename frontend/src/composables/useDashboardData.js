import { ref, computed } from 'vue'
import dayjs from 'dayjs'

export function useDashboardData({ bills, selectedCategory, selectedPlatform }) {
  const stats = ref([
    { title: '期间支出', value: '¥0', desc: '暂无数据', type: 'expense', trend: 'neutral', change: 0 },
    { title: '期间收入', value: '¥0', desc: '暂无数据', type: 'income', trend: 'neutral', change: 0 },
    { title: '期间结余', value: '¥0', desc: '结余率 0%', type: 'balance', trend: 'neutral', change: 0 },
    { title: '账单笔数', value: '0', desc: '暂无数据', type: 'count', trend: 'neutral', change: 0 },
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

  const pieSelectedCategory = ref(null)

  const categorySeries = computed(() => categoryType.value === 'expense' ? expenseSeries.value : incomeSeries.value)
  const categoryLabels = computed(() => categoryType.value === 'expense' ? expenseLabels.value : incomeLabels.value)

  const processBillsData = (filterType, range) => {
    const start = dayjs(range.start)
    const end = dayjs(range.end)

    let filteredBills = bills.value.filter(bill => {
      const billDate = dayjs(bill.date)
      return billDate.isAfter(start.subtract(1, 'day')) && billDate.isBefore(end.add(1, 'day'))
    })

    if (selectedCategory.value !== 'all') {
      filteredBills = filteredBills.filter(bill => (bill.category || '其他') === selectedCategory.value)
    }
    if (selectedPlatform.value !== 'all') {
      filteredBills = filteredBills.filter(bill => bill.platform === selectedPlatform.value)
    }

    const periodExpense = filteredBills.filter(b => b.amount < 0).reduce((sum, b) => sum + Math.abs(b.amount), 0)
    const periodIncome = filteredBills.filter(b => b.amount >= 0).reduce((sum, b) => sum + b.amount, 0)
    const periodBalance = periodIncome - periodExpense
    const billCount = filteredBills.length

    const prevStart = start.subtract(end.diff(start, 'day') + 1, 'day')
    const prevEnd = start.subtract(1, 'day')
    let prevBills = bills.value.filter(bill => {
      const billDate = dayjs(bill.date)
      return billDate.isAfter(prevStart.subtract(1, 'day')) && billDate.isBefore(prevEnd.add(1, 'day'))
    })

    if (selectedCategory.value !== 'all') {
      prevBills = prevBills.filter(bill => (bill.category || '其他') === selectedCategory.value)
    }
    if (selectedPlatform.value !== 'all') {
      prevBills = prevBills.filter(bill => bill.platform === selectedPlatform.value)
    }

    const prevExpense = prevBills.filter(b => b.amount < 0).reduce((sum, b) => sum + Math.abs(b.amount), 0)
    const prevIncome = prevBills.filter(b => b.amount >= 0).reduce((sum, b) => sum + b.amount, 0)

    const expenseChange = prevExpense > 0 ? ((periodExpense - prevExpense) / prevExpense * 100).toFixed(0) : 0
    const incomeChange = prevIncome > 0 ? ((periodIncome - prevIncome) / prevIncome * 100).toFixed(0) : 0

    stats.value = [
      { title: '期间支出', value: `¥${periodExpense.toLocaleString()}`, desc: prevExpense > 0 ? `${expenseChange >= 0 ? '+' : ''}${expenseChange}%` : '-', type: 'expense', trend: expenseChange >= 0 ? 'up' : 'down', change: expenseChange },
      { title: '期间收入', value: `¥${periodIncome.toLocaleString()}`, desc: prevIncome > 0 ? `${incomeChange >= 0 ? '+' : ''}${incomeChange}%` : '-', type: 'income', trend: incomeChange >= 0 ? 'up' : 'down', change: incomeChange },
      { title: '期间结余', value: `¥${periodBalance.toLocaleString()}`, desc: `结余率 ${periodIncome > 0 ? ((periodBalance / periodIncome) * 100).toFixed(0) : 0}%`, type: 'balance', trend: 'neutral', change: 0 },
      { title: '账单笔数', value: String(billCount), desc: `${filteredBills.length}条`, type: 'count', trend: 'neutral', change: 0 },
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
        dailyData[date.format('YYYY-MM-DD')] = { income: 0, expense: 0 }
        trendCategories.value.push(date.format('ddd'))
      }
    } else if (filterType === '月报') {
      for (let i = 0; i < days && i <= 31; i++) {
        const date = start.add(i, 'day')
        dailyData[date.format('YYYY-MM-DD')] = { income: 0, expense: 0 }
        const dayNum = date.date()
        trendCategories.value.push(dayNum % 3 === 1 || i === days - 1 ? String(dayNum) : '')
      }
    } else if (filterType === '季报' || filterType === '年报') {
      const monthCount = filterType === '季报' ? 3 : 12
      for (let i = 0; i < monthCount; i++) {
        const month = start.month() + i
        dailyData[`month-${month}`] = { income: 0, expense: 0 }
        trendCategories.value.push(`${(month % 12) + 1}月`)
      }
    } else {
      for (let i = 0; i < days && i <= 31; i++) {
        const date = start.add(i, 'day')
        dailyData[date.format('YYYY-MM-DD')] = { income: 0, expense: 0 }
        trendCategories.value.push(i % 3 === 0 || i === days - 1 ? date.format('MM-DD') : '')
      }
    }

    filteredBills.forEach(bill => {
      const key = (filterType === '季报' || filterType === '年报')
        ? `month-${dayjs(bill.date).month()}`
        : bill.date
      if (dailyData[key]) {
        if (bill.amount >= 0) dailyData[key].income += bill.amount
        else dailyData[key].expense += Math.abs(bill.amount)
      }
    })

    const incomeData = []
    const expenseData = []
    Object.keys(dailyData).forEach(key => {
      incomeData.push(dailyData[key].income)
      expenseData.push(dailyData[key].expense)
    })
    trendSeries.value = [{ name: '收入', data: incomeData }, { name: '支出', data: expenseData }]
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
        periods.push({ label: i === 0 ? '本周' : `前${i}周`, start: periodStart, end: periodStart.add(6, 'day') })
      }
    } else if (filterType === '月报') {
      const currentMonth = start.month()
      for (let i = 3; i >= 0; i--) {
        const periodStart = start.subtract(i, 'month').startOf('month')
        periods.push({ label: `${(currentMonth - i + 12) % 12 + 1}月`, start: periodStart, end: periodStart.endOf('month') })
      }
    } else if (filterType === '季报') {
      const quarterNames = ['Q1', 'Q2', 'Q3', 'Q4']
      const currentQuarter = Math.floor(start.month() / 3)
      for (let i = 3; i >= 0; i--) {
        const q = (currentQuarter - i + 4) % 4
        periods.push({ label: quarterNames[q], start: start.startOf('year').add(q * 3, 'month'), end: start.startOf('year').add((q + 1) * 3 - 1, 'month').endOf('month') })
      }
    } else if (filterType === '年报') {
      const currentYear = start.year()
      for (let i = 3; i >= 0; i--) {
        const year = currentYear - i
        periods.push({ label: `${year}年`, start: dayjs(`${year}-01-01`), end: dayjs(`${year}-12-31`) })
      }
    } else {
      if (days <= 14) {
        const dayCount = Math.min(days, 7)
        for (let i = dayCount - 1; i >= 0; i--) {
          const periodStart = start.subtract(i, 'day')
          periods.push({ label: periodStart.format('MM-DD'), start: periodStart, end: periodStart })
        }
      } else if (days <= 60) {
        const weekCount = Math.min(Math.ceil(days / 7), 6)
        for (let i = weekCount - 1; i >= 0; i--) {
          const periodStart = start.subtract(i * 7, 'day')
          periods.push({ label: `第${weekCount - i}周`, start: periodStart, end: periodStart.add(6, 'day') })
        }
      } else {
        const monthCount = Math.min(Math.ceil(days / 30), 6)
        for (let i = monthCount - 1; i >= 0; i--) {
          const periodStart = start.subtract(i, 'month').startOf('month')
          periods.push({ label: periodStart.format('M月'), start: periodStart, end: periodStart.endOf('month') })
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
      incomeData.push(periodBills.filter(b => b.amount >= 0).reduce((sum, b) => sum + b.amount, 0))
      expenseData.push(periodBills.filter(b => b.amount < 0).reduce((sum, b) => sum + Math.abs(b.amount), 0))
    })

    comparisonSeries.value = [{ name: '收入', data: incomeData }, { name: '支出', data: expenseData }]
  }

  const clearPieFilter = () => {
    pieSelectedCategory.value = null
  }

  return {
    stats, trendSeries, trendCategories,
    categoryType, categorySeries, categoryLabels,
    pieSelectedCategory, clearPieFilter,
    expenseLabels, incomeLabels, totalExpense, totalIncome,
    comparisonSeries, comparisonCategories,
    processBillsData
  }
}
