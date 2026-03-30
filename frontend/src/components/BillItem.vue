<script setup>
import { useI18n } from 'vue-i18n'
import PlatformIcon from './PlatformIcon.vue'
import { PLATFORM_INFO } from '../constants/bill'
import { formatAmount } from '../utils/format'

const { t } = useI18n()

defineProps({
  bill: { type: Object, required: true },
  compact: { type: Boolean, default: false }
})

defineEmits(['edit', 'delete'])

const platformInfo = PLATFORM_INFO
</script>

<template>
  <div
    class="group flex items-center bg-base-200/20 hover:bg-base-200/40 transition-all"
    :class="compact
      ? 'gap-3 p-3 rounded-xl'
      : 'gap-4 p-4 rounded-2xl duration-300 cursor-pointer'"
  >
    <div
      class="shrink-0 bg-gradient-to-br text-white flex items-center justify-center"
      :class="[
        platformInfo[bill.platform]?.color,
        compact ? 'w-9 h-9 rounded-lg' : 'w-11 h-11 rounded-xl shadow-sm'
      ]"
    >
      <PlatformIcon :platform="bill.platform" size="sm" />
    </div>

    <div class="flex-1 min-w-0">
      <div class="flex items-center" :class="compact ? 'gap-1.5' : 'gap-2'">
        <span class="font-medium text-sm truncate">{{ bill.name }}</span>
        <span
          class="shrink-0 text-xs bg-base-200/80 text-base-content/50"
          :class="compact ? 'px-1.5 py-0.5 rounded' : 'px-2 py-0.5 rounded-md'"
        >{{ t('categories.' + (bill.category || '其他')) }}</span>
      </div>
      <div class="text-xs text-base-content/40" :class="compact ? 'mt-0.5' : 'mt-1'">
        {{ bill.date }}<template v-if="compact && bill.note"> · {{ bill.note }}</template>
      </div>
    </div>

    <template v-if="compact">
      <div class="font-semibold text-sm tabular-nums shrink-0" :class="bill.amount >= 0 ? 'text-success' : 'text-base-content'">
        {{ formatAmount(bill.amount) }}
      </div>
      <div class="flex gap-0.5 shrink-0 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
        <button @click="$emit('edit', bill)" class="p-1.5 rounded-lg hover:bg-primary/10 text-primary/60 hover:text-primary transition-all">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button @click="$emit('delete', bill)" class="p-1.5 rounded-lg hover:bg-error/10 text-error/60 hover:text-error transition-all">
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </template>

    <template v-else>
      <div class="text-right flex items-center gap-2">
        <div class="font-semibold tabular-nums mr-2" :class="bill.amount >= 0 ? 'text-success' : 'text-base-content'">
          {{ formatAmount(bill.amount) }}
        </div>
        <button @click.stop="$emit('edit', bill)" class="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-primary/10 text-primary/60 hover:text-primary transition-all" :title="t('common.edit')">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button @click.stop="$emit('delete', bill)" class="p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-error/10 text-error/60 hover:text-error transition-all" :title="t('common.delete')">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </template>
  </div>
</template>
