<script setup>
import { ref, computed, onMounted } from 'vue'
import { getCurrentTheme } from '../utils/theme'

const API_BASE = 'http://localhost:8000'

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

const filteredBills = computed(() => {
  return bills.value.filter(bill => {
    const matchSearch = bill.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchCategory = selectedCategory.value === 'all' || bill.category === selectedCategory.value
    const matchPlatform = selectedPlatform.value === 'all' || bill.platform === selectedPlatform.value
    return matchSearch && matchCategory && matchPlatform
  })
})

const platformInfo = {
  wechat: { name: '微信', icon: '💚', color: 'from-green-500 to-green-600' },
  alipay: { name: '支付宝', icon: '💙', color: 'from-blue-500 to-blue-600' },
  bank: { name: '银行卡', icon: '💛', color: 'from-yellow-500 to-yellow-600' }
}

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

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const files = e.dataTransfer.files
  if (files.length > 0) {
    uploadedFile.value = files[0]
  }
}

const handleFileSelect = (e) => {
  if (e.target.files.length > 0) {
    uploadedFile.value = e.target.files[0]
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
    <div class="mb-10">
      <h1 class="text-3xl font-bold tracking-tight">账单</h1>
      <p class="text-sm text-base-content/50 mt-2 font-medium">导入和管理您的账单数据</p>
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

              <div class="grid grid-cols-3 gap-3 mb-6">
                <button
                  v-for="(info, key) in platformInfo"
                  :key="key"
                  @click="importType = key"
                  class="group relative overflow-hidden rounded-2xl p-4 transition-all duration-300"
                  :class="importType === key 
                    ? 'bg-gradient-to-br ' + info.color + ' text-white shadow-lg scale-[1.02]' 
                    : 'bg-base-200/50 hover:bg-base-200/80'"
                >
                  <div class="text-2xl mb-2">{{ info.icon }}</div>
                  <div class="text-xs font-medium" :class="importType === key ? 'text-white' : 'text-base-content/70'">
                    {{ info.name }}
                  </div>
                </button>
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
                  <p class="text-xs text-base-content/30 mt-2">支持 CSV、Excel 格式（微信账单）</p>
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
                    {{ platformInfo[record.platform].icon }}
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
                <div class="w-11 h-11 rounded-xl flex items-center justify-center text-lg"
                  :class="'bg-gradient-to-br ' + platformInfo[bill.platform]?.color + ' text-white shadow-sm'">
                  {{ platformInfo[bill.platform]?.icon || '💳' }}
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
                <div class="text-right">
                  <div class="font-semibold tabular-nums" :class="bill.amount >= 0 ? 'text-success' : 'text-base-content'">
                    {{ formatAmount(bill.amount) }}
                  </div>
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
              <p class="text-xs text-base-content/30 mt-1">导入账单文件后这里会显示记录</p>
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
</style>
