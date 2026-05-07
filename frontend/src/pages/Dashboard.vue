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

const { budgetStatus, fetchBudgetStatus } = useBudgetApi()

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
  <div class="space-y-6 animate-elegant-in">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight mb-1">
          <span class="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">{{ t('dashboard.title') }}</span>
        </h1>
        <p class="text-sm text-base-content/50">{{ t('dashboard.subtitle') || '查看您的财务概览' }}</p>
      </div>
      <div class="flex gap-3">
        <button
          @click="showImportModal = true"
          class="flex items-center gap-2 px-5 py-2.5 rounded-elegant bg-base-200/60 hover:bg-base-200/80 text-base-content font-medium text-sm transition-elegant hover-lift shadow-elegant"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          {{ t('dashboard.import') }}
        </button>
        <button
          @click="openAddModal"
          class="flex items-center gap-2 px-5 py-2.5 rounded-elegant bg-gradient-elegant text-white font-medium text-sm shadow-elevated hover-lift transition-elegant group"
        >
          <svg class="w-4 h-4 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('dashboard.addBill') }}
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="space-y-6">
      <div class="grid gap-4" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
        <div v-for="i in 4" :key="i" class="glass-elegant rounded-elegant-lg p-5 space-y-4 hover-lift transition-elegant">
          <div class="flex justify-between"><div class="skeleton w-12 h-12 rounded-xl"></div><div class="skeleton w-16 h-6 rounded-lg"></div></div>
          <div class="skeleton w-20 h-3 rounded"></div>
          <div class="skeleton w-32 h-8 rounded-lg"></div>
          <div class="skeleton w-24 h-3 rounded"></div>
        </div>
      </div>
      <div class="grid gap-6 lg:grid-cols-2">
        <div class="glass-elegant rounded-elegant-lg p-6 hover-lift transition-elegant"><div class="skeleton w-full h-56 rounded-xl"></div></div>
        <div class="glass-elegant rounded-elegant-lg p-6 hover-lift transition-elegant"><div class="skeleton w-full h-56 rounded-xl"></div></div>
      </div>
      <div class="glass-elegant rounded-elegant-lg p-6 hover-lift transition-elegant"><div class="skeleton w-full h-56 rounded-xl"></div></div>
    </div>

    <div v-else-if="bills.length === 0" class="py-20 text-center">
      <div class="relative inline-block mb-8">
        <div class="w-24 h-24 mx-auto rounded-3xl bg-gradient-to-br from-primary/20 via-purple-500/20 to-pink-500/20 flex items-center justify-center hover-lift transition-elegant">
          <svg class="w-12 h-12 text-primary/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <div class="absolute -inset-4 bg-gradient-to-r from-primary/10 via-purple-500/10 to-pink-500/10 rounded-3xl blur-xl -z-10"></div>
      </div>
      <h2 class="text-2xl font-bold text-base-content/80 mb-3">{{ t('bill.noBills') }}</h2>
      <p class="text-base-content/50 mb-8 max-w-md mx-auto">{{ t('bill.noBillsHint') }}</p>
      <button
        @click="showImportModal = true"
        class="inline-flex items-center gap-2 px-6 py-3 rounded-elegant bg-gradient-elegant text-white font-semibold text-sm shadow-elevated hover-lift transition-elegant group"
      >
        <svg class="w-4 h-4 transition-transform group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
        </svg>
        {{ t('dashboard.importBtn') }}
      </button>
    </div>

    <template v-else>
      <div class="flex items-center gap-3 flex-wrap">
        <TimeFilter @change="onTimeFilterChange" />
        <AppleSelect
          v-model="selectedCategory"
          :options="categoryOptions"
        />
        <AppleSelect
          v-model="selectedPlatform"
          :options="platformOptions"
        />
        <div v-if="pieSelectedCategory" class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-primary/10 to-purple-500/10 text-primary text-xs font-semibold border border-primary/20 hover-lift transition-elegant">
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
        <div class="glass-elegant rounded-elegant-lg p-6 hover-lift transition-elegant group">
          <h3 class="text-lg font-bold mb-5 group-hover:text-primary transition-colors">{{ t('dashboard.trendTitle') }}</h3>
          <VueApexCharts type="area" height="240" :options="trendOptions" :series="trendSeries" />
        </div>

        <div class="glass-elegant rounded-elegant-lg p-6 hover-lift transition-elegant group">
          <div class="flex items-center justify-between mb-5">
            <h3 class="text-lg font-bold group-hover:text-primary transition-colors">{{ t('dashboard.categoryTitle') }}</h3>
            <div class="flex gap-1 p-1 bg-base-200/50 rounded-xl">
              <button
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-elegant"
                :class="categoryType === 'expense' ? 'bg-gradient-elegant text-white shadow-md' : 'text-base-content/60 hover:text-base-content'"
                @click="categoryType = 'expense'; pieSelectedCategory = null"
              >{{ t('common.expense') }}</button>
              <button
                class="px-3 py-1.5 rounded-lg text-xs font-semibold transition-elegant"
                :class="categoryType === 'income' ? 'bg-gradient-elegant text-white shadow-md' : 'text-base-content/60 hover:text-base-content'"
                @click="categoryType = 'income'; pieSelectedCategory = null"
              >{{ t('common.income') }}</button>
            </div>
          </div>
          <div v-if="categorySeries.length === 0" class="py-12 text-center text-base-content/40 text-sm">
            {{ t('common.noData') }}
          </div>
          <VueApexCharts v-else type="donut" height="240" :options="categoryOptionsChart" :series="categorySeries" />
        </div>
      </div>

      <div class="glass-elegant rounded-elegant-lg p-6 mb-6 hover-lift transition-elegant group">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-bold group-hover:text-primary transition-colors">{{ t('dashboard.billDetail') }}</h3>
            <span class="text-xs text-base-content/40 px-2.5 py-1 rounded-full bg-base-200/50 font-medium">{{ displayBills.length }}</span>
            <div v-if="pieSelectedCategory" class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r from-primary/10 to-purple-500/10 text-primary text-xs font-semibold border border-primary/20">
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
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-base-200/50 hover:bg-base-200 transition-elegant text-xs font-medium text-base-content/60"
          >
            {{ showBillList ? t('dashboard.collapse') : t('dashboard.expand') }}
            <svg class="w-4 h-4 transition-transform duration-300" :class="{ 'rotate-180': !showBillList }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
        
        <div v-if="showBillList" class="space-y-2 max-h-[450px] overflow-y-auto pr-2">
          <BillItem
            v-for="bill in displayBills"
            :key="bill.id"
            :bill="bill"
            compact
            @edit="openEditModal"
            @delete="openDeleteModal"
          />
          
          <div v-if="displayBills.length === 0" class="py-12 text-center text-base-content/40 text-sm">
            {{ t('bill.noMatchingBills') }}
          </div>
          <div v-else class="py-4 text-center text-xs text-base-content/30">
            {{ t('bill.onlyShowRecent', { n: 20 }) }}
          </div>
        </div>
      </div>

      <div class="glass-elegant rounded-elegant-lg p-6 hover-lift transition-elegant group">
        <h3 class="text-lg font-bold mb-5 group-hover:text-primary transition-colors">{{ t('dashboard.periodComparison') }}</h3>
        <VueApexCharts type="bar" height="240" :options="comparisonOptions" :series="comparisonSeries" />
      </div>
    </template>

    <div v-if="showImportModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/20 backdrop-blur-md" @click="showImportModal = false"></div>
      <div class="relative w-full max-w-md glass-elegant rounded-elegant-xl shadow-elegant-lg overflow-hidden animate-elegant-in">
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500"></div>
        <div class="p-8">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-2xl font-bold">{{ t('import.title') }}</h2>
            <button @click="showImportModal = false" class="p-2 rounded-xl hover:bg-base-200/60 transition-elegant">
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <Transition name="slide-fade">
            <div v-if="uploadResult" class="mb-5 p-3 rounded-xl flex items-center justify-between"
              :class="uploadResult.type === 'success' ? 'bg-success/10 text-success border border-success/20' : 'bg-error/10 text-error border border-error/20'">
              <span class="text-sm font-medium">{{ uploadResult.message }}</span>
              <button @click="uploadResult = null" class="p-1 hover:opacity-70">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </Transition>

          <div class="mb-5">
            <label class="block text-sm font-semibold text-base-content/70 mb-3">{{ t('import.selectPlatform') }}</label>
            <div class="grid grid-cols-3 gap-3">
              <button
                v-for="(info, key) in platformInfo"
                :key="key"
                @click="importType = key"
                class="p-4 rounded-xl text-center transition-elegant hover-lift"
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
              : 'border-base-300/50 hover:border-primary/50 bg-base-200/30 hover:bg-base-200/50'"
          >
            <input
              type="file"
              @change="handleFileSelect"
              accept=".csv,.CSV,.xlsx,.xls"
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div class="p-8 text-center">
              <p v-if="!uploadedFile" class="text-sm text-base-content/50 group-hover:text-base-content/70 transition-colors">
                {{ t('import.dragHintShort') }}
              </p>
              <p v-else class="text-sm text-primary font-semibold">{{ uploadedFile.name }}</p>
              <p class="text-xs text-base-content/30 mt-2">{{ t('import.supportedFormatShort') }}</p>
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

    <BillFormModal :visible="showAddModal" :bill="newBill" :title="t('bill.addTitle')" :is-saving="isSaving" @close="closeAddModal" @save="saveBill" />

    <BillFormModal :visible="showEditModal" :bill="editingBill" :title="t('bill.editTitle')" :is-saving="isSaving" @close="closeEditModal" @save="updateBill" />

    <DeleteConfirmModal :visible="showDeleteModal" :bill="deletingBill" @close="closeDeleteModal" @confirm="confirmDelete" />

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
