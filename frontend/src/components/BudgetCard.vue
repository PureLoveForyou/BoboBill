<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  status: { type: Object, default: null }
})

const { t } = useI18n()

const hasBudget = computed(() => props.status && props.status.monthly_total > 0)
const totalPercentage = computed(() => hasBudget.value ? Math.min(props.status.percentage, 100) : 0)
const isOverBudget = computed(() => hasBudget.value && props.status.over_budget)
const isNearBudget = computed(() => hasBudget.value && !props.status.over_budget && props.status.percentage >= 80)

const progressColor = computed(() => {
  if (isOverBudget.value) return 'bg-error'
  if (isNearBudget.value) return 'bg-warning'
  return 'bg-success'
})

const barTrackColor = computed(() => {
  if (isOverBudget.value) return 'bg-error/20'
  if (isNearBudget.value) return 'bg-warning/20'
  return 'bg-success/20'
})

const sortedCategoryStatus = computed(() => {
  if (!props.status?.category_status) return []
  return Object.entries(props.status.category_status)
    .filter(([, v]) => v.budget > 0)
    .sort((a, b) => b[1].percentage - a[1].percentage)
})
</script>

<template>
  <div v-if="hasBudget" class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-bold">{{ t('budget.budgetStatus') }}</h3>
      <span
        v-if="isOverBudget"
        class="px-2.5 py-1 rounded-full text-xs font-semibold bg-error/10 text-error"
      >
        {{ t('budget.overBudget') }}
      </span>
      <span
        v-else-if="isNearBudget"
        class="px-2.5 py-1 rounded-full text-xs font-semibold bg-warning/10 text-warning"
      >
        {{ t('budget.percentage', { percent: Math.round(status.percentage) }) }}
      </span>
    </div>

    <!-- Alert -->
    <div
      v-if="isOverBudget"
      class="mb-4 p-3 rounded-xl bg-error/10 text-error text-sm font-medium flex items-center gap-2"
    >
      <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      {{ t('budget.overBudgetAlert', { amount: '¥' + Math.abs(status.remaining).toLocaleString() }) }}
    </div>

    <!-- Total Budget Bar -->
    <div class="mb-4">
      <div class="flex justify-between text-sm mb-1.5">
        <span class="text-base-content/60">{{ t('budget.totalSpent') }}</span>
        <span class="font-semibold">
          ¥{{ status.total_spent.toLocaleString() }}
          <span class="text-base-content/40 font-normal">/ ¥{{ status.monthly_total.toLocaleString() }}</span>
        </span>
      </div>
      <div class="h-2.5 rounded-full overflow-hidden" :class="barTrackColor">
        <div
          class="h-full rounded-full transition-all duration-500"
          :class="progressColor"
          :style="{ width: totalPercentage + '%' }"
        ></div>
      </div>
      <div class="flex justify-between text-xs mt-1">
        <span :class="isOverBudget ? 'text-error' : 'text-base-content/40'">
          {{ t('budget.percentage', { percent: Math.round(status.percentage) }) }}
        </span>
        <span v-if="!isOverBudget" class="text-base-content/40">
          {{ t('budget.remaining') }}: ¥{{ status.remaining.toLocaleString() }}
        </span>
      </div>
    </div>

    <!-- Category Budgets -->
    <div v-if="sortedCategoryStatus.length > 0" class="space-y-3">
      <div
        v-for="[cat, info] in sortedCategoryStatus"
        :key="cat"
        class="space-y-1"
      >
        <div class="flex justify-between text-xs">
          <span class="font-medium">{{ t('categories.' + cat) }}</span>
          <span>
            ¥{{ info.spent.toLocaleString() }}
            <span class="text-base-content/40">/ ¥{{ info.budget.toLocaleString() }}</span>
          </span>
        </div>
        <div class="h-1.5 rounded-full overflow-hidden" :class="info.over_budget ? 'bg-error/20' : 'bg-base-200'">
          <div
            class="h-full rounded-full transition-all duration-500"
            :class="info.over_budget ? 'bg-error' : (info.percentage >= 80 ? 'bg-warning' : 'bg-success')"
            :style="{ width: Math.min(info.percentage, 100) + '%' }"
          ></div>
        </div>
      </div>
    </div>
  </div>

  <!-- No Budget Hint -->
  <div v-else class="rounded-2xl bg-gradient-to-br from-base-100 to-base-200/30 border border-base-200/50 p-5">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
        <svg class="w-5 h-5 text-primary/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>
      <div>
        <div class="text-sm font-semibold">{{ t('budget.noBudget') }}</div>
        <div class="text-xs text-base-content/50">{{ t('budget.noBudgetHint') }}</div>
      </div>
    </div>
  </div>
</template>
