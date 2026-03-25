<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCurrentTheme } from '../utils/theme'
import { API_BASE } from '../config'
import PlatformIcon from '../components/PlatformIcon.vue'

const toast = ref('')
const toastTimer = ref(null)
const showToast = (msg) => {
  toast.value = msg
  clearTimeout(toastTimer.value)
  toastTimer.value = setTimeout(() => { toast.value = '' }, 3000)
}

const currentTheme = ref(getCurrentTheme())

window.addEventListener('themechange', (e) => {
  currentTheme.value = e.detail.theme
})

const importType = ref(null)
const isDragging = ref(false)
const uploadedFile = ref(null)
const isUploading = ref(false)
const uploadResult = ref(null)
const importHistory = ref([])

const bills = ref([])
const isLoading = ref(false)

const searchQuery = ref('')
const selectedCategory = ref('all')
const selectedPlatform = ref('all')

const categories = ['all', '餐饮', '交通', '购物', '工资', '投资', '娱乐', '医疗', '转账', '其他']
const platforms = ['all', 'wechat', 'alipay', 'bank']
const editCategories = ['餐饮', '交通', '购物', '工资', '投资', '娱乐', '医疗', '转账', '其他']
const editPlatforms = ['wechat', 'alipay', 'bank']

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

const filteredBills = computed(() => {
  return bills.value.filter(bill => {
    const matchSearch = bill.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchCategory = selectedCategory.value === 'all' || bill.category === selectedCategory.value
    const matchPlatform = selectedPlatform.value === 'all' || bill.platform === selectedPlatform.value
    return matchSearch && matchCategory && matchPlatform
  })
})

const platformInfo = {
  wechat: { name: '微信', color: 'from-green-500 to-green-600' },
  alipay: { name: '支付宝', color: 'from-blue-500 to-blue-600' },
  bank: { name: '银行卡', color: 'from-yellow-500 to-yellow-600' }
}

const fetchBills = async () => {
  isLoading.value = true
  try {
    const response = await fetch(`${API_BASE}/bills`)
    if (response.ok) {
      bills.value = await response.json()
    } else {
      showToast('获取账单失败: ' + response.status)
    }
  } catch (error) {
    console.error('获取账单失败:', error)
    showToast('无法连接服务器，请检查网络')
  } finally {
    isLoading.value = false
  }
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
      
      importHistory.value.unshift({
        id: Date.now(),
        platform: importType.value,
        count: result.success,
        date: new Date().toLocaleDateString('zh-CN'),
        status: 'success'
      })
      
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

const formatAmount = (amount) => {
  const absAmount = Math.abs(amount)
  return amount >= 0 ? `+¥${absAmount.toFixed(2)}` : `-¥${absAmount.toFixed(2)}`
}

const clearResult = () => {
  uploadResult.value = null
}

onMounted(() => {
  fetchBills()
})
</script>

<template>
  <div class="p-6 lg:p-8 max-w-[1400px] mx-auto">
    <div class="mb-10 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">账单</h1>
        <p class="text-sm text-base-content/50 mt-2 font-medium">导入和管理您的账单数据</p>
      </div>
      <button
        @click="openAddModal"
        class="flex items-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-primary to-primary/80 text-white font-semibold text-sm shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5 transition-all duration-300"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        手动记账
      </button>
    </div>

    <div
      v-if="uploadResult"
      class="mb-6 p-4 rounded-2xl flex items-center justify-between animate-[fadeIn_0.3s_ease-out]"
      :class="uploadResult.type === 'success' 
        ? 'bg-success/10 border border-success/20 text-success' 
        : 'bg-error/10 border border-error/20 text-error'"
    >
      <div class="flex items-center gap-3">
        <svg v-if="uploadResult.type === 'success'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="font-medium">{{ uploadResult.message }}</span>
      </div>
      <button @click="clearResult" class="p-1 hover:opacity-70 transition-opacity">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <div class="grid gap-8 lg:grid-cols-5">
      <div class="lg:col-span-2">
        <div class="sticky top-8 space-y-6">
          <div class="relative overflow-hidden rounded-[20px] bg-gradient-to-br from-base-100/90 via-base-100/80 to-base-200/30 backdrop-blur-2xl border border-white/10 dark:border-white/5 shadow-[0_8px_32px_rgba(0,0,0,0.08)]">
            <div class="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent"></div>
            
            <div class="relative p-6">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                  <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-lg font-semibold tracking-tight">导入账单</h2>
                  <p class="text-xs text-base-content/50">支持微信、支付宝账单文件</p>
                </div>
              </div>

              <div class="mb-6">
                <div class="flex items-center justify-between mb-3">
                  <span class="text-sm font-medium text-base-content/60">选择平台</span>
                  <span v-if="uploadedFile && importType" class="text-xs text-success font-medium">
                    ✓ 已自动识别
                  </span>
                </div>
                <div class="grid grid-cols-3 gap-3">
                  <button
                    v-for="(info, key) in platformInfo"
                    :key="key"
                    @click="importType = key"
                    class="group relative overflow-hidden rounded-2xl p-4 transition-all duration-300"
                    :class="importType === key 
                      ? 'bg-gradient-to-br ' + info.color + ' text-white shadow-lg scale-[1.02]'
                      : 'bg-base-200/50 hover:bg-base-200/80'"
                  >
                    <PlatformIcon :platform="key" size="md" />
                    <div class="text-xs font-medium mt-1" :class="importType === key ? 'text-white' : 'text-base-content/70'">
                      {{ info.name }}
                    </div>
                  </button>
                </div>
              </div>

              <div
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @drop="handleDrop"
                class="relative rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer overflow-hidden"
                :class="isDragging 
                  ? 'border-primary bg-primary/5 scale-[1.01]' 
                  : 'border-base-300/50 hover:border-primary/50 bg-base-200/30'"
              >
                <input
                  type="file"
                  @change="handleFileSelect"
                  accept=".csv,.CSV,.xlsx,.xls"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div class="p-8 text-center">
                  <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-base-200 to-base-300/50 flex items-center justify-center">
                    <svg class="w-7 h-7 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p v-if="!uploadedFile" class="text-sm text-base-content/50 font-medium">
                    拖拽文件到此处，或<span class="text-primary">点击上传</span>
                  </p>
                  <p v-else class="text-sm text-primary font-medium">
                    {{ uploadedFile.name }}
                  </p>
                  <p class="text-xs text-base-content/30 mt-2">支持 CSV、Excel 格式</p>
                </div>
              </div>

              <button
                @click="startImport"
                :disabled="!uploadedFile || !importType || isUploading"
                class="w-full mt-5 py-3.5 rounded-2xl font-semibold text-sm tracking-wide transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed"
                :class="uploadedFile && importType && !isUploading
                  ? 'bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5'
                  : 'bg-base-200 text-base-content/50'"
              >
                <span v-if="isUploading" class="flex items-center justify-center gap-2">
                  <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  正在导入...
                </span>
                <span v-else>开始导入</span>
              </button>
            </div>
          </div>

          <div v-if="importHistory.length > 0" class="relative overflow-hidden rounded-[20px] bg-gradient-to-br from-base-100/90 via-base-100/80 to-base-200/30 backdrop-blur-2xl border border-white/10 dark:border-white/5 shadow-[0_8px_32px_rgba(0,0,0,0.08)]">
            <div class="p-6">
              <div class="flex items-center justify-between mb-5">
                <h3 class="font-semibold tracking-tight">导入历史</h3>
                <span class="text-xs text-base-content/40">{{ importHistory.length }} 次导入</span>
              </div>
              <div class="space-y-3">
                <div
                  v-for="record in importHistory"
                  :key="record.id"
                  class="flex items-center gap-3 p-3 rounded-xl bg-base-200/30 hover:bg-base-200/50 transition-colors"
                >
                  <div class="w-9 h-9 rounded-xl flex items-center justify-center text-lg"
                    :class="'bg-gradient-to-br ' + platformInfo[record.platform].color + ' text-white'">
                    <PlatformIcon :platform="record.platform" size="sm" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="text-sm font-medium truncate">{{ platformInfo[record.platform].name }}账单</div>
                    <div class="text-xs text-base-content/40">{{ record.count }} 条记录</div>
                  </div>
                  <div class="text-xs text-base-content/30">{{ record.date }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="lg:col-span-3">
        <div class="relative overflow-hidden rounded-[20px] bg-gradient-to-br from-base-100/90 via-base-100/80 to-base-200/30 backdrop-blur-2xl border border-white/10 dark:border-white/5 shadow-[0_8px_32px_rgba(0,0,0,0.08)]">
          <div class="p-6">
            <div class="flex flex-col sm:flex-row gap-4 mb-6">
              <div class="relative flex-1">
                <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-base-content/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索账单..."
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm placeholder:text-base-content/30 transition-all"
                />
              </div>
              <div class="flex gap-3">
                <select
                  v-model="selectedCategory"
                  class="px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm cursor-pointer appearance-none min-w-[100px]"
                >
                  <option v-for="cat in categories" :key="cat" :value="cat">
                    {{ cat === 'all' ? '全部分类' : cat }}
                  </option>
                </select>
                <select
                  v-model="selectedPlatform"
                  class="px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm cursor-pointer appearance-none min-w-[100px]"
                >
                  <option v-for="plat in platforms" :key="plat" :value="plat">
                    {{ plat === 'all' ? '全部平台' : platformInfo[plat].name }}
                  </option>
                </select>
              </div>
            </div>

            <div v-if="isLoading" class="py-16 text-center">
              <svg class="w-8 h-8 mx-auto animate-spin text-primary" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-sm text-base-content/40 mt-4">加载中...</p>
            </div>

            <div v-else-if="filteredBills.length > 0" class="space-y-2">
              <div
                v-for="bill in filteredBills"
                :key="bill.id"
                class="group flex items-center gap-4 p-4 rounded-2xl bg-base-200/20 hover:bg-base-200/40 transition-all duration-300 cursor-pointer"
              >
                <div class="w-11 h-11 rounded-xl flex items-center justify-center"
                  :class="'bg-gradient-to-br ' + platformInfo[bill.platform]?.color + ' text-white shadow-sm'">
                  <PlatformIcon :platform="bill.platform" size="sm" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-sm truncate">{{ bill.name }}</span>
                    <span class="px-2 py-0.5 rounded-md text-xs bg-base-200/80 text-base-content/50">
                      {{ bill.category || '其他' }}
                    </span>
                  </div>
                  <div class="text-xs text-base-content/40 mt-1">{{ bill.date }}</div>
                </div>
                <div class="text-right flex items-center gap-2">
                  <div class="font-semibold tabular-nums mr-2" :class="bill.amount >= 0 ? 'text-success' : 'text-base-content'">
                    {{ formatAmount(bill.amount) }}
                  </div>
                  <button
                    @click.stop="openEditModal(bill)"
                    class="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-primary/10 text-primary/60 hover:text-primary transition-all"
                    title="编辑"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    @click.stop="openDeleteModal(bill)"
                    class="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-error/10 text-error/60 hover:text-error transition-all"
                    title="删除"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="py-16 text-center">
              <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-base-200/50 flex items-center justify-center">
                <svg class="w-8 h-8 text-base-content/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p class="text-sm text-base-content/40">暂无账单数据</p>
              <p class="text-xs text-base-content/30 mt-1">导入账单文件或手动添加记录</p>
            </div>

            <div v-if="!isLoading && filteredBills.length > 0" class="mt-6 pt-4 border-t border-base-200/50">
              <div class="flex items-center justify-between text-sm">
                <span class="text-base-content/40">共 {{ filteredBills.length }} 条记录</span>
                <span class="text-base-content/40">总计 {{ bills.length }} 条</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showAddModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeAddModal"></div>
      <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold tracking-tight">手动记账</h2>
            <button @click="closeAddModal" class="p-2 rounded-xl hover:bg-base-200 transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div class="flex gap-2 p-1 bg-base-200/50 rounded-2xl">
              <button
                class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
                :class="newBill.type === 'expense' ? 'bg-base-100 text-error shadow-sm' : 'text-base-content/60'"
                @click="newBill.type = 'expense'"
              >
                支出
              </button>
              <button
                class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
                :class="newBill.type === 'income' ? 'bg-base-100 text-success shadow-sm' : 'text-base-content/60'"
                @click="newBill.type = 'income'"
              >
                收入
              </button>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">金额</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-base-content/40">¥</span>
                <input
                  v-model="newBill.amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  class="w-full pl-8 pr-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-lg font-semibold"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">名称</label>
              <input
                v-model="newBill.name"
                type="text"
                placeholder="例如：午餐、地铁、工资"
                class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-base-content/60 mb-2">日期</label>
                <input
                  v-model="newBill.date"
                  type="date"
                  class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-base-content/60 mb-2">分类</label>
                <select
                  v-model="newBill.category"
                  class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer appearance-none"
                >
                  <option v-for="cat in editCategories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">平台</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="(info, key) in platformInfo"
                  :key="key"
                  @click="newBill.platform = key"
                  class="py-2.5 rounded-xl text-sm font-medium transition-all"
                  :class="newBill.platform === key 
                    ? 'bg-gradient-to-br ' + info.color + ' text-white' 
                    : 'bg-base-200/50 text-base-content/60 hover:bg-base-200'"
                >
                  {{ info.name }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">备注（可选）</label>
              <input
                v-model="newBill.note"
                type="text"
                placeholder="添加备注..."
                class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <button
              @click="closeAddModal"
              class="flex-1 py-3 rounded-xl bg-base-200 text-base-content font-semibold text-sm hover:bg-base-300 transition-colors"
            >
              取消
            </button>
            <button
              @click="saveBill"
              :disabled="!newBill.name || !newBill.amount || !newBill.date || isSaving"
              class="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-semibold text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span v-if="isSaving" class="flex items-center justify-center gap-2">
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                保存中...
              </span>
              <span v-else>保存</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeEditModal"></div>
      <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold tracking-tight">编辑账单</h2>
            <button @click="closeEditModal" class="p-2 rounded-xl hover:bg-base-200 transition-colors">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="space-y-4">
            <div class="flex gap-2 p-1 bg-base-200/50 rounded-2xl">
              <button
                class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
                :class="editingBill.type === 'expense' ? 'bg-base-100 text-error shadow-sm' : 'text-base-content/60'"
                @click="editingBill.type = 'expense'"
              >
                支出
              </button>
              <button
                class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
                :class="editingBill.type === 'income' ? 'bg-base-100 text-success shadow-sm' : 'text-base-content/60'"
                @click="editingBill.type = 'income'"
              >
                收入
              </button>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">金额</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-base-content/40">¥</span>
                <input
                  v-model="editingBill.amount"
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  class="w-full pl-8 pr-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-lg font-semibold"
                />
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">名称</label>
              <input
                v-model="editingBill.name"
                type="text"
                placeholder="例如：午餐、地铁、工资"
                class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-base-content/60 mb-2">日期</label>
                <input
                  v-model="editingBill.date"
                  type="date"
                  class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-base-content/60 mb-2">分类</label>
                <select
                  v-model="editingBill.category"
                  class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer appearance-none"
                >
                  <option v-for="cat in editCategories" :key="cat" :value="cat">{{ cat }}</option>
                </select>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">平台</label>
              <div class="grid grid-cols-3 gap-2">
                <button
                  v-for="(info, key) in platformInfo"
                  :key="key"
                  @click="editingBill.platform = key"
                  class="py-2.5 rounded-xl text-sm font-medium transition-all"
                  :class="editingBill.platform === key 
                    ? 'bg-gradient-to-br ' + info.color + ' text-white' 
                    : 'bg-base-200/50 text-base-content/60 hover:bg-base-200'"
                >
                  {{ info.name }}
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">备注（可选）</label>
              <input
                v-model="editingBill.note"
                type="text"
                placeholder="添加备注..."
                class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
          </div>

          <div class="flex gap-3 mt-6">
            <button
              @click="closeEditModal"
              class="flex-1 py-3 rounded-xl bg-base-200 text-base-content font-semibold text-sm hover:bg-base-300 transition-colors"
            >
              取消
            </button>
            <button
              @click="updateBill"
              :disabled="!editingBill.name || !editingBill.amount || !editingBill.date || isSaving"
              class="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-semibold text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span v-if="isSaving" class="flex items-center justify-center gap-2">
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                保存中...
              </span>
              <span v-else>保存</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeDeleteModal"></div>
      <div class="relative w-full max-w-sm bg-base-100 rounded-3xl shadow-2xl overflow-hidden animate-[scaleIn_0.2s_ease-out]">
        <div class="p-6 text-center">
          <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-error/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
          <h3 class="text-lg font-bold mb-2">删除账单</h3>
          <p class="text-sm text-base-content/60 mb-1">确定要删除这条账单吗？</p>
          <p v-if="deletingBill" class="text-sm font-medium text-base-content/80">
            {{ deletingBill.name }} · {{ formatAmount(deletingBill.amount) }}
          </p>
        </div>
        <div class="flex border-t border-base-200">
          <button
            @click="closeDeleteModal"
            class="flex-1 py-4 text-sm font-semibold text-base-content/60 hover:bg-base-200/50 transition-colors"
          >
            取消
          </button>
          <button
            @click="confirmDelete"
            class="flex-1 py-4 text-sm font-semibold text-error hover:bg-error/10 transition-colors border-l border-base-200"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Toast 通知 -->
  <div v-if="toast" class="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl shadow-lg text-white text-sm font-medium animate-bounce"
    :class="toast.includes('成功') ? 'bg-success' : 'bg-error'">
    {{ toast }}
  </div>
</template>

<style>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
