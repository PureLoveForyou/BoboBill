<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import weekOfYear from 'dayjs/plugin/weekOfYear'
import isBetween from 'dayjs/plugin/isBetween'
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'

dayjs.extend(weekOfYear)
dayjs.extend(isBetween)

const { t } = useI18n()

const reportTypeKeys = ['weekly', 'monthly', 'quarterly', 'yearly', 'custom']
const selectedReportType = ref('monthly')

const currentYear = ref(dayjs().year())
const currentWeek = ref(dayjs().week())
const currentMonth = ref(dayjs().month() + 1)
const currentQuarter = ref(Math.ceil((dayjs().month() + 1) / 3))
const selectedYear = ref(currentYear.value)
const selectedWeek = ref(currentWeek.value)
const selectedMonth = ref(currentMonth.value)
const selectedQuarter = ref(currentQuarter.value)

const customDateRange = ref([dayjs().subtract(30, 'day').toDate(), dayjs().toDate()])
const showCustomPicker = ref(false)

const years = Array.from({ length: 5 }, (_, i) => ({ value: dayjs().year() - i, label: t('timeFilter.yearOnly', { year: dayjs().year() - i }) }))
const weeks = Array.from({ length: 53 }, (_, i) => ({ value: i + 1, label: `${i + 1}` }))
const months = Array.from({ length: 12 }, (_, i) => ({ value: i + 1, label: t('timeFilter.monthOnly', { month: i + 1 }) }))
const quarters = [1, 2, 3, 4].map(q => ({ value: q, label: `Q${q}` }))

const timeRange = computed(() => {
  switch (selectedReportType.value) {
    case 'weekly': {
      const weekStart = dayjs().year(selectedYear.value).week(selectedWeek.value).startOf('week').add(1, 'day')
      const weekEnd = weekStart.endOf('week').add(1, 'day')
      return {
        start: weekStart.format('YYYY-MM-DD'),
        end: weekEnd.format('YYYY-MM-DD'),
        label: t('timeFilter.weekYear', { year: selectedYear.value, week: selectedWeek.value })
      }
    }
    case 'monthly': {
      const monthStart = dayjs().year(selectedYear.value).month(selectedMonth.value - 1).startOf('month')
      const monthEnd = monthStart.endOf('month')
      return {
        start: monthStart.format('YYYY-MM-DD'),
        end: monthEnd.format('YYYY-MM-DD'),
        label: t('timeFilter.monthYear', { year: selectedYear.value, month: selectedMonth.value })
      }
    }
    case 'quarterly': {
      const quarterStart = dayjs().year(selectedYear.value).month((selectedQuarter.value - 1) * 3).startOf('month')
      const quarterEnd = quarterStart.add(2, 'month').endOf('month')
      return {
        start: quarterStart.format('YYYY-MM-DD'),
        end: quarterEnd.format('YYYY-MM-DD'),
        label: `${selectedYear.value}Q${selectedQuarter.value}`
      }
    }
    case 'yearly': {
      const yearStart = dayjs().year(selectedYear.value).startOf('year')
      const yearEnd = yearStart.endOf('year')
      return {
        start: yearStart.format('YYYY-MM-DD'),
        end: yearEnd.format('YYYY-MM-DD'),
        label: t('timeFilter.yearOnly', { year: selectedYear.value })
      }
    }
    case 'custom': {
      if (!customDateRange.value || customDateRange.value.length !== 2) {
        return { start: '', end: '', label: '' }
      }
      const start = dayjs(customDateRange.value[0])
      const end = dayjs(customDateRange.value[1])
      return {
        start: start.format('YYYY-MM-DD'),
        end: end.format('YYYY-MM-DD'),
        label: `${start.format('MM/DD')}-${end.format('MM/DD')}`
      }
    }
    default:
      return { start: '', end: '', label: '' }
  }
})

const comparisonRanges = computed(() => {
  const ranges = []
  const { start, end } = timeRange.value
  const days = dayjs(end).diff(dayjs(start), 'day') + 1

  switch (selectedReportType.value) {
    case 'weekly':
      for (let i = 5; i >= 0; i--) {
        const week = selectedWeek.value - i
        const weekStart = dayjs().year(selectedYear.value).week(week).startOf('week').add(1, 'day')
        const weekEnd = weekStart.endOf('week').add(1, 'day')
        ranges.push({
          label: t('timeFilter.weekPrefix', { week }),
          start: weekStart.format('YYYY-MM-DD'),
          end: weekEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break
    case 'monthly':
      for (let i = 5; i >= 0; i--) {
        const month = selectedMonth.value - i
        if (month < 1) continue
        const monthStart = dayjs().year(selectedYear.value).month(month - 1).startOf('month')
        const monthEnd = monthStart.endOf('month')
        ranges.push({
          label: t('timeFilter.monthOnly', { month }),
          start: monthStart.format('YYYY-MM-DD'),
          end: monthEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break
    case 'quarterly':
      for (let i = 5; i >= 0; i--) {
        const quarter = selectedQuarter.value - i
        if (quarter < 1) continue
        const quarterStart = dayjs().year(selectedYear.value).month((quarter - 1) * 3).startOf('month')
        const quarterEnd = quarterStart.add(2, 'month').endOf('month')
        ranges.push({
          label: `Q${quarter}`,
          start: quarterStart.format('YYYY-MM-DD'),
          end: quarterEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break
    case 'yearly':
      for (let i = 5; i >= 0; i--) {
        const year = selectedYear.value - i
        const yearStart = dayjs().year(year).startOf('year')
        const yearEnd = yearStart.endOf('year')
        ranges.push({
          label: t('timeFilter.yearOnly', { year }),
          start: yearStart.format('YYYY-MM-DD'),
          end: yearEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break
    case 'custom':
      const chunkDays = Math.ceil(days / 6)
      const chunkStart = dayjs(start)
      for (let i = 0; i < 6; i++) {
        const rangeStart = chunkStart.add(i * chunkDays, 'day')
        const rangeEnd = rangeStart.add(chunkDays - 1, 'day')
        if (rangeStart.isAfter(end)) break
        ranges.push({
          label: t('timeFilter.range', { n: i + 1 }),
          start: rangeStart.format('YYYY-MM-DD'),
          end: rangeEnd.isAfter(end) ? end : rangeEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break
  }

  return ranges
})

const switchReportType = (type) => {
  selectedReportType.value = type
  if (type === 'custom') {
    showCustomPicker.value = true
  } else {
    showCustomPicker.value = false
  }
}

const confirmCustomRange = () => {
  if (!customDateRange.value || customDateRange.value.length !== 2) return
  const start = dayjs(customDateRange.value[0])
  const end = dayjs(customDateRange.value[1])
  if (start.isAfter(end)) {
    customDateRange.value = [customDateRange.value[1], customDateRange.value[0]]
  }
  showCustomPicker.value = false
}

const emit = defineEmits(['change'])

watch([selectedReportType, selectedYear, selectedMonth, selectedWeek, selectedQuarter, customDateRange], () => {
  emit('change', {
    type: selectedReportType.value,
    range: timeRange.value,
    comparisons: comparisonRanges.value
  })
}, { immediate: true, deep: true })
</script>

<template>
  <div class="flex items-center gap-3 flex-wrap">
    <div class="flex gap-1.5 p-1.5 bg-base-200/50 rounded-2xl">
      <button
        v-for="typeKey in reportTypeKeys"
        :key="typeKey"
        class="px-4 py-2 rounded-xl text-sm font-semibold transition-all"
        :class="selectedReportType === typeKey 
          ? 'bg-base-100 text-base-content shadow-sm' 
          : 'text-base-content/50 hover:text-base-content'"
        @click="switchReportType(typeKey)"
      >
        {{ t('timeFilter.' + typeKey) }}
      </button>
    </div>

    <template v-if="!showCustomPicker">
      <select
        v-if="selectedReportType === 'weekly' || selectedReportType === 'monthly' || selectedReportType === 'quarterly' || selectedReportType === 'yearly'"
        v-model="selectedYear"
        class="select select-bordered rounded-xl bg-base-100 text-sm font-medium w-28"
      >
        <option v-for="y in years" :key="y.value" :value="y.value">{{ y.label }}</option>
      </select>

      <select
        v-if="selectedReportType === 'weekly'"
        v-model="selectedWeek"
        class="select select-bordered rounded-xl bg-base-100 text-sm font-medium w-24"
      >
        <option v-for="w in weeks" :key="w.value" :value="w.value">{{ t('timeFilter.weekPrefix', { week: w.label }) }}</option>
      </select>

      <select
        v-if="selectedReportType === 'monthly'"
        v-model="selectedMonth"
        class="select select-bordered rounded-xl bg-base-100 text-sm font-medium w-24"
      >
        <option v-for="m in months" :key="m.value" :value="m.value">{{ m.label }}</option>
      </select>

      <select
        v-if="selectedReportType === 'quarterly'"
        v-model="selectedQuarter"
        class="select select-bordered rounded-xl bg-base-100 text-sm font-medium w-24"
      >
        <option v-for="q in quarters" :key="q.value" :value="q.value">{{ q.label }}</option>
      </select>

      <div class="flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-xl">
        <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span class="text-sm font-semibold text-primary">{{ timeRange.label }}</span>
      </div>
    </template>

    <template v-else>
      <VueDatePicker
        v-model="customDateRange"
        range
        :enable-time-picker="false"
        :format="'MM/dd'"
        :preview-format="'MM/dd'"
        :placeholder="t('timeFilter.selectDate')"
        class="compact-datepicker"
        :clearable="false"
        style="width: 180px;"
      />
      <button @click="confirmCustomRange" class="btn btn-primary rounded-xl px-5 text-sm font-semibold">{{ t('timeFilter.confirm') }}</button>
    </template>
  </div>
</template>

<style>
.compact-datepicker {
  --dp-font-family: inherit;
  --dp-border-radius: 8px;
  --dp-input-padding: 6px 10px;
  --dp-font-size: 12px;
  --dp-border-color: rgba(0, 0, 0, 0.1);
  --dp-primary-color: hsl(var(--p));
  --dp-primary-text-color: hsl(var(--pc));
}

.compact-datepicker .dp__input {
  border: 1px solid var(--dp-border-color);
  border-radius: var(--dp-border-radius);
  background: hsl(var(--b1));
  font-size: 12px;
}

.dp__menu {
  border-radius: 12px !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1) !important;
}
</style>
