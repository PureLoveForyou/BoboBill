<script setup>
import { ref, computed, watch } from 'vue'
import dayjs from 'dayjs'
import weekOfYear from 'dayjs/plugin/weekOfYear'
import isBetween from 'dayjs/plugin/isBetween'
import { VueDatePicker } from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'
import ModernSelect from './ModernSelect.vue'

dayjs.extend(weekOfYear)
dayjs.extend(isBetween)

// 报表类型
const reportTypes = ['周报', '月报', '季报', '年报', '自定义']
const selectedReportType = ref('月报')

// 日期选择
const currentYear = ref(dayjs().year())
const currentWeek = ref(dayjs().week())
const currentMonth = ref(dayjs().month() + 1)
const currentQuarter = ref(Math.ceil((dayjs().month() + 1) / 3))
const selectedYear = ref(currentYear.value)
const selectedWeek = ref(currentWeek.value)
const selectedMonth = ref(currentMonth.value)
const selectedQuarter = ref(currentQuarter.value)

// 自定义日期范围
const customDateRange = ref([dayjs().subtract(30, 'day').toDate(), dayjs().toDate()])
const showCustomPicker = ref(false)

// 数据选项
const years = Array.from({ length: 5 }, (_, i) => ({ value: dayjs().year() - i, label: `${dayjs().year() - i}年` }))
const weeks = Array.from({ length: 53 }, (_, i) => ({ value: i + 1, label: `${i + 1}` }))
const months = Array.from({ length: 12 }, (_, i) => ({ value: i + 1, label: `${i + 1}月` }))
const quarters = [1, 2, 3, 4].map(q => ({ value: q, label: `Q${q}` }))

// 计算属性：当前选中的时间范围
const timeRange = computed(() => {
  switch (selectedReportType.value) {
    case '周报': {
      const weekStart = dayjs().year(selectedYear.value).week(selectedWeek.value).startOf('week').add(1, 'day')
      const weekEnd = weekStart.endOf('week').add(1, 'day')
      return {
        start: weekStart.format('YYYY-MM-DD'),
        end: weekEnd.format('YYYY-MM-DD'),
        label: `${selectedYear.value}年 第${selectedWeek.value}周 (${weekStart.format('MM/DD')} - ${weekEnd.format('MM/DD')})`
      }
    }
    case '月报': {
      const monthStart = dayjs().year(selectedYear.value).month(selectedMonth.value - 1).startOf('month')
      const monthEnd = monthStart.endOf('month')
      return {
        start: monthStart.format('YYYY-MM-DD'),
        end: monthEnd.format('YYYY-MM-DD'),
        label: `${selectedYear.value}年 ${selectedMonth.value}月`
      }
    }
    case '季报': {
      const quarterStart = dayjs().year(selectedYear.value).month((selectedQuarter.value - 1) * 3).startOf('month')
      const quarterEnd = quarterStart.add(2, 'month').endOf('month')
      return {
        start: quarterStart.format('YYYY-MM-DD'),
        end: quarterEnd.format('YYYY-MM-DD'),
        label: `${selectedYear.value}年 Q${selectedQuarter.value}`
      }
    }
    case '年报': {
      const yearStart = dayjs().year(selectedYear.value).startOf('year')
      const yearEnd = yearStart.endOf('year')
      return {
        start: yearStart.format('YYYY-MM-DD'),
        end: yearEnd.format('YYYY-MM-DD'),
        label: `${selectedYear.value}年`
      }
    }
    case '自定义': {
      if (!customDateRange.value || customDateRange.value.length !== 2) {
        return { start: '', end: '', label: '' }
      }
      const start = dayjs(customDateRange.value[0])
      const end = dayjs(customDateRange.value[1])
      const days = end.diff(start, 'day') + 1
      return {
        start: start.format('YYYY-MM-DD'),
        end: end.format('YYYY-MM-DD'),
        label: `${start.format('YYYY-MM-DD')} ~ ${end.format('YYYY-MM-DD')} (${days}天)`
      }
    }
    default:
      return { start: '', end: '', label: '' }
  }
})

// 计算属性：用于柱状图对比的6个周期
const comparisonRanges = computed(() => {
  const ranges = []
  const { start, end } = timeRange.value
  const days = dayjs(end).diff(dayjs(start), 'day') + 1

  switch (selectedReportType.value) {
    case '周报':
      for (let i = 5; i >= 0; i--) {
        const week = selectedWeek.value - i
        const weekStart = dayjs().year(selectedYear.value).week(week).startOf('week').add(1, 'day')
        const weekEnd = weekStart.endOf('week').add(1, 'day')
        ranges.push({
          label: `第${week}周`,
          start: weekStart.format('YYYY-MM-DD'),
          end: weekEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break

    case '月报':
      for (let i = 5; i >= 0; i--) {
        const month = selectedMonth.value - i
        if (month < 1) continue
        const monthStart = dayjs().year(selectedYear.value).month(month - 1).startOf('month')
        const monthEnd = monthStart.endOf('month')
        ranges.push({
          label: `${month}月`,
          start: monthStart.format('YYYY-MM-DD'),
          end: monthEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break

    case '季报':
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

    case '年报':
      for (let i = 5; i >= 0; i--) {
        const year = selectedYear.value - i
        const yearStart = dayjs().year(year).startOf('year')
        const yearEnd = yearStart.endOf('year')
        ranges.push({
          label: `${year}年`,
          start: yearStart.format('YYYY-MM-DD'),
          end: yearEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break

    case '自定义':
      const chunkDays = Math.ceil(days / 6)
      const chunkStart = dayjs(start)
      for (let i = 0; i < 6; i++) {
        const rangeStart = chunkStart.add(i * chunkDays, 'day')
        const rangeEnd = rangeStart.add(chunkDays - 1, 'day')
        if (rangeStart.isAfter(end)) break
        ranges.push({
          label: `区间${i + 1}`,
          start: rangeStart.format('YYYY-MM-DD'),
          end: rangeEnd.isAfter(end) ? end : rangeEnd.format('YYYY-MM-DD'),
          isSelected: i === 0
        })
      }
      break
  }

  return ranges
})

// 切换报表类型
const switchReportType = (type) => {
  selectedReportType.value = type
  if (type === '自定义') {
    showCustomPicker.value = true
  } else {
    showCustomPicker.value = false
  }
}

// 自定义日期确认
const confirmCustomRange = () => {
  if (!customDateRange.value || customDateRange.value.length !== 2) return
  
  const start = dayjs(customDateRange.value[0])
  const end = dayjs(customDateRange.value[1])
  
  if (start.isAfter(end)) {
    customDateRange.value = [customDateRange.value[1], customDateRange.value[0]]
  }
  showCustomPicker.value = false
}

// Emits
const emit = defineEmits(['change'])

// 监听变化
watch([selectedReportType, selectedYear, selectedMonth, selectedWeek, selectedQuarter, customDateRange], () => {
  emit('change', {
    type: selectedReportType.value,
    range: timeRange.value,
    comparisons: comparisonRanges.value
  })
}, { immediate: true, deep: true })
</script>

<template>
  <div class="relative rounded-3xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/30 border border-base-200/50 backdrop-blur-sm shadow-sm" style="z-index: 100;">
    <!-- 报表类型分段控制器 -->
    <div class="p-6 pb-4">
      <div class="flex gap-1.5 p-1.5 bg-base-200/50 rounded-2xl">
        <button
          v-for="type in reportTypes"
          :key="type"
          class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300"
          :class="selectedReportType === type 
            ? 'bg-base-100 text-base-content shadow-sm' 
            : 'text-base-content/60 hover:text-base-content'"
          @click="switchReportType(type)"
        >
          {{ type }}
        </button>
      </div>
    </div>

    <!-- 时间选择器 -->
    <div v-if="!showCustomPicker" class="px-6 pb-6">
      <div class="flex items-center justify-between gap-4">
        <!-- 周报选择 -->
        <template v-if="selectedReportType === '周报'">
          <div class="flex items-center gap-3">
            <ModernSelect
              v-model="selectedYear"
              :options="years"
              class="w-32"
            />
            <span class="text-base-content/60 font-medium">第</span>
            <ModernSelect
              v-model="selectedWeek"
              :options="weeks"
              class="w-20"
            />
            <span class="text-base-content/60 font-medium">周</span>
          </div>
        </template>

        <!-- 月报选择 -->
        <template v-else-if="selectedReportType === '月报'">
          <div class="flex items-center gap-3">
            <ModernSelect
              v-model="selectedYear"
              :options="years"
              class="w-32"
            />
            <ModernSelect
              v-model="selectedMonth"
              :options="months"
              class="w-24"
            />
          </div>
        </template>

        <!-- 季报选择 -->
        <template v-else-if="selectedReportType === '季报'">
          <div class="flex items-center gap-3">
            <ModernSelect
              v-model="selectedYear"
              :options="years"
              class="w-32"
            />
            <ModernSelect
              v-model="selectedQuarter"
              :options="quarters"
              class="w-24"
            />
          </div>
        </template>

        <!-- 年报选择 -->
        <template v-else-if="selectedReportType === '年报'">
          <div class="flex items-center gap-3">
            <ModernSelect
              v-model="selectedYear"
              :options="years"
              class="w-32"
            />
          </div>
        </template>

        <!-- 显示当前选中的时间范围 -->
        <div class="flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-xl">
          <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span class="text-sm font-semibold text-primary">{{ timeRange.label }}</span>
        </div>
      </div>
    </div>

    <!-- 自定义日期范围选择器 -->
    <div v-else class="px-6 pb-6">
      <div class="flex flex-col gap-4">
        <div>
          <label class="label pb-2">
            <span class="label-text font-semibold text-base-content/70">选择日期范围</span>
          </label>
          <VueDatePicker
            v-model="customDateRange"
            range
            :enable-time-picker="false"
            :format="'yyyy-MM-dd'"
            :preview-format="'yyyy-MM-dd'"
            placeholder="选择开始和结束日期"
            class="modern-datepicker"
            :clearable="false"
            :transitions="true"
          />
        </div>
        <div class="flex justify-end gap-3 pt-2">
          <button @click="showCustomPicker = false" class="btn btn-ghost btn-sm rounded-xl px-6 font-semibold hover:bg-base-200/50 transition-all">取消</button>
          <button @click="confirmCustomRange" class="btn btn-primary btn-sm rounded-xl px-6 font-semibold shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 transition-all">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.modern-datepicker {
  --dp-font-family: inherit;
  --dp-border-radius: 12px;
  --dp-input-padding: 12px 16px;
  --dp-font-size: 14px;
  --dp-border-color: rgba(0, 0, 0, 0.05);
  --dp-border-color-hover: rgba(0, 0, 0, 0.1);
  --dp-primary-color: hsl(var(--p));
  --dp-primary-text-color: hsl(var(--pc));
}

.modern-datepicker .dp__input {
  border: 1px solid var(--dp-border-color);
  border-radius: var(--dp-border-radius);
  background: hsl(var(--b1));
  transition: all 0.3s ease;
}

.modern-datepicker .dp__input:hover {
  border-color: var(--dp-border-color-hover);
}

.modern-datepicker .dp__input:focus {
  outline: none;
  border-color: var(--dp-primary-color);
  box-shadow: 0 0 0 3px rgba(var(--p), 0.1);
}

.dp__menu {
  border-radius: 16px !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1) !important;
  font-family: inherit !important;
}

.dp__calendar_header {
  font-weight: 600;
}

.dp__cell_inner {
  border-radius: 8px !important;
  transition: all 0.2s ease !important;
}

.dp__cell_inner:hover {
  background: rgba(var(--p), 0.1) !important;
}

.dp__cell_inner.dp__cell_active {
  background: var(--dp-primary-color) !important;
  color: var(--dp-primary-text-color) !important;
}

.dp__range_start,
.dp__range_end {
  background: var(--dp-primary-color) !important;
  color: var(--dp-primary-text-color) !important;
}

.dp__range_between {
  background: rgba(var(--p), 0.1) !important;
}
</style>
