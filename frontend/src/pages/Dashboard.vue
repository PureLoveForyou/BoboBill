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
  expenseLabels, expenseSeries, incomeLabels, incomeSeries,
  totalExpense, totalIncome,
  comparisonSeries, comparisonCategories,
  processBillsData
} = useDashboardData({ bills, selectedCategory, selectedPlatform })

const { budgetStatus, fetchBudgetStatus } = useBudgetApi()

const currentFilterType = ref('monthly')
const currentRange = ref({ start: dayjs().startOf('month').format('YYYY-MM-DD'), end: dayjs().endOf('month').format('YYYY-MM-DD') })
const currentTheme = ref(getCurrentTheme())
const platformInfo = PLATFORM_INFO

const { trendOptions, categoryOptionsChart, comparisonOptions } = useChartConfig({
  currentTheme, trendCategories,
  categoryType, categoryLabels, categorySeries,
  pieSelectedCategory, expenseLabels, incomeLabels, totalExpense, totalIncome,
  comparisonCategories
})

const themeChangeHandler = (e) => { currentTheme.value = e.detail.theme }
window.addEventListener('themechange', themeChangeHandler)

const anyModalOpen = computed(() => showImportModal.value || showAddModal.value || showEditModal.value || showDeleteModal.value)
watch(anyModalOpen, (isOpen) => { document.body.style.overflow = isOpen ? 'hidden' : '' })
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
  if (selectedCategory.value !== 'all') result = result.filter(bill => (bill.category || '其他') === selectedCategory.value)
  if (selectedPlatform.value !== 'all') result = result.filter(bill => bill.platform === selectedPlatform.value)
  if (pieSelectedCategory.value) result = result.filter(bill => (bill.category || '其他') === pieSelectedCategory.value)
  return result.sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 8)
})

const onTimeFilterChange = (data) => {
  currentFilterType.value = data.type
  currentRange.value = data.range
  pieSelectedCategory.value = null
  processBillsData(data.type, data.range)
}

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return t('greeting.night')
  if (hour < 12) return t('greeting.morning')
  if (hour < 14) return t('greeting.noon')
  if (hour < 18) return t('greeting.afternoon')
  return t('greeting.evening')
})

const heroTrendPill = computed(() => {
  const exp = stats.value.find(s => s.type === 'expense')
  if (!exp || exp.trend === 'neutral' || !exp.change) return null
  const arrow = exp.trend === 'down' ? '↓' : '↑'
  const change = Math.abs(Number(exp.change))
  return { text: `${arrow} ${change}% ${exp.trend === 'down' ? t('dashboard.trendDown') : t('dashboard.trendUp')}`, positive: exp.trend === 'down' }
})

const heroIncome = computed(() => totalIncome.value)
const heroBalance = computed(() => totalIncome.value - totalExpense.value)
const heroCount = computed(() => { const s = stats.value.find(st => st.type === 'count'); return s ? parseInt(s.value) || 0 : 0 })

const aiInsights = computed(() => {
  const insights = []
  if (expenseSeries.value && expenseSeries.value.length > 0 && expenseLabels.value && expenseLabels.value.length > 0) {
    const maxPct = Math.max(...expenseSeries.value)
    const maxIdx = expenseSeries.value.indexOf(maxPct)
    if (maxIdx >= 0 && maxPct > 0) insights.push(`这个月在「${expenseLabels.value[maxIdx]}」上花得最多，占了 ${maxPct}%。`)
  }
  if (budgetStatus.value && budgetStatus.value.monthly_total > 0) {
    if (budgetStatus.value.over_budget) insights.push(`预算超了 ¥${Math.abs(budgetStatus.value.remaining).toLocaleString()}，要看看哪里能调整吗？`)
    else if (budgetStatus.value.percentage >= 80) insights.push(`月度预算用了 ${Math.round(budgetStatus.value.percentage)}%，注意控制一下就好。`)
  }
  const smallBills = filteredBillsByTime.value.filter(b => b.amount < 0 && Math.abs(b.amount) < 50 && Math.abs(b.amount) > 0)
  if (smallBills.length >= 8) insights.push(`小额支出有 ${smallBills.length} 笔，小零花加起来也不少。`)
  return insights.slice(0, 3)
})

onMounted(async () => {
  await fetchBills()
  processBillsData('monthly', currentRange.value)
  fetchBudgetStatus()
})
</script>

<template>
  <div class="bb-page min-h-full p-6 lg:p-8 max-w-[1400px] mx-auto">

    <div v-if="isLoading" class="space-y-6">
      <div class="text-center py-12">
        <div class="skeleton w-40 h-10 mx-auto mb-4 rounded-xl"></div>
        <div class="skeleton w-56 h-6 mx-auto mb-8 rounded-lg"></div>
        <div class="grid gap-4 max-w-md mx-auto" style="grid-template-columns: repeat(3, 1fr);">
          <div class="skeleton w-full h-16 rounded-xl"></div>
          <div class="skeleton w-full h-16 rounded-xl"></div>
          <div class="skeleton w-full h-16 rounded-xl"></div>
        </div>
      </div>
    </div>

    <div v-else-if="bills.length === 0" class="py-20 text-center">
      <div class="w-20 h-20 mx-auto mb-6 rounded-2xl bg-[var(--bb-bg-soft)] flex items-center justify-center">
        <svg class="w-10 h-10 text-[var(--bb-text-tertiary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
      </div>
      <h2 class="text-xl font-bold text-[var(--bb-text)] mb-2">{{ t('bill.noBills') }}</h2>
      <p class="bb-muted text-sm mb-6">{{ t('bill.noBillsHint') }}</p>
      <button @click="showImportModal = true" class="bb-button-primary">{{ t('dashboard.importBtn') }}</button>
    </div>

    <template v-else>
      <div class="flex items-center justify-between gap-6 mb-6 flex-wrap">
        <div>
          <h1 class="text-[30px] font-extrabold text-[var(--bb-text)] tracking-[-0.055em] leading-tight">
            {{ greeting }}，{{ t('greeting.name') }}
          </h1>
          <p class="text-sm font-medium text-[var(--bb-text-secondary)] mt-2">{{ t('greeting.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <button @click="showImportModal = true" class="bb-button-secondary">{{ t('dashboard.import') }}</button>
          <button @click="openAddModal" class="bb-button-primary">{{ t('dashboard.addBill') }}</button>
        </div>
      </div>

      <div class="grid gap-5" style="grid-template-columns: minmax(0, 1.12fr) minmax(320px, .72fr)">
        <div class="bb-card-glass relative overflow-hidden p-7 min-h-[260px] rounded-[var(--bb-radius-lg)]">
          <div class="absolute right-[-90px] top-[-120px] w-[340px] h-[340px] rounded-full opacity-50 pointer-events-none" style="background: radial-gradient(circle, rgba(54,211,153,.24), rgba(36,120,255,.10), transparent 66%);"></div>
          <div class="relative z-10">
            <h2 class="text-base font-bold text-[var(--bb-text)] tracking-[-0.035em]">{{ t('dashboard.periodExpense') }}</h2>
            <p class="bb-hero-amount mt-4 mb-2">
              <small class="text-[27px] font-medium text-[var(--bb-text-secondary)] tracking-[-0.04em] mr-1">{{ t('common.currency') }}</small>{{ totalExpense.toLocaleString() }}
            </p>
            <span v-if="heroTrendPill" class="bb-pill inline-flex" :class="heroTrendPill.positive ? 'bb-pill-positive' : 'bb-pill-warning'">
              {{ heroTrendPill.text }}
            </span>

            <div class="grid grid-cols-3 gap-3 mt-8 max-w-[620px]">
              <div class="rounded-[20px] bg-[var(--bb-surface)] border border-[var(--bb-border)] p-4">
                <span class="text-xs font-bold text-[var(--bb-text-secondary)]">{{ t('common.income') }}</span>
                <strong class="block text-[19px] font-bold text-[var(--bb-text)] mt-2 tracking-[-0.04em]">{{ t('common.currency') }}{{ heroIncome.toLocaleString() }}</strong>
              </div>
              <div class="rounded-[20px] bg-[var(--bb-surface)] border border-[var(--bb-border)] p-4">
                <span class="text-xs font-bold text-[var(--bb-text-secondary)]">{{ t('dashboard.netWorth') }}</span>
                <strong class="block text-[19px] font-bold mt-2 tracking-[-0.04em]" :class="heroBalance >= 0 ? 'text-[var(--bb-mint)]' : 'text-[var(--bb-coral)]'">
                  {{ heroBalance >= 0 ? '+' : '' }}{{ t('common.currency') }}{{ heroBalance.toLocaleString() }}
                </strong>
              </div>
              <div class="rounded-[20px] bg-[var(--bb-surface)] border border-[var(--bb-border)] p-4">
                <span class="text-xs font-bold text-[var(--bb-text-secondary)]">{{ t('dashboard.billCount') }}</span>
                <strong class="block text-[19px] font-bold text-[var(--bb-text)] mt-2 tracking-[-0.04em]">{{ heroCount }}</strong>
              </div>
            </div>
          </div>
        </div>

        <div v-if="aiInsights.length > 0" class="bb-card-glass p-6 flex flex-col gap-4 rounded-[var(--bb-radius-lg)]">
          <div class="w-[54px] h-[54px] rounded-[19px] flex items-center justify-center text-[var(--bb-blue)] text-2xl flex-shrink-0" style="background: linear-gradient(145deg, rgba(54,211,153,.18), rgba(36,120,255,.13));">✦</div>
          <h3 class="text-[22px] font-extrabold text-[var(--bb-text)] tracking-[-0.055em] m-0">{{ t('ai.insightTitle') }}</h3>
          <p class="text-[14px] font-medium leading-relaxed m-0 text-[var(--bb-text-secondary)]">
            {{ aiInsights[0] }}
            <template v-if="aiInsights.length > 1">。{{ aiInsights[1] }}</template>
          </p>
          <div class="flex flex-wrap gap-2 mt-auto">
            <span v-for="(insight, idx) in aiInsights" :key="idx" class="bb-chip">{{ insight.slice(0, 16) }}{{ insight.length > 16 ? '…' : '' }}</span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-3 my-6 flex-wrap">
        <TimeFilter @change="onTimeFilterChange" />
        <AppleSelect v-model="selectedCategory" :options="categoryOptions" />
        <AppleSelect v-model="selectedPlatform" :options="platformOptions" />
        <button v-if="pieSelectedCategory" @click="clearPieFilter" class="bb-chip text-[var(--bb-blue)] bg-[var(--bb-blue)]/8 border-[var(--bb-blue)]/20">{{ pieSelectedCategory }} ✕</button>
      </div>

      <div class="mb-6"><BudgetCard :status="budgetStatus" /></div>

      <div class="grid gap-5 lg:grid-cols-2 mb-5">
        <div class="bb-card-glass p-5">
          <h3 class="bb-section-title mb-4">{{ t('dashboard.trendTitle') }}</h3>
          <VueApexCharts type="area" height="220" :options="trendOptions" :series="trendSeries" />
        </div>
        <div class="bb-card-glass p-5">
          <div class="flex items-center justify-between mb-4">
            <h3 class="bb-section-title">{{ t('dashboard.categoryTitle') }}</h3>
            <div class="flex gap-1 p-0.5 bg-[var(--bb-bg-soft)] rounded-lg">
              <button class="px-2 py-1 rounded-md text-xs font-medium transition-colors" :class="categoryType === 'expense' ? 'bg-white shadow-sm text-[var(--bb-text)]' : 'bb-muted'" @click="categoryType = 'expense'; pieSelectedCategory = null">{{ t('common.expense') }}</button>
              <button class="px-2 py-1 rounded-md text-xs font-medium transition-colors" :class="categoryType === 'income' ? 'bg-white shadow-sm text-[var(--bb-text)]' : 'bb-muted'" @click="categoryType = 'income'; pieSelectedCategory = null">{{ t('common.income') }}</button>
            </div>
          </div>
          <div v-if="categorySeries.length === 0" class="py-6 text-center bb-muted text-sm">{{ t('common.noData') }}</div>
          <VueApexCharts v-else type="donut" height="220" :options="categoryOptionsChart" :series="categorySeries" />
        </div>
      </div>

      <div class="bb-card-glass p-5 mb-5">
        <h3 class="bb-section-title mb-4">{{ t('dashboard.periodComparison') }}</h3>
        <VueApexCharts type="bar" height="220" :options="comparisonOptions" :series="comparisonSeries" />
      </div>

      <div class="bb-card-glass p-5">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <h3 class="bb-section-title">{{ t('dashboard.recentTransactions') }}</h3>
            <span v-if="pieSelectedCategory" class="bb-chip text-[var(--bb-blue)] bg-[var(--bb-blue)]/8 border-[var(--bb-blue)]/20">{{ pieSelectedCategory }}</span>
          </div>
          <router-link to="/bills" class="text-[13px] font-extrabold text-[var(--bb-blue)] no-underline hover:underline">{{ t('dashboard.viewAll') }} →</router-link>
        </div>
        <div v-if="displayBills.length === 0" class="py-8 text-center bb-muted text-sm">{{ t('bill.noMatchingBills') }}</div>
        <div v-else class="flex flex-col gap-[10px]">
          <BillItem v-for="bill in displayBills" :key="bill.id" :bill="bill" compact @edit="openEditModal" @delete="openDeleteModal" />
          <div class="pt-3 text-center">
            <router-link to="/bills" class="text-xs text-[var(--bb-text-tertiary)] hover:text-[var(--bb-text-secondary)] transition-colors no-underline">{{ t('bill.onlyShowRecent', { n: 8 }) }}</router-link>
          </div>
        </div>
      </div>
    </template>

    <div v-if="showImportModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="showImportModal = false"></div>
      <div class="relative w-full max-w-md bb-card-glass shadow-2xl p-6 rounded-[var(--bb-radius-lg)]">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-[var(--bb-text)]">{{ t('import.title') }}</h2>
          <button @click="showImportModal = false" class="p-2 rounded-xl hover:bg-[var(--bb-bg-soft)] transition-colors"><svg class="w-5 h-5 text-[var(--bb-text-secondary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
        </div>
        <div v-if="uploadResult" class="mb-4 p-3 rounded-xl flex items-center justify-between" :class="uploadResult.type === 'success' ? 'bg-[var(--bb-mint)]/10 text-[var(--bb-mint)]' : 'bg-[var(--bb-coral)]/10 text-[var(--bb-coral)]'">
          <span class="text-sm font-medium">{{ uploadResult.message }}</span>
          <button @click="uploadResult = null" class="p-1 hover:opacity-70"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
        </div>
        <div class="mb-5">
          <label class="block text-sm font-medium text-[var(--bb-text-secondary)] mb-2">{{ t('import.selectPlatform') }}</label>
          <div class="grid grid-cols-3 gap-3">
            <button v-for="(info, key) in platformInfo" :key="key" @click="importType = key" class="p-3 rounded-xl text-center transition-all border" :class="importType === key ? 'bg-gradient-to-br ' + info.color + ' text-white border-transparent' : 'bg-[var(--bb-bg-soft)] border-[var(--bb-border)] hover:border-[var(--bb-text-tertiary)]'">
              <PlatformIcon :platform="key" size="md" />
              <div class="text-xs font-medium mt-1">{{ t('platforms.' + key) }}</div>
            </button>
          </div>
        </div>
        <div @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop" class="relative rounded-2xl border-2 border-dashed transition-all cursor-pointer overflow-hidden" :class="isDragging ? 'border-[var(--bb-blue)] bg-[var(--bb-blue)]/5' : 'border-[var(--bb-border)] hover:border-[var(--bb-blue)]/50 bg-[var(--bb-bg-soft)]'">
          <input type="file" @change="handleFileSelect" accept=".csv,.CSV,.xlsx,.xls" class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"/>
          <div class="p-6 text-center">
            <p v-if="!uploadedFile" class="text-sm text-[var(--bb-text-secondary)]">{{ t('import.dragHintShort') }}</p>
            <p v-else class="text-sm text-[var(--bb-blue)] font-medium">{{ uploadedFile.name }}</p>
            <p class="text-xs bb-muted mt-1">{{ t('import.supportedFormatShort') }}</p>
          </div>
        </div>
        <button @click="startImport" :disabled="!uploadedFile || !importType || isUploading" class="bb-button-primary w-full mt-5 disabled:opacity-40">
          <span v-if="isUploading" class="flex items-center justify-center gap-2"><svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>{{ t('import.importing') }}</span>
          <span v-else>{{ t('import.startImport') }}</span>
        </button>
      </div>
    </div>

    <BillFormModal :visible="showAddModal" :bill="newBill" :title="t('bill.addTitle')" :is-saving="isSaving" @close="closeAddModal" @save="saveBill" />
    <BillFormModal :visible="showEditModal" :bill="editingBill" :title="t('bill.editTitle')" :is-saving="isSaving" @close="closeEditModal" @save="updateBill" />
    <DeleteConfirmModal :visible="showDeleteModal" :bill="deletingBill" @close="closeDeleteModal" @confirm="confirmDelete" />

    <div v-if="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl text-white text-sm font-medium animate-slide-down" :class="toast.type === 'success' ? 'bg-[var(--bb-mint)]' : 'bg-[var(--bb-coral)]'">{{ toast.message }}</div>
  </div>
</template>
