<script setup>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import TimeFilter from '../components/TimeFilter.vue'
import PlatformIcon from '../components/PlatformIcon.vue'
import AppleSelect from '../components/AppleSelect.vue'
import dayjs from 'dayjs'
import { getCurrentTheme } from '../utils/theme'
import { API_BASE } from '../config'

const bills = ref([])
const isLoading = ref(false)

const currentFilterType = ref('月报')
const currentRange = ref({ start: dayjs().startOf('month').format('YYYY-MM-DD'), end: dayjs().endOf('month').format('YYYY-MM-DD') })

const selectedCategory = ref('all')
const selectedPlatform = ref('all')
const categories = ['all', '餐饮', '交通', '购物', '工资', '投资', '娱乐', '医疗', '转账', '其他']
const platforms = ['all', 'wechat', 'alipay', 'bank']

const categoryOptions = computed(() => 
  categories.map(cat => ({
    value: cat,
    label: cat === 'all' ? '全部分类' : cat
  }))
)

const platformOptions = computed(() => 
  platforms.map(plat => ({
    value: plat,
    label: plat === 'all' ? '全部平台' : platformInfo[plat]?.name || plat
  }))
)

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

const currentTheme = ref(getCurrentTheme())

const pieSelectedCategory = ref(null)
const showBillList = ref(true)

const showImportModal = ref(false)
const importType = ref(null)
const isDragging = ref(false)
const uploadedFile = ref(null)
const isUploading = ref(false)
const uploadResult = ref(null)

const showAddModal = ref(false)
const showEditModal = ref(false)
const showDeleteModal = ref(false)
const isSaving = ref(false)
const deletingBill = ref(null)

const newBill = ref({
  name: '',
  amount: '',
  type: 'expense',
  date: new Date().toISOString().split('T')[0],
  category: '其他',
  platform: 'wechat',
  note: ''
})

const editingBill = ref({
  id: null,
  name: '',
  amount: '',
  type: 'expense',
  date: '',
  category: '其他',
  platform: 'wechat',
  note: ''
})

const toast = ref('')
const toastTimer = ref(null)
const showToast = (msg) => {
  toast.value = msg
  clearTimeout(toastTimer.value)
  toastTimer.value = setTimeout(() => { toast.value = '' }, 3000)
}

const getTextColor = () => currentTheme.value === 'dark' ? '#ffffff' : '#1f2937'

window.addEventListener('themechange', (e) => {
  currentTheme.value = e.detail.theme
})

const categorySeries = computed(() => categoryType.value === 'expense' ? expenseSeries.value : incomeSeries.value)
const categoryLabels = computed(() => categoryType.value === 'expense' ? expenseLabels.value : incomeLabels.value)

const platformInfo = {
  wechat: { name: '微信', color: 'from-green-500 to-green-600' },
  alipay: { name: '支付宝', color: 'from-blue-500 to-blue-600' },
  bank: { name: '银行卡', color: 'from-yellow-500 to-yellow-600' }
}

const filteredBillsByTime = computed(() => {
  const start = dayjs(currentRange.value.start)
  const end = dayjs(currentRange.value.end)
  
  return bills.value.filter(bill => {
    const billDate = dayjs(bill.date)
    return billDate.isAfter(start.subtract(1, 'day')) && billDate.isBefore(end.add(1, 'day'))
  })
})

const displayBills = computed(() => {
  let result = filteredBillsByTime.value
  
  if (selectedCategory.value !== 'all') {
    result = result.filter(bill => {
      const billCategory = bill.category || '其他'
      return billCategory === selectedCategory.value
    })
  }
  
  if (selectedPlatform.value !== 'all') {
    result = result.filter(bill => bill.platform === selectedPlatform.value)
  }
  
  if (pieSelectedCategory.value) {
    result = result.filter(bill => {
      const billCategory = bill.category || '其他'
      return billCategory === pieSelectedCategory.value
    })
  }
  
  return result.sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 20)
})

const formatAmount = (amount) => {
  const absAmount = Math.abs(amount)
  return amount >= 0 ? `+¥${absAmount.toFixed(2)}` : `-¥${absAmount.toFixed(2)}`
}

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

const categoryOptionsChart = computed(() => {
  const textColor = getTextColor()
  return {
    chart: { 
      type: 'donut', 
      fontFamily: 'inherit',
      events: {
        dataPointSelection: (event, chartContext, config) => {
          const labelIndex = config.dataPointIndex
          const labels = categoryType.value === 'expense' ? expenseLabels.value : incomeLabels.value
          if (labelIndex >= 0 && labelIndex < labels.length) {
            const clickedCategory = labels[labelIndex]
            if (pieSelectedCategory.value === clickedCategory) {
              pieSelectedCategory.value = null
            } else {
              pieSelectedCategory.value = clickedCategory
            }
          }
        }
      }
    },
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
  currentFilterType.value = data.type
  currentRange.value = data.range
  pieSelectedCategory.value = null
  processBillsData(data.type, data.range)
}

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
    { 
      title: '期间支出', 
      value: `¥${periodExpense.toLocaleString()}`, 
      desc: prevExpense > 0 ? `${expenseChange >= 0 ? '+' : ''}${expenseChange}%` : '-',
      type: 'expense',
      trend: expenseChange >= 0 ? 'up' : 'down',
      change: expenseChange
    },
    { 
      title: '期间收入', 
      value: `¥${periodIncome.toLocaleString()}`, 
      desc: prevIncome > 0 ? `${incomeChange >= 0 ? '+' : ''}${incomeChange}%` : '-',
      type: 'income',
      trend: incomeChange >= 0 ? 'up' : 'down',
      change: incomeChange
    },
    { 
      title: '期间结余', 
      value: `¥${periodBalance.toLocaleString()}`, 
      desc: `结余率 ${periodIncome > 0 ? ((periodBalance / periodIncome) * 100).toFixed(0) : 0}%`,
      type: 'balance',
      trend: 'neutral',
      change: 0
    },
    { 
      title: '账单笔数', 
      value: String(billCount), 
      desc: `${filteredBills.length}条`,
      type: 'count',
      trend: 'neutral',
      change: 0
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
    const quarterNames = ['Q1', 'Q2', 'Q3', 'Q4']
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

const clearPieFilter = () => {
  pieSelectedCategory.value = null
}

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = async (e) => {
  e.preventDefault()
  isDragging.value = false
  const files = e.dataTransfer.files
  if (files.length > 0) {
    uploadedFile.value = files[0]
    await detectPlatform()
  }
}

const handleFileSelect = async (e) => {
  if (e.target.files.length > 0) {
    uploadedFile.value = e.target.files[0]
    await detectPlatform()
  }
  e.target.value = ''
}

const detectPlatform = async () => {
  if (!uploadedFile.value) return
  
  const formData = new FormData()
  formData.append('file', uploadedFile.value)
  
  try {
    const response = await fetch(`${API_BASE}/bills/detect`, {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.platform && result.platform !== 'unknown') {
        importType.value = result.platform
      }
    }
  } catch (error) {
    console.error('检测平台失败:', error)
  }
}

const startImport = async () => {
  if (!uploadedFile.value || !importType.value) return
  
  isUploading.value = true
  uploadResult.value = null
  
  const formData = new FormData()
  formData.append('file', uploadedFile.value)
  formData.append('platform', importType.value)
  
  try {
    const response = await fetch(`${API_BASE}/bills/upload`, {
      method: 'POST',
      body: formData
    })
    
    const result = await response.json()
    
    if (response.ok) {
      uploadResult.value = {
        type: 'success',
        message: result.message
      }
      await fetchBills()
      uploadedFile.value = null
      importType.value = null
    } else {
      uploadResult.value = {
        type: 'error',
        message: result.detail || '导入失败，请检查文件格式'
      }
    }
  } catch (error) {
    uploadResult.value = {
      type: 'error',
      message: '网络错误，请确保后端服务已启动'
    }
    console.error('上传失败:', error)
  } finally {
    isUploading.value = false
  }
}

const openAddModal = () => {
  newBill.value = {
    name: '',
    amount: '',
    type: 'expense',
    date: new Date().toISOString().split('T')[0],
    category: '其他',
    platform: 'wechat',
    note: ''
  }
  showAddModal.value = true
}

const closeAddModal = () => {
  showAddModal.value = false
}

const saveBill = async () => {
  if (!newBill.value.name || !newBill.value.amount || !newBill.value.date) return
  
  isSaving.value = true
  
  try {
    const amount = parseFloat(newBill.value.amount)
    const billData = {
      name: newBill.value.name,
      amount: newBill.value.type === 'expense' ? -Math.abs(amount) : Math.abs(amount),
      type: newBill.value.type,
      date: newBill.value.date,
      category: newBill.value.category,
      platform: newBill.value.platform,
      note: newBill.value.note || ''
    }
    
    const response = await fetch(`${API_BASE}/bills`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(billData)
    })
    
    if (response.ok) {
      await fetchBills()
      closeAddModal()
      showToast('保存成功')
    } else {
      const result = await response.json()
      showToast('保存失败: ' + (result.detail || '未知错误'))
    }
  } catch (error) {
    console.error('保存失败:', error)
    showToast('无法连接服务器')
  } finally {
    isSaving.value = false
  }
}

const openEditModal = (bill) => {
  editingBill.value = {
    id: bill.id,
    name: bill.name,
    amount: Math.abs(bill.amount),
    type: bill.type || (bill.amount >= 0 ? 'income' : 'expense'),
    date: bill.date,
    category: bill.category || '其他',
    platform: bill.platform || 'wechat',
    note: bill.note || ''
  }
  showEditModal.value = true
}

const closeEditModal = () => {
  showEditModal.value = false
}

const updateBill = async () => {
  if (!editingBill.value.name || !editingBill.value.amount || !editingBill.value.date) return
  
  isSaving.value = true
  
  try {
    const amount = parseFloat(editingBill.value.amount)
    const billData = {
      name: editingBill.value.name,
      amount: editingBill.value.type === 'expense' ? -Math.abs(amount) : Math.abs(amount),
      type: editingBill.value.type,
      date: editingBill.value.date,
      category: editingBill.value.category,
      platform: editingBill.value.platform,
      note: editingBill.value.note || ''
    }
    
    const response = await fetch(`${API_BASE}/bills/${editingBill.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(billData)
    })
    
    if (response.ok) {
      await fetchBills()
      closeEditModal()
      showToast('更新成功')
    } else {
      const result = await response.json()
      showToast('更新失败: ' + (result.detail || '未知错误'))
    }
  } catch (error) {
    console.error('更新失败:', error)
    showToast('无法连接服务器')
  } finally {
    isSaving.value = false
  }
}

const openDeleteModal = (bill) => {
  deletingBill.value = bill
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  deletingBill.value = null
}

const confirmDelete = async () => {
  if (!deletingBill.value) return
  
  try {
    const response = await fetch(`${API_BASE}/bills/${deletingBill.value.id}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      await fetchBills()
      closeDeleteModal()
      showToast('删除成功')
    } else {
      const result = await response.json()
      showToast('删除失败: ' + (result.detail || '未知错误'))
    }
  } catch (error) {
    console.error('删除失败:', error)
    showToast('无法连接服务器')
  }
}

onMounted(async () => {
  await fetchBills()
})
</script>

<template>
  <div class="p-6 lg:p-8 max-w-[1600px] mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
      </div>
      <div class="flex gap-3">
        <button
          @click="showImportModal = true"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-base-200/80 hover:bg-base-200 text-base-content font-medium text-sm transition-all"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          导入
        </button>
        <button
          @click="openAddModal"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-medium text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          记账
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="py-20 text-center">
      <svg class="w-10 h-10 mx-auto animate-spin text-primary" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <p class="text-sm text-base-content/40 mt-4">加载数据中...</p>
    </div>

    <div v-else-if="bills.length === 0" class="py-16 text-center">
      <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
        <svg class="w-10 h-10 text-primary/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-base-content/80 mb-2">暂无账单数据</h2>
      <p class="text-base-content/50 mb-6">导入账单文件或手动添加记录</p>
      <button
        @click="showImportModal = true"
        class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-medium text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        导入账单
      </button>
    </div>

    <template v-else>
      <div class="flex items-center gap-3 mb-5 flex-wrap">
        <TimeFilter @change="onTimeFilterChange" />
        <AppleSelect
          v-model="selectedCategory"
          :options="categoryOptions"
          placeholder="全部分类"
        />
        <AppleSelect
          v-model="selectedPlatform"
          :options="platformOptions"
          placeholder="全部平台"
        />
        <div v-if="pieSelectedCategory" class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-medium">
          <span>{{ pieSelectedCategory }}</span>
          <button @click="clearPieFilter" class="hover:bg-primary/20 rounded-full p-0.5 transition-colors">
            <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div class="grid gap-4 mb-6" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
        <div 
          v-for="(stat, index) in stats" 
          :key="index" 
          class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/50 border border-base-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-base-300/10 hover:-translate-y-0.5"
        >
          <div class="absolute inset-0 bg-gradient-to-br opacity-5" :class="{
            'from-error to-error/50': stat.type === 'expense',
            'from-success to-success/50': stat.type === 'income',
            'from-info to-info/50': stat.type === 'balance',
            'from-primary to-primary/50': stat.type === 'count'
          }"></div>
          
          <div class="relative p-4">
            <div class="flex items-start justify-between mb-2">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110" :class="{
                'bg-gradient-to-br from-error/20 to-error/5 text-error': stat.type === 'expense',
                'bg-gradient-to-br from-success/20 to-success/5 text-success': stat.type === 'income',
                'bg-gradient-to-br from-info/20 to-info/5 text-info': stat.type === 'balance',
                'bg-gradient-to-br from-primary/20 to-primary/5 text-primary': stat.type === 'count'
              }">
                <svg v-if="stat.type === 'expense'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <svg v-else-if="stat.type === 'income'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <svg v-else-if="stat.type === 'balance'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
                <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              
              <div v-if="stat.trend !== 'neutral'" class="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold" :class="{
                'bg-success/10 text-success': stat.trend === 'up',
                'bg-error/10 text-error': stat.trend === 'down'
              }">
                <svg v-if="stat.trend === 'up'" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                </svg>
              </div>
            </div>
            
            <div class="text-xs font-medium text-base-content/60 mb-1">{{ stat.title }}</div>
            <div class="text-2xl font-bold tracking-tight mb-1">{{ stat.value }}</div>
            <div class="text-xs font-medium" :class="{
              'text-error': stat.type === 'expense',
              'text-success': stat.type === 'income',
              'text-info': stat.type === 'balance',
              'text-base-content/50': stat.type === 'count'
            }">{{ stat.desc }}</div>
          </div>
        </div>
      </div>

      <div class="grid gap-6 lg:grid-cols-3 mb-6">
        <div class="lg:col-span-2 grid gap-6 lg:grid-cols-2">
          <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
            <h3 class="text-base font-bold mb-4">收支趋势</h3>
            <VueApexCharts type="area" height="200" :options="trendOptions" :series="trendSeries" />
          </div>

          <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-base font-bold">分类统计</h3>
              <div class="flex gap-1 p-0.5 bg-base-200/50 rounded-lg">
                <button
                  class="px-2 py-1 rounded-md text-xs font-medium transition-all"
                  :class="categoryType === 'expense' ? 'bg-base-100 shadow-sm' : 'text-base-content/60'"
                  @click="categoryType = 'expense'; pieSelectedCategory = null"
                >支出</button>
                <button
                  class="px-2 py-1 rounded-md text-xs font-medium transition-all"
                  :class="categoryType === 'income' ? 'bg-base-100 shadow-sm' : 'text-base-content/60'"
                  @click="categoryType = 'income'; pieSelectedCategory = null"
                >收入</button>
              </div>
            </div>
            <div v-if="categorySeries.length === 0" class="py-6 text-center text-base-content/40 text-sm">
              暂无数据
            </div>
            <VueApexCharts v-else type="donut" height="180" :options="categoryOptionsChart" :series="categorySeries" />
          </div>
        </div>

        <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-bold">账单明细</h3>
            <div class="flex items-center gap-2">
              <span class="text-xs text-base-content/50">{{ displayBills.length }} 条</span>
              <button
                @click="showBillList = !showBillList"
                class="w-6 h-6 rounded-md bg-base-200/50 flex items-center justify-center hover:bg-base-200 transition-colors"
              >
                <svg class="w-3.5 h-3.5 transition-transform duration-300" :class="{ 'rotate-180': !showBillList }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>
          </div>
          
          <div v-if="showBillList" class="space-y-1.5 max-h-[280px] overflow-y-auto pr-1">
            <div
              v-for="bill in displayBills"
              :key="bill.id"
              class="group flex items-center gap-2.5 p-2.5 rounded-xl bg-base-200/20 hover:bg-base-200/40 transition-all"
            >
              <div class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
                :class="'bg-gradient-to-br ' + platformInfo[bill.platform]?.color + ' text-white'">
                <PlatformIcon :platform="bill.platform" size="sm" />
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-1.5">
                  <span class="font-medium text-sm truncate">{{ bill.name }}</span>
                  <span class="px-1 py-0.5 rounded text-xs bg-base-200/80 text-base-content/50 shrink-0">
                    {{ bill.category || '其他' }}
                  </span>
                </div>
                <div class="text-xs text-base-content/40">{{ bill.date }}</div>
              </div>
              <div class="font-semibold text-sm tabular-nums shrink-0" :class="bill.amount >= 0 ? 'text-success' : 'text-base-content'">
                {{ formatAmount(bill.amount) }}
              </div>
              <div class="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                <button
                  @click="openEditModal(bill)"
                  class="p-1 rounded hover:bg-primary/10 text-primary/60 hover:text-primary transition-all"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
                <button
                  @click="openDeleteModal(bill)"
                  class="p-1 rounded hover:bg-error/10 text-error/60 hover:text-error transition-all"
                >
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div v-if="displayBills.length === 0" class="py-6 text-center text-base-content/40 text-sm">
              暂无符合条件的账单
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
        <h3 class="text-base font-bold mb-4">周期对比</h3>
        <VueApexCharts type="bar" height="200" :options="comparisonOptions" :series="comparisonSeries" />
      </div>
    </template>

    <div v-if="showImportModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showImportModal = false"></div>
      <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold">导入账单</h2>
            <button @click="showImportModal = false" class="p-2 rounded-xl hover:bg-base-200 transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div v-if="uploadResult" class="mb-4 p-3 rounded-xl flex items-center justify-between"
            :class="uploadResult.type === 'success' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'">
            <span class="text-sm font-medium">{{ uploadResult.message }}</span>
            <button @click="uploadResult = null" class="p-1 hover:opacity-70">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="mb-5">
            <label class="block text-sm font-medium text-base-content/60 mb-2">选择平台</label>
            <div class="grid grid-cols-3 gap-3">
              <button
                v-for="(info, key) in platformInfo"
                :key="key"
                @click="importType = key"
                class="p-3 rounded-xl text-center transition-all"
                :class="importType === key 
                  ? 'bg-gradient-to-br ' + info.color + ' text-white shadow-lg' 
                  : 'bg-base-200/50 hover:bg-base-200'"
              >
                <PlatformIcon :platform="key" size="md" />
                <div class="text-xs font-medium mt-1">{{ info.name }}</div>
              </button>
            </div>
          </div>

          <div
            @dragover="handleDragOver"
            @dragleave="handleDragLeave"
            @drop="handleDrop"
            class="relative rounded-2xl border-2 border-dashed transition-all cursor-pointer overflow-hidden"
            :class="isDragging 
              ? 'border-primary bg-primary/5' 
              : 'border-base-300/50 hover:border-primary/50 bg-base-200/30'"
          >
            <input
              type="file"
              @change="handleFileSelect"
              accept=".csv,.CSV,.xlsx,.xls"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div class="p-6 text-center">
              <p v-if="!uploadedFile" class="text-sm text-base-content/50">
                拖拽文件或<span class="text-primary">点击上传</span>
              </p>
              <p v-else class="text-sm text-primary font-medium">{{ uploadedFile.name }}</p>
              <p class="text-xs text-base-content/30 mt-1">支持 CSV、Excel</p>
            </div>
          </div>

          <button
            @click="startImport"
            :disabled="!uploadedFile || !importType || isUploading"
            class="w-full mt-5 py-3 rounded-xl font-semibold text-sm transition-all disabled:opacity-40"
            :class="uploadedFile && importType && !isUploading
              ? 'bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/25 hover:shadow-xl'
              : 'bg-base-200 text-base-content/50'"
          >
            <span v-if="isUploading" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              导入中...
            </span>
            <span v-else>开始导入</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeAddModal"></div>
      <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold">手动记账</h2>
            <button @click="closeAddModal" class="p-1.5 rounded-lg hover:bg-base-200 transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div class="flex gap-2 p-1 bg-base-200/50 rounded-xl">
              <button
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                :class="newBill.type === 'expense' ? 'bg-base-100 text-error shadow-sm' : 'text-base-content/60'"
                @click="newBill.type = 'expense'"
              >支出</button>
              <button
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                :class="newBill.type === 'income' ? 'bg-base-100 text-success shadow-sm' : 'text-base-content/60'"
                @click="newBill.type = 'income'"
              >收入</button>
            </div>

            <div>
              <label class="block text-xs font-medium text-base-content/60 mb-1.5">金额</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40">¥</span>
                <input
                  v-model="newBill.amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  class="w-full pl-7 pr-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-base font-semibold"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-base-content/60 mb-1.5">名称</label>
              <input
                v-model="newBill.name"
                type="text"
                placeholder="例如：午餐、地铁、工资"
                class="w-full px-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm"
              />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-base-content/60 mb-1.5">日期</label>
                <input
                  v-model="newBill.date"
                  type="date"
                  class="w-full px-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-base-content/60 mb-1.5">分类</label>
                <select
                  v-model="newBill.category"
                  class="w-full px-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm cursor-pointer appearance-none"
                >
                  <option v-for="cat in ['餐饮', '交通', '购物', '工资', '投资', '娱乐', '医疗', '转账', '其他']" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-base-content/60 mb-1.5">平台</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="(info, key) in platformInfo"
                  :key="key"
                  @click="newBill.platform = key"
                  class="py-2 rounded-xl text-xs font-medium transition-all"
                  :class="newBill.platform === key 
                    ? 'bg-gradient-to-br ' + info.color + ' text-white' 
                    : 'bg-base-200/50 text-base-content/60 hover:bg-base-200'"
                >{{ info.name }}</button>
              </div>
            </div>
          </div>

          <div class="flex gap-3 mt-5">
            <button
              @click="closeAddModal"
              class="flex-1 py-2.5 rounded-xl bg-base-200 text-base-content font-medium text-sm hover:bg-base-300 transition-colors"
            >取消</button>
            <button
              @click="saveBill"
              :disabled="!newBill.name || !newBill.amount || !newBill.date || isSaving"
              class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-medium text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all disabled:opacity-40"
            >保存</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeEditModal"></div>
      <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold">编辑账单</h2>
            <button @click="closeEditModal" class="p-1.5 rounded-lg hover:bg-base-200 transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div class="flex gap-2 p-1 bg-base-200/50 rounded-xl">
              <button
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                :class="editingBill.type === 'expense' ? 'bg-base-100 text-error shadow-sm' : 'text-base-content/60'"
                @click="editingBill.type = 'expense'"
              >支出</button>
              <button
                class="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                :class="editingBill.type === 'income' ? 'bg-base-100 text-success shadow-sm' : 'text-base-content/60'"
                @click="editingBill.type = 'income'"
              >收入</button>
            </div>

            <div>
              <label class="block text-xs font-medium text-base-content/60 mb-1.5">金额</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40">¥</span>
                <input
                  v-model="editingBill.amount"
                  type="number"
                  step="0.01"
                  class="w-full pl-7 pr-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-base font-semibold"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-base-content/60 mb-1.5">名称</label>
              <input
                v-model="editingBill.name"
                type="text"
                class="w-full px-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm"
              />
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-base-content/60 mb-1.5">日期</label>
                <input
                  v-model="editingBill.date"
                  type="date"
                  class="w-full px-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-base-content/60 mb-1.5">分类</label>
                <select
                  v-model="editingBill.category"
                  class="w-full px-3 py-2.5 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm cursor-pointer appearance-none"
                >
                  <option v-for="cat in ['餐饮', '交通', '购物', '工资', '投资', '娱乐', '医疗', '转账', '其他']" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium text-base-content/60 mb-1.5">平台</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="(info, key) in platformInfo"
                  :key="key"
                  @click="editingBill.platform = key"
                  class="py-2 rounded-xl text-xs font-medium transition-all"
                  :class="editingBill.platform === key 
                    ? 'bg-gradient-to-br ' + info.color + ' text-white' 
                    : 'bg-base-200/50 text-base-content/60 hover:bg-base-200'"
                >{{ info.name }}</button>
              </div>
            </div>
          </div>

          <div class="flex gap-3 mt-5">
            <button
              @click="closeEditModal"
              class="flex-1 py-2.5 rounded-xl bg-base-200 text-base-content font-medium text-sm hover:bg-base-300 transition-colors"
            >取消</button>
            <button
              @click="updateBill"
              :disabled="!editingBill.name || !editingBill.amount || !editingBill.date || isSaving"
              class="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-medium text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all disabled:opacity-40"
            >保存</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeDeleteModal"></div>
      <div class="relative w-full max-w-sm bg-base-100 rounded-2xl shadow-2xl overflow-hidden">
        <div class="p-6 text-center">
          <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-error/10 flex items-center justify-center">
            <svg class="w-6 h-6 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
          <h3 class="text-base font-bold mb-1">删除账单</h3>
          <p v-if="deletingBill" class="text-sm text-base-content/60">
            {{ deletingBill.name }} · {{ formatAmount(deletingBill.amount) }}
          </p>
        </div>
        <div class="flex border-t border-base-200">
          <button
            @click="closeDeleteModal"
            class="flex-1 py-3 text-sm font-medium text-base-content/60 hover:bg-base-200/50 transition-colors"
          >取消</button>
          <button
            @click="confirmDelete"
            class="flex-1 py-3 text-sm font-medium text-error hover:bg-error/10 transition-colors border-l border-base-200"
          >删除</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl shadow-lg text-white text-sm font-medium"
      :class="toast.includes('成功') ? 'bg-success' : 'bg-error'">
      {{ toast }}
    </div>
  </div>
</template>
