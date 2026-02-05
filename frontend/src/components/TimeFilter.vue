<script setup>
import { ref, computed, watch } from 'vue'
import dayjs from 'dayjs'
import weekOfYear from 'dayjs/plugin/weekOfYear'
import isBetween from 'dayjs/plugin/isBetween'

dayjs.extend(weekOfYear)
dayjs.extend(isBetween)

// 报表类型
const reportTypes = ['周报', '月报', '季报', '年报', '自定义']
const selectedReportType = ref('月报')

// 日期选择
const currentYear = ref(dayjs().year())
const currentWeek = ref(dayjs().week())
const currentMonth = ref(dayjs().month() + 1)
const currentQuarter = ref(Math.ceil(dayjs().month() + 1 / 3))
const selectedYear = ref(currentYear.value)
const selectedWeek = ref(currentWeek.value)
const selectedMonth = ref(currentMonth.value)
const selectedQuarter = ref(currentQuarter.value)

// 自定义日期范围
const customStartDate = ref(dayjs().subtract(30, 'day').format('YYYY-MM-DD'))
const customEndDate = ref(dayjs().format('YYYY-MM-DD'))
const showCustomPicker = ref(false)

// 数据选项
const years = Array.from({ length: 5 }, (_, i) => dayjs().year() - i)
const weeks = Array.from({ length: 53 }, (_, i) => i + 1)
const months = Array.from({ length: 12 }, (_, i) => i + 1)
const quarters = [1, 2, 3, 4]

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
      const start = dayjs(customStartDate.value)
      const end = dayjs(customEndDate.value)
      const days = end.diff(start, 'day') + 1
      return {
        start: customStartDate.value,
        end: customEndDate.value,
        label: `${customStartDate.value} ~ ${customEndDate.value} (${days}天)`
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
  if (dayjs(customStartDate.value).isAfter(dayjs(customEndDate.value))) {
    const temp = customStartDate.value
    customStartDate.value = customEndDate.value
    customEndDate.value = temp
  }
  showCustomPicker.value = false
}

// Emits
const emit = defineEmits(['change'])

// 监听变化
watch([selectedReportType, selectedYear, selectedMonth, selectedWeek, selectedQuarter, customStartDate, customEndDate], () => {
  emit('change', {
    type: selectedReportType.value,
    range: timeRange.value,
    comparisons: comparisonRanges.value
  })
}, { immediate: true, deep: true })
</script>

<template>
  <div class="bg-base-200 rounded-box p-4">
    <!-- 报表类型 Tab -->
    <div class="tabs tabs-boxed mb-4">
      <a
        v-for="type in reportTypes"
        :key="type"
        class="tab"
        :class="{ 'tab-active': selectedReportType === type }"
        @click="switchReportType(type)"
      >
        {{ type }}
      </a>
    </div>

    <!-- 时间选择器 -->
    <div v-if="!showCustomPicker" class="flex items-center gap-4">
      <!-- 周报选择 -->
      <template v-if="selectedReportType === '周报'">
        <div class="flex items-center gap-2">
          <select v-model="selectedYear" class="select select-bordered select-sm">
            <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
          </select>
          <span>第</span>
          <select v-model="selectedWeek" class="select select-bordered select-sm w-20">
            <option v-for="week in weeks" :key="week" :value="week">{{ week }}</option>
          </select>
          <span>周</span>
        </div>
      </template>

      <!-- 月报选择 -->
      <template v-else-if="selectedReportType === '月报'">
        <div class="flex items-center gap-2">
          <select v-model="selectedYear" class="select select-bordered select-sm">
            <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
          </select>
          <select v-model="selectedMonth" class="select select-bordered select-sm">
            <option v-for="month in months" :key="month" :value="month">{{ month }}月</option>
          </select>
        </div>
      </template>

      <!-- 季报选择 -->
      <template v-else-if="selectedReportType === '季报'">
        <div class="flex items-center gap-2">
          <select v-model="selectedYear" class="select select-bordered select-sm">
            <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
          </select>
          <select v-model="selectedQuarter" class="select select-bordered select-sm">
            <option v-for="quarter in quarters" :key="quarter" :value="quarter">Q{{ quarter }}</option>
          </select>
        </div>
      </template>

      <!-- 年报选择 -->
      <template v-else-if="selectedReportType === '年报'">
        <div class="flex items-center gap-2">
          <select v-model="selectedYear" class="select select-bordered select-sm">
            <option v-for="year in years" :key="year" :value="year">{{ year }}年</option>
          </select>
        </div>
      </template>

      <!-- 显示当前选中的时间范围 -->
      <div class="text-sm font-medium text-primary">
        {{ timeRange.label }}
      </div>
    </div>

    <!-- 自定义日期范围选择器 -->
    <div v-else class="flex flex-col gap-3">
      <div class="flex items-center gap-4">
        <div class="flex-1">
          <label class="label">
            <span class="label-text">开始日期</span>
          </label>
          <input v-model="customStartDate" type="date" class="input input-bordered w-full" />
        </div>
        <div class="flex-1">
          <label class="label">
            <span class="label-text">结束日期</span>
          </label>
          <input v-model="customEndDate" type="date" class="input input-bordered w-full" />
        </div>
      </div>
      <div class="flex justify-end gap-2">
        <button @click="showCustomPicker = false" class="btn btn-ghost btn-sm">取消</button>
        <button @click="confirmCustomRange" class="btn btn-primary btn-sm">确认</button>
      </div>
    </div>
  </div>
</template>
