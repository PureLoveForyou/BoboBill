<script setup>
defineOptions({ name: 'Dashboard' })
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import VueApexCharts from 'vue3-apexcharts'
import TimeFilter from '../components/TimeFilter.vue'
import PlatformIcon from '../components/PlatformIcon.vue'
import AppleSelect from '../components/AppleSelect.vue'
import dayjs from 'dayjs'
import { getCurrentTheme } from '../utils/theme'
import { PLATFORM_INFO } from '../constants/bill'
import { useToast } from '../composables/useToast'
import { useBillApi } from '../composables/useBillApi'
import { useFileImport } from '../composables/useFileImport'
import { useBillFilters } from '../composables/useBillFilters'
import { useDashboardData } from '../composables/useDashboardData'
import { useChartConfig } from '../composables/useChartConfig'
import BillItem from '../components/BillItem.vue'
import StatCards from '../components/StatCards.vue'
import BillFormModal from '../components/BillFormModal.vue'
import DeleteConfirmModal from '../components/DeleteConfirmModal.vue'
import BudgetCard from '../components/BudgetCard.vue'
import { useBudgetApi } from '../composables/useBudgetApi'

const { t } = useI18n()

// --- Composables ---
const { toast, showToast } = useToast()
const { selectedCategory, selectedPlatform, categoryOptions, platformOptions } = useBillFilters()

const {
  bills, isLoading, fetchBills,
  showAddModal, newBill, isSaving, openAddModal, closeAddModal, saveBill,
  showEditModal, editingBill, openEditModal, closeEditModal, updateBill,
  showDeleteModal, deletingBill, openDeleteModal, closeDeleteModal, confirmDelete
} = useBillApi({ showToast, onBillsChanged: () => processBillsData(currentFilterType.value, currentRange.value) })

const {
  showImportModal, importType, isDragging, uploadedFile, isUploading, uploadResult,
  handleDragOver, handleDragLeave, handleDrop, handleFileSelect,
  startImport
} = useFileImport({ showToast, onImportSuccess: async () => { await fetchBills() } })

const {
  stats, trendSeries, trendCategories,
  categoryType, categorySeries, categoryLabels,
  pieSelectedCategory, clearPieFilter,
  expenseLabels, incomeLabels, totalExpense, totalIncome,
  comparisonSeries, comparisonCategories,
  processBillsData
} = useDashboardData({ bills, selectedCategory, selectedPlatform })

// --- Local State ---
const currentFilterType = ref('monthly')
const currentRange = ref({ start: dayjs().startOf('month').format('YYYY-MM-DD'), end: dayjs().endOf('month').format('YYYY-MM-DD') })
const currentTheme = ref(getCurrentTheme())
const showBillList = ref(true)
const platformInfo = PLATFORM_INFO

const { trendOptions, categoryOptionsChart, comparisonOptions } = useChartConfig({
  currentTheme, trendCategories,
  categoryType, categoryLabels, categorySeries,
  pieSelectedCategory, expenseLabels, incomeLabels, totalExpense, totalIncome,
  comparisonCategories
})

// --- Budget ---
const { budgetStatus, fetchBudgetStatus } = useBudgetApi()

// --- Theme & Modal ---
const themeChangeHandler = (e) => {
  currentTheme.value = e.detail.theme
}
window.addEventListener('themechange', themeChangeHandler)

const anyModalOpen = computed(() => showImportModal.value || showAddModal.value || showEditModal.value || showDeleteModal.value)
watch(anyModalOpen, (isOpen) => {
  document.body.style.overflow = isOpen ? 'hidden' : ''
})
const handleEscape = (e) => {
  if (e.key === 'Escape') {
    if (showDeleteModal.value) closeDeleteModal()
    else if (showEditModal.value) closeEditModal()
    else if (showAddModal.value) closeAddModal()
    else if (showImportModal.value) showImportModal.value = false
  }
}
window.addEventListener('keydown', handleEscape)

onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', handleEscape)
  window.removeEventListener('themechange', themeChangeHandler)
})

// --- Filtered Bills ---
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
    result = result.filter(bill => (bill.category || '其他') === selectedCategory.value)
  }
  if (selectedPlatform.value !== 'all') {
    result = result.filter(bill => bill.platform === selectedPlatform.value)
  }
  if (pieSelectedCategory.value) {
    result = result.filter(bill => (bill.category || '其他') === pieSelectedCategory.value)
  }
  return result.sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 20)
})

const onTimeFilterChange = (data) => {
  currentFilterType.value = data.type
  currentRange.value = data.range
  pieSelectedCategory.value = null
  processBillsData(data.type, data.range)
}

onMounted(async () => {
  await fetchBills()
  processBillsData('monthly', currentRange.value)
  fetchBudgetStatus()
})
</script>

<template>
  <div class="p-6 lg:p-8 max-w-[1600px] mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold tracking-tight">{{ t('dashboard.title') }}</h1>
      </div>
      <div class="flex gap-3">
        <button
          @click="showImportModal = true"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-base-200/80 hover:bg-base-200 text-base-content font-medium text-sm transition-all"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {{ t('dashboard.import') }}
        </button>
        <button
          @click="openAddModal"
          class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-medium text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('dashboard.addBill') }}
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="space-y-6">
      <div class="grid gap-4" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
        <div v-for="i in 4" :key="i" class="rounded-2xl border border-base-200/50 p-4 space-y-3">
          <div class="flex justify-between"><div class="skeleton w-10 h-10"></div><div class="skeleton w-12 h-6"></div></div>
          <div class="skeleton w-16 h-3"></div>
          <div class="skeleton w-28 h-7"></div>
          <div class="skeleton w-20 h-3"></div>
        </div>
      </div>
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="rounded-2xl border border-base-200/50 p-5"><div class="skeleton w-full h-56"></div></div>
        <div class="rounded-2xl border border-base-200/50 p-5"><div class="skeleton w-full h-56"></div></div>
      </div>
      <div class="rounded-2xl border border-base-200/50 p-5"><div class="skeleton w-full h-56"></div></div>
    </div>

    <div v-else-if="bills.length === 0" class="py-16 text-center">
      <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
        <svg class="w-10 h-10 text-primary/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-base-content/80 mb-2">{{ t('bill.noBills') }}</h2>
      <p class="text-base-content/50 mb-6">{{ t('bill.noBillsHint') }}</p>
      <button
        @click="showImportModal = true"
        class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-medium text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        {{ t('dashboard.importBtn') }}
      </button>
    </div>

    <template v-else>
      <div class="flex items-center gap-3 mb-5 flex-wrap">
        <TimeFilter @change="onTimeFilterChange" />
        <AppleSelect
          v-model="selectedCategory"
          :options="categoryOptions"
        />
        <AppleSelect
          v-model="selectedPlatform"
          :options="platformOptions"
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

      <StatCards :stats="stats" />

      <div class="mb-6">
        <BudgetCard :status="budgetStatus" />
      </div>

      <div class="grid gap-6 lg:grid-cols-2 mb-6">
        <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
          <h3 class="text-base font-bold mb-4">{{ t('dashboard.trendTitle') }}</h3>
          <VueApexCharts type="area" height="220" :options="trendOptions" :series="trendSeries" />
        </div>

        <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-base font-bold">{{ t('dashboard.categoryTitle') }}</h3>
            <div class="flex gap-1 p-0.5 bg-base-200/50 rounded-lg">
              <button
                class="px-2 py-1 rounded-md text-xs font-medium transition-all"
                :class="categoryType === 'expense' ? 'bg-base-100 shadow-sm' : 'text-base-content/60'"
                @click="categoryType = 'expense'; pieSelectedCategory = null"
              >{{ t('common.expense') }}</button>
              <button
                class="px-2 py-1 rounded-md text-xs font-medium transition-all"
                :class="categoryType === 'income' ? 'bg-base-100 shadow-sm' : 'text-base-content/60'"
                @click="categoryType = 'income'; pieSelectedCategory = null"
              >{{ t('common.income') }}</button>
            </div>
          </div>
          <div v-if="categorySeries.length === 0" class="py-6 text-center text-base-content/40 text-sm">
            {{ t('common.noData') }}
          </div>
          <VueApexCharts v-else type="donut" height="220" :options="categoryOptionsChart" :series="categorySeries" />
        </div>
      </div>

      <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5 mb-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <h3 class="text-base font-bold">{{ t('dashboard.billDetail') }}</h3>
            <span class="text-xs text-base-content/40 px-2 py-0.5 rounded-full bg-base-200/50">{{ displayBills.length }}</span>
            <div v-if="pieSelectedCategory" class="flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
              {{ pieSelectedCategory }}
              <button @click="clearPieFilter" class="hover:bg-primary/20 rounded-full p-0.5 transition-colors">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <button
            @click="showBillList = !showBillList"
            class="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-base-200/50 hover:bg-base-200 transition-colors text-xs font-medium text-base-content/60"
          >
            {{ showBillList ? t('dashboard.collapse') : t('dashboard.expand') }}
            <svg class="w-3.5 h-3.5 transition-transform duration-300" :class="{ 'rotate-180': !showBillList }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
        
        <div v-if="showBillList" class="space-y-1.5 max-h-[400px] overflow-y-auto pr-1">
          <BillItem
            v-for="bill in displayBills"
            :key="bill.id"
            :bill="bill"
            compact
            @edit="openEditModal"
            @delete="openDeleteModal"
          />
          
          <div v-if="displayBills.length === 0" class="py-8 text-center text-base-content/40 text-sm">
            {{ t('bill.noMatchingBills') }}
          </div>
          <div v-else class="py-3 text-center text-xs text-base-content/30">
            {{ t('bill.onlyShowRecent', { n: 20 }) }}
          </div>
        </div>
      </div>

      <div class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
        <h3 class="text-base font-bold mb-4">{{ t('dashboard.periodComparison') }}</h3>
        <VueApexCharts type="bar" height="220" :options="comparisonOptions" :series="comparisonSeries" />
      </div>
    </template>

    <div v-if="showImportModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showImportModal = false"></div>
      <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
        <div class="p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-xl font-bold">{{ t('import.title') }}</h2>
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
            <label class="block text-sm font-medium text-base-content/60 mb-2">{{ t('import.selectPlatform') }}</label>
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
                <div class="text-xs font-medium mt-1">{{ t('platforms.' + key) }}</div>
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
                {{ t('import.dragHintShort') }}
              </p>
              <p v-else class="text-sm text-primary font-medium">{{ uploadedFile.name }}</p>
              <p class="text-xs text-base-content/30 mt-1">{{ t('import.supportedFormatShort') }}</p>
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
              {{ t('import.importing') }}
            </span>
            <span v-else>{{ t('import.startImport') }}</span>
          </button>
        </div>
      </div>
    </div>

    <BillFormModal :visible="showAddModal" :bill="newBill" :title="t('bill.addTitle')" :is-saving="isSaving" @close="closeAddModal" @save="saveBill" />

    <BillFormModal :visible="showEditModal" :bill="editingBill" :title="t('bill.editTitle')" :is-saving="isSaving" @close="closeEditModal" @save="updateBill" />

    <DeleteConfirmModal :visible="showDeleteModal" :bill="deletingBill" @close="closeDeleteModal" @confirm="confirmDelete" />

    <div v-if="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl shadow-lg text-white text-sm font-medium animate-slide-down"
      :class="toast.type === 'success' ? 'bg-success' : 'bg-error'">
      {{ toast.message }}
    </div>
  </div>
</template>
