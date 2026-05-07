<script setup>
defineOptions({ name: 'Bills' })
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()
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
  bills, total, isLoading, fetchBills, loadMore, exportBills, batchDeleteBills,
  showAddModal, newBill, isSaving, openAddModal, closeAddModal, saveBill,
  showEditModal, editingBill, openEditModal, closeEditModal, updateBill,
  showDeleteModal, deletingBill, openDeleteModal, closeDeleteModal, confirmDelete
} = useBillApi({ showToast })

const isSelectMode = ref(false)
const selectedIds = ref(new Set())

const toggleSelectMode = () => {
  isSelectMode.value = !isSelectMode.value
  if (!isSelectMode.value) {
    selectedIds.value.clear()
  }
}

const toggleSelect = (bill) => {
  if (selectedIds.value.has(bill.id)) {
    selectedIds.value.delete(bill.id)
  } else {
    selectedIds.value.add(bill.id)
  }
}

const isSelected = (id) => selectedIds.value.has(id)

const selectAll = () => {
  bills.value.forEach(b => selectedIds.value.add(b.id))
}

const deselectAll = () => {
  selectedIds.value.clear()
}

const isAllSelected = computed(() => bills.value.length > 0 && selectedIds.value.size === bills.value.length)

const showBatchDeleteConfirm = ref(false)

const openBatchDeleteConfirm = () => {
  showBatchDeleteConfirm.value = true
}

const closeBatchDeleteConfirm = () => {
  showBatchDeleteConfirm.value = false
}

const confirmBatchDelete = async () => {
  const success = await batchDeleteBills([...selectedIds.value])
  if (success) {
    selectedIds.value.clear()
    isSelectMode.value = false
    await fetchBills(getFetchParams())
  }
  closeBatchDeleteConfirm()
}

const {
  importType, isDragging, uploadedFile, isUploading, uploadResult,
  handleDragOver, handleDragLeave, handleDrop, handleFileSelect,
  startImport, clearResult
} = useFileImport({ showToast, onImportSuccess: () => fetchBills(getFetchParams()) })

const searchQuery = ref('')
const startDate = ref('')
const endDate = ref('')
const minAmount = ref('')
const maxAmount = ref('')
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
  start_date: startDate.value || undefined,
  end_date: endDate.value || undefined,
  min_amount: minAmount.value ? parseFloat(minAmount.value) : undefined,
  max_amount: maxAmount.value ? parseFloat(maxAmount.value) : undefined,
})

const doFetch = () => {
  bills.value = []
  fetchBills(getFetchParams())
}

const doExport = () => {
  exportBills({
    search: searchQuery.value || undefined,
    category: selectedCategory.value !== 'all' ? selectedCategory.value : undefined,
    platform: selectedPlatform.value !== 'all' ? selectedPlatform.value : undefined,
    start_date: startDate.value || undefined,
    end_date: endDate.value || undefined,
    min_amount: minAmount.value ? parseFloat(minAmount.value) : undefined,
    max_amount: maxAmount.value ? parseFloat(maxAmount.value) : undefined,
  })
}

const clearDateFilter = () => {
  startDate.value = ''
  endDate.value = ''
  minAmount.value = ''
  maxAmount.value = ''
}

const doLoadMore = async () => {
  if (isLoadingMore.value || !hasMore.value) return
  isLoadingMore.value = true
  await loadMore({
    page_size: PAGE_SIZE,
    search: searchQuery.value || undefined,
    category: selectedCategory.value !== 'all' ? selectedCategory.value : undefined,
    platform: selectedPlatform.value !== 'all' ? selectedPlatform.value : undefined,
    start_date: startDate.value || undefined,
    end_date: endDate.value || undefined,
    min_amount: minAmount.value ? parseFloat(minAmount.value) : undefined,
    max_amount: maxAmount.value ? parseFloat(maxAmount.value) : undefined,
  })
  isLoadingMore.value = false
}

let debounceTimer = null
watch(searchQuery, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(doFetch, 300)
})

watch([selectedCategory, selectedPlatform, startDate, endDate, minAmount, maxAmount], doFetch)

onMounted(doFetch)
</script>

<template>
  <div class="space-y-6 animate-elegant-in">
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight mb-1">
          <span class="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">{{ t('bills.title') }}</span>
        </h1>
        <p class="text-sm text-base-content/50 font-medium">{{ t('bills.subtitle') }}</p>
      </div>
      <div class="flex items-center gap-3">
        <template v-if="isSelectMode">
          <button
            @click="isAllSelected ? deselectAll() : selectAll()"
            class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-base-200/60 text-base-content/70 font-medium text-sm hover:bg-base-200/80 transition-elegant hover-lift"
          >
            <div class="w-5 h-5 rounded-lg border-2 flex items-center justify-center transition-all" :class="isAllSelected ? 'bg-gradient-elegant border-transparent shadow-md' : 'border-base-content/30'">
              <svg v-if="isAllSelected" class="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            {{ t('bill.selectAll') }}
          </button>
          <button
            @click="openBatchDeleteConfirm"
            :disabled="selectedIds.size === 0"
            class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-error/10 text-error font-medium text-sm hover:bg-error/20 transition-elegant hover-lift disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:transform-none"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            {{ t('bill.batchDelete') }} ({{ selectedIds.size }})
          </button>
          <button
            @click="toggleSelectMode"
            class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-base-200/60 text-base-content/70 font-medium text-sm hover:bg-base-200/80 transition-elegant hover-lift"
          >
            {{ t('common.cancel') }}
          </button>
        </template>
        <template v-else>
          <button
            @click="toggleSelectMode"
            class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-base-200/60 text-base-content/70 font-medium text-sm hover:bg-base-200/80 hover:text-base-content/90 transition-elegant hover-lift"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            {{ t('bill.batchSelect') }}
          </button>
          <button
            @click="doExport"
            class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-base-200/60 text-base-content/70 font-medium text-sm hover:bg-base-200/80 hover:text-base-content/90 transition-elegant hover-lift"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {{ t('bill.exportBtn') }}
          </button>
          <button
            @click="openAddModal"
            class="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-elegant text-white font-semibold text-sm shadow-elevated hover-lift transition-elegant group"
          >
            <svg class="w-5 h-5 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            {{ t('bill.addTitle') }}
          </button>
        </template>
      </div>
    </div>

    <Transition name="slide-fade">
      <div
        v-if="uploadResult"
        class="mb-6 p-4 rounded-xl flex items-center justify-between glass-elegant"
        :class="uploadResult.type === 'success' 
          ? 'border border-success/20' 
          : 'border border-error/20'"
      >
        <div class="flex items-center gap-3">
          <svg v-if="uploadResult.type === 'success'" class="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <svg v-else class="w-5 h-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span class="font-medium text-sm" :class="uploadResult.type === 'success' ? 'text-success' : 'text-error'">{{ uploadResult.message }}</span>
        </div>
        <button @click="clearResult" class="p-1 hover:opacity-70 transition-opacity">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </Transition>

    <div class="grid gap-8 lg:grid-cols-5">
      <div class="lg:col-span-2">
        <div class="sticky top-8 space-y-6">
          <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant-lg hover-lift transition-elegant group">
            <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
            
            <div class="relative p-6">
              <div class="flex items-center gap-3 mb-5">
                <div class="w-11 h-11 rounded-xl bg-gradient-elegant flex items-center justify-center shadow-lg">
                  <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-lg font-bold tracking-tight">{{ t('import.title') }}</h2>
                  <p class="text-xs text-base-content/50 font-medium">{{ t('import.platformSupport') }}</p>
                </div>
              </div>

              <div class="mb-5">
                <div class="flex items-center justify-between mb-3">
                  <span class="text-sm font-semibold text-base-content/60">{{ t('import.selectPlatform') }}</span>
                  <span v-if="uploadedFile && importType" class="text-xs text-success font-semibold px-2 py-1 rounded-lg bg-success/10">
                    {{ t('import.autoDetected') }}
                  </span>
                </div>
                <div class="grid grid-cols-3 gap-3">
                  <button
                    v-for="(info, key) in platformInfo"
                    :key="key"
                    @click="importType = key"
                    class="group relative overflow-hidden rounded-xl p-4 transition-elegant hover-lift"
                    :class="importType === key 
                      ? 'bg-gradient-elegant text-white shadow-elevated' 
                      : 'bg-base-200/50 hover:bg-base-200'"
                  >
                    <PlatformIcon :platform="key" size="md" />
                    <div class="text-xs font-semibold mt-2">{{ t('platforms.' + key) }}</div>
                  </button>
                </div>
              </div>

              <div
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @drop="handleDrop"
                class="relative rounded-xl border-2 border-dashed transition-elegant cursor-pointer overflow-hidden group"
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
                <div class="p-8 text-center">
                  <div class="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-base-200 to-base-300/50 flex items-center justify-center shadow-inner">
                    <svg class="w-7 h-7 text-base-content/40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <p v-if="!uploadedFile" class="text-sm text-base-content/50 font-medium group-hover:text-base-content/70 transition-colors">
                    {{ t('import.dragHint') }}
                  </p>
                  <p v-else class="text-sm text-primary font-semibold">
                    {{ uploadedFile.name }}
                  </p>
                  <p class="text-xs text-base-content/30 mt-2">{{ t('import.supportedFormat') }}</p>
                </div>
              </div>

              <button
                @click="startImport"
                :disabled="!uploadedFile || !importType || isUploading"
                class="w-full mt-5 py-3.5 rounded-xl font-semibold text-sm transition-elegant disabled:opacity-40 group"
                :class="uploadedFile && importType && !isUploading
                  ? 'bg-gradient-elegant text-white shadow-elevated hover-lift' 
                  : 'bg-base-200 text-base-content/50'"
              >
                <span v-if="isUploading" class="flex items-center justify-center gap-2">
                  <svg class="w-4 h-4 animate-elegant-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ t('import.importing') }}
                </span>
                <span v-else>{{ t('import.startImport') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="lg:col-span-3">
        <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant-lg hover-lift transition-elegant">
          <div class="p-6">
            <div class="flex flex-col sm:flex-row gap-4 mb-5">
              <div class="relative flex-1 group">
                <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-base-content/30 group-focus-within:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  v-model="searchQuery"
                  type="text"
                  :placeholder="t('bill.searchPlaceholder')"
                  class="w-full pl-11 pr-4 py-3 rounded-xl bg-base-200/50 border border-transparent group-hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm placeholder:text-base-content/30 shadow-inset"
                />
              </div>
              <div class="flex gap-3">
                <AppleSelect
                  v-model="selectedCategory"
                  :options="categoryOptions"
                />
                <AppleSelect
                  v-model="selectedPlatform"
                  :options="platformOptions"
                />
              </div>
            </div>

            <div class="flex items-center gap-3 mb-5 text-sm">
              <svg class="w-4 h-4 text-base-content/30 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <input
                v-model="startDate"
                type="date"
                class="px-3 py-2 rounded-lg bg-base-200/50 border border-transparent hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm text-base-content/70 shadow-inset"
              />
              <span class="text-base-content/30">—</span>
              <input
                v-model="endDate"
                type="date"
                class="px-3 py-2 rounded-lg bg-base-200/50 border border-transparent hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm text-base-content/70 shadow-inset"
              />
              <button
                v-if="startDate || endDate || minAmount || maxAmount"
                @click="clearDateFilter"
                class="px-2.5 py-1 rounded-lg text-xs font-medium text-base-content/40 hover:text-base-content/60 hover:bg-base-200/60 transition-elegant"
              >
                {{ t('common.clear') }}
              </button>
            </div>

            <div class="flex items-center gap-3 mb-5 text-sm">
              <svg class="w-4 h-4 text-base-content/30 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-base-content/40 text-xs font-medium">{{ t('bill.amountRange') }}</span>
              <input
                v-model.number="minAmount"
                type="number"
                :placeholder="t('bill.minAmount')"
                step="100"
                min="0"
                class="px-3 py-2 w-28 rounded-lg bg-base-200/50 border border-transparent hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm text-base-content/70 placeholder:text-base-content/30 shadow-inset"
              />
              <span class="text-base-content/30">—</span>
              <input
                v-model.number="maxAmount"
                type="number"
                :placeholder="t('bill.maxAmount')"
                step="100"
                min="0"
                class="px-3 py-2 w-28 rounded-lg bg-base-200/50 border border-transparent hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm text-base-content/70 placeholder:text-base-content/30 shadow-inset"
              />
              <span class="text-xs text-base-content/30 font-medium">{{ t('common.currency') }}</span>
            </div>

            <div v-if="isLoading" class="py-16 text-center">
              <svg class="w-10 h-10 mx-auto animate-elegant-spin text-primary" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-sm text-base-content/40 mt-4 font-medium">{{ t('common.loading') }}</p>
            </div>

            <div v-else-if="bills.length > 0" class="space-y-2">
              <BillItem
                v-for="bill in bills"
                :key="bill.id"
                :bill="bill"
                :selectable="isSelectMode"
                :selected="isSelected(bill.id)"
                @edit="openEditModal"
                @delete="openDeleteModal"
                @toggle-select="toggleSelect"
              />
            </div>

            <div v-else class="py-16 text-center">
              <div class="relative inline-block mb-6">
                <div class="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-base-200/60 to-base-100/40 flex items-center justify-center hover-lift transition-elegant">
                  <svg class="w-10 h-10 text-base-content/20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div class="absolute -inset-4 bg-gradient-to-r from-primary/10 via-purple-500/10 to-pink-500/10 rounded-2xl blur-xl -z-10"></div>
              </div>
              <p class="text-sm text-base-content/40 font-medium">{{ t('bill.noBills') }}</p>
              <p class="text-xs text-base-content/30 mt-2">{{ t('bill.noBillsHint') }}</p>
            </div>

            <div v-if="!isLoading && bills.length > 0" class="mt-6 pt-4 border-t border-base-200/50">
              <div class="flex items-center justify-between text-sm">
                <span class="text-base-content/40 font-medium">{{ t('bill.loadedOf', { loaded: bills.length, total }) }}</span>
                <button
                  v-if="hasMore"
                  @click="doLoadMore"
                  :disabled="isLoadingMore"
                  class="px-4 py-2 rounded-xl bg-base-200/60 hover:bg-base-200 text-sm font-medium text-base-content/60 hover:text-base-content/80 transition-elegant hover-lift disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg v-if="isLoadingMore" class="w-4 h-4 animate-elegant-spin inline-block mr-1" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ isLoadingMore ? t('common.loading') : t('bill.loadMore') }}
                </button>
                <span v-else class="text-base-content/30 font-medium">{{ t('bill.allLoaded') }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <BillFormModal :visible="showAddModal" :bill="newBill" :title="t('bill.addTitle')" :is-saving="isSaving" @close="closeAddModal" @save="saveBill" />

    <BillFormModal :visible="showEditModal" :bill="editingBill" :title="t('bill.editTitle')" :is-saving="isSaving" @close="closeEditModal" @save="updateBill" />

    <DeleteConfirmModal :visible="showDeleteModal" :bill="deletingBill" @close="closeDeleteModal" @confirm="confirmDelete" />

    <div v-if="showBatchDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/20 backdrop-blur-md" @click="closeBatchDeleteConfirm"></div>
      <div class="relative w-full max-w-md glass-elegant rounded-2xl shadow-elegant-lg overflow-hidden animate-elegant-in">
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-error via-red-500 to-pink-500"></div>
        <div class="p-8 text-center">
          <div class="w-16 h-16 mx-auto mb-5 rounded-2xl bg-error/10 flex items-center justify-center">
            <svg class="w-8 h-8 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </div>
          <h3 class="text-xl font-bold mb-3">{{ t('bill.batchDeleteTitle') }}</h3>
          <p class="text-sm text-base-content/60 mb-6">{{ t('bill.batchDeleteConfirm', { n: selectedIds.size }) }}</p>
          <div class="flex gap-3">
            <button @click="closeBatchDeleteConfirm" class="flex-1 py-3 rounded-xl bg-base-200 text-base-content/70 font-semibold text-sm hover:bg-base-200/80 transition-elegant">
              {{ t('common.cancel') }}
            </button>
            <button @click="confirmBatchDelete" class="flex-1 py-3 rounded-xl bg-gradient-to-r from-error to-red-500 text-white font-semibold text-sm shadow-elevated hover-lift transition-elegant">
              {{ t('common.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <Transition name="slide-down">
      <div v-if="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl shadow-elevated text-white text-sm font-semibold backdrop-blur-md"
        :class="toast.type === 'success' ? 'bg-gradient-to-r from-success to-green-500' : 'bg-gradient-to-r from-error to-red-500'">
        {{ toast.message }}
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

.slide-down-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translate(-50%, -1.5rem);
  opacity: 0;
}
</style>
