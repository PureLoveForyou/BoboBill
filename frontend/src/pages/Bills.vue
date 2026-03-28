<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { getCurrentTheme } from '../utils/theme'
import PlatformIcon from '../components/PlatformIcon.vue'
import AppleSelect from '../components/AppleSelect.vue'
import { PLATFORM_INFO } from '../constants/bill'
import { useToast } from '../composables/useToast'
import { useBillApi } from '../composables/useBillApi'
import { useFileImport } from '../composables/useFileImport'
import { useBillFilters } from '../composables/useBillFilters'
import BillItem from '../components/BillItem.vue'
import BillFormModal from '../components/BillFormModal.vue'
import DeleteConfirmModal from '../components/DeleteConfirmModal.vue'

const { toast, showToast } = useToast()

const currentTheme = ref(getCurrentTheme())

const onThemeChange = (e) => {
  currentTheme.value = e.detail.theme
}
window.addEventListener('themechange', onThemeChange)

onUnmounted(() => {
  window.removeEventListener('themechange', onThemeChange)
})

const PAGE_SIZE = 20

const {
  bills, total, isLoading, fetchBills, loadMore,
  showAddModal, newBill, isSaving, openAddModal, closeAddModal, saveBill,
  showEditModal, editingBill, openEditModal, closeEditModal, updateBill,
  showDeleteModal, deletingBill, openDeleteModal, closeDeleteModal, confirmDelete
} = useBillApi({ showToast })

const {
  importType, isDragging, uploadedFile, isUploading, uploadResult,
  handleDragOver, handleDragLeave, handleDrop, handleFileSelect,
  startImport, clearResult
} = useFileImport({ showToast, onImportSuccess: () => fetchBills(getFetchParams()) })

const searchQuery = ref('')
const { selectedCategory, selectedPlatform, categoryOptions, platformOptions } = useBillFilters()

const platformInfo = PLATFORM_INFO

const hasMore = computed(() => bills.value.length < total.value)
const isLoadingMore = ref(false)

const getFetchParams = () => ({
  page: 1,
  page_size: PAGE_SIZE,
  search: searchQuery.value || undefined,
  category: selectedCategory.value !== 'all' ? selectedCategory.value : undefined,
  platform: selectedPlatform.value !== 'all' ? selectedPlatform.value : undefined,
})

const doFetch = () => {
  bills.value = []
  fetchBills(getFetchParams())
}

const doLoadMore = async () => {
  if (isLoadingMore.value || !hasMore.value) return
  isLoadingMore.value = true
  await loadMore({
    page_size: PAGE_SIZE,
    search: searchQuery.value || undefined,
    category: selectedCategory.value !== 'all' ? selectedCategory.value : undefined,
    platform: selectedPlatform.value !== 'all' ? selectedPlatform.value : undefined,
  })
  isLoadingMore.value = false
}

let debounceTimer = null
watch(searchQuery, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(doFetch, 300)
})

watch([selectedCategory, selectedPlatform], doFetch)

onMounted(doFetch)
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
              </div>
            </div>

            <div v-if="isLoading" class="py-16 text-center">
              <svg class="w-8 h-8 mx-auto animate-spin text-primary" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-sm text-base-content/40 mt-4">加载中...</p>
            </div>

            <div v-else-if="bills.length > 0" class="space-y-2">
              <BillItem
                v-for="bill in bills"
                :key="bill.id"
                :bill="bill"
                @edit="openEditModal"
                @delete="openDeleteModal"
              />
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

            <div v-if="!isLoading && bills.length > 0" class="mt-6 pt-4 border-t border-base-200/50">
              <div class="flex items-center justify-between text-sm">
                <span class="text-base-content/40">已加载 {{ bills.length }} / {{ total }} 条</span>
                <button
                  v-if="hasMore"
                  @click="doLoadMore"
                  :disabled="isLoadingMore"
                  class="px-4 py-2 rounded-xl bg-base-200/60 hover:bg-base-200 text-sm font-medium text-base-content/60 hover:text-base-content/80 transition-all disabled:opacity-50"
                >
                  <svg v-if="isLoadingMore" class="w-4 h-4 animate-spin inline-block mr-1" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ isLoadingMore ? '加载中...' : '加载更多' }}
                </button>
                <span v-else class="text-base-content/30">已全部加载</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BillFormModal :visible="showAddModal" :bill="newBill" title="手动记账" :is-saving="isSaving" @close="closeAddModal" @save="saveBill" />

    <BillFormModal :visible="showEditModal" :bill="editingBill" title="编辑账单" :is-saving="isSaving" @close="closeEditModal" @save="updateBill" />

    <DeleteConfirmModal :visible="showDeleteModal" :bill="deletingBill" @close="closeDeleteModal" @confirm="confirmDelete" />
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
