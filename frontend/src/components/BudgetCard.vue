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
  if (isOverBudget.value) return 'var(--bb-coral)'
  if (isNearBudget.value) return 'var(--bb-orange)'
  return 'var(--bb-mint)'
})

const barTrackColor = computed(() => {
  if (isOverBudget.value) return 'rgba(255,107,95,0.12)'
  if (isNearBudget.value) return 'rgba(255,159,10,0.12)'
  return 'var(--bb-bg-soft)'
})

const sortedCategoryStatus = computed(() => {
  if (!props.status?.category_status) return []
  return Object.entries(props.status.category_status)
    .filter(([, v]) => v.budget > 0)
    .sort((a, b) => b[1].percentage - a[1].percentage)
})
</script>

<template>
  <div v-if="hasBudget" class="bb-card p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="bb-section-title">{{ t('budget.budgetStatus') }}</h3>
      <span
        v-if="isOverBudget"
        class="bb-chip text-[var(--bb-coral)] bg-[var(--bb-coral)]/8 border-[var(--bb-coral)]/20"
      >
        {{ t('budget.overBudget') }}
      </span>
      <span
        v-else-if="isNearBudget"
        class="bb-chip text-[var(--bb-orange)] bg-[var(--bb-orange)]/8 border-[var(--bb-orange)]/20"
      >
        {{ t('budget.percentage', { percent: Math.round(status.percentage) }) }}
      </span>
    </div>

    <div
      v-if="isOverBudget"
      class="mb-4 p-3 rounded-xl bg-[var(--bb-coral)]/8 text-[var(--bb-coral)] text-sm font-medium flex items-center gap-2"
    >
      <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      {{ t('budget.overBudgetAlert', { amount: t('common.currency') + Math.abs(status.remaining).toLocaleString() }) }}
    </div>

    <div class="mb-4">
      <div class="flex justify-between text-sm mb-1.5">
        <span class="text-[var(--bb-text-secondary)]">{{ t('budget.totalSpent') }}</span>
        <span class="font-semibold text-[var(--bb-text)]">
          {{ t('common.currency') }}{{ status.total_spent.toLocaleString() }}
          <span class="text-[var(--bb-text-tertiary)] font-normal">/ {{ t('common.currency') }}{{ status.monthly_total.toLocaleString() }}</span>
        </span>
      </div>
      <div class="h-2.5 rounded-full overflow-hidden" :style="{ backgroundColor: barTrackColor }">
        <div
          class="h-full rounded-full transition-all duration-500"
          :style="{ width: totalPercentage + '%', backgroundColor: progressColor }"
        ></div>
      </div>
      <div class="flex justify-between text-xs mt-1">
        <span :class="isOverBudget ? 'text-[var(--bb-coral)]' : 'text-[var(--bb-text-tertiary)]'">
          {{ t('budget.percentage', { percent: Math.round(status.percentage) }) }}
        </span>
        <span v-if="!isOverBudget" class="text-[var(--bb-text-tertiary)]">
          {{ t('budget.remaining') }}: {{ t('common.currency') }}{{ status.remaining.toLocaleString() }}
        </span>
      </div>
    </div>

    <div v-if="sortedCategoryStatus.length > 0" class="space-y-3">
      <div
        v-for="[cat, info] in sortedCategoryStatus"
        :key="cat"
        class="space-y-1"
      >
        <div class="flex justify-between text-xs">
          <span class="font-medium text-[var(--bb-text-secondary)]">{{ t('categories.' + cat) }}</span>
          <span class="text-[var(--bb-text-tertiary)]">
            {{ t('common.currency') }}{{ info.spent.toLocaleString() }}
            <span>/ {{ t('common.currency') }}{{ info.budget.toLocaleString() }}</span>
          </span>
        </div>
        <div class="h-1.5 rounded-full overflow-hidden" :style="{ backgroundColor: info.over_budget ? 'rgba(255,107,95,0.12)' : 'var(--bb-bg-soft)' }">
          <div
            class="h-full rounded-full transition-all duration-500"
            :style="{ width: Math.min(info.percentage, 100) + '%', backgroundColor: info.over_budget ? 'var(--bb-coral)' : (info.percentage >= 80 ? 'var(--bb-orange)' : 'var(--bb-mint)') }"
          ></div>
        </div>
      </div>
    </div>
  </div>

  <div v-else class="bb-card p-5">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-[var(--bb-bg-soft)] flex items-center justify-center">
        <svg class="w-5 h-5 text-[var(--bb-text-tertiary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      </div>
      <div>
        <div class="text-sm font-semibold text-[var(--bb-text)]">{{ t('budget.noBudget') }}</div>
        <div class="text-xs bb-muted">{{ t('budget.noBudgetHint') }}</div>
      </div>
    </div>
  </div>
</template>
