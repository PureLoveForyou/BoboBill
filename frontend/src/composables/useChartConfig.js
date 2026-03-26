import { computed } from 'vue'
import { CHART_COLORS } from '../constants/bill'

export function useChartConfig({
  currentTheme, trendCategories,
  categoryType, categoryLabels, categorySeries,
  pieSelectedCategory, expenseLabels, incomeLabels, totalExpense, totalIncome,
  comparisonCategories
}) {
  const getTextColor = () => currentTheme.value === 'dark' ? '#ffffff' : '#1f2937'

  const trendOptions = computed(() => {
    const textColor = getTextColor()
    return {
      chart: { type: 'area', fontFamily: 'inherit', toolbar: { show: false }, animations: { enabled: true } },
      colors: CHART_COLORS.income,
      fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.05, stops: [0, 100] } },
      stroke: { curve: 'smooth', width: 2 },
      dataLabels: { enabled: false },
      xaxis: {
        categories: trendCategories.value,
        labels: { style: { colors: Array(50).fill(textColor) }, rotate: 0, hideOverlappingLabels: true, trim: false, formatter: (value) => value || '' }
      },
      yaxis: {
        labels: { style: { colors: Array(50).fill(textColor) }, formatter: (value) => '¥' + (value / 1000) + 'k' }
      },
      grid: { borderColor: currentTheme.value === 'dark' ? '#374151' : '#e5e7eb', padding: { top: 0 } },
      legend: { labels: { colors: textColor }, position: 'top', horizontalAlign: 'right', offsetY: -5, itemMargin: { horizontal: 15 } },
      tooltip: {
        theme: 'dark',
        x: { formatter: (value, { dataPointIndex }) => trendCategories.value[dataPointIndex] || value },
        y: { formatter: (value) => '¥' + value.toLocaleString() }
      }
    }
  })

  const categoryOptionsChart = computed(() => {
    const textColor = getTextColor()
    return {
      chart: {
        type: 'donut',
        fontFamily: 'inherit',
        events: {
          dataPointSelection: (event, chartContext, config) => {
            const labelIndex = config.dataPointIndex
            const labels = categoryType.value === 'expense' ? expenseLabels.value : incomeLabels.value
            if (labelIndex >= 0 && labelIndex < labels.length) {
              const clickedCategory = labels[labelIndex]
              pieSelectedCategory.value = pieSelectedCategory.value === clickedCategory ? null : clickedCategory
            }
          }
        }
      },
      labels: categoryLabels.value,
      colors: categoryType.value === 'expense' ? CHART_COLORS.expenseCategory : CHART_COLORS.incomeCategory,
      plotOptions: {
        pie: {
          donut: {
            size: '65%',
            labels: {
              show: true,
              name: { show: true, color: textColor },
              value: { show: true, color: textColor },
              total: {
                show: true,
                label: categoryType.value === 'expense' ? '总支出' : '总收入',
                color: textColor,
                formatter: () => '¥' + (categoryType.value === 'expense' ? totalExpense.value : totalIncome.value).toLocaleString()
              }
            }
          }
        }
      },
      dataLabels: { enabled: false },
      legend: { position: 'bottom', labels: { colors: textColor } },
      tooltip: {
        theme: 'dark',
        y: {
          formatter: (value) => {
            const actualTotal = categoryType.value === 'expense' ? totalExpense.value : totalIncome.value
            return `${value}% (¥${Math.round(actualTotal * value / 100).toLocaleString()})`
          }
        }
      }
    }
  })

  const comparisonOptions = computed(() => {
    const textColor = getTextColor()
    return {
      chart: { type: 'bar', fontFamily: 'inherit', toolbar: { show: false }, animations: { enabled: true } },
      colors: CHART_COLORS.income,
      plotOptions: { bar: { horizontal: false, columnWidth: '60%', borderRadius: 4 } },
      dataLabels: { enabled: false },
      xaxis: {
        categories: comparisonCategories.value,
        labels: { style: { colors: Array(50).fill(textColor) } }
      },
      yaxis: {
        labels: { style: { colors: Array(50).fill(textColor) }, formatter: (value) => '¥' + (value / 1000) + 'k' }
      },
      grid: { borderColor: currentTheme.value === 'dark' ? '#374151' : '#e5e7eb' },
      legend: { labels: { colors: textColor }, position: 'top', horizontalAlign: 'right', offsetY: -5, itemMargin: { horizontal: 15 } },
      tooltip: { theme: 'dark', y: { formatter: (value) => '¥' + value.toLocaleString() } }
    }
  })

  return { trendOptions, categoryOptionsChart, comparisonOptions }
}
