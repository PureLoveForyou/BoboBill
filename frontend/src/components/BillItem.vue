<script setup>
import { useI18n } from 'vue-i18n'
import PlatformIcon from './PlatformIcon.vue'
import { PLATFORM_INFO } from '../constants/bill'
import { formatAmount } from '../utils/format'

const { t } = useI18n()

const props = defineProps({
  bill: { type: Object, required: true },
  compact: { type: Boolean, default: false },
  selectable: { type: Boolean, default: false },
  selected: { type: Boolean, default: false }
})

const emit = defineEmits(['edit', 'delete', 'toggle-select'])

const platformInfo = PLATFORM_INFO
</script>

<template>
  <div
    class="group relative flex items-center rounded-2xl glass-elegant hover-lift transition-elegant"
    :class="[
      compact ? 'gap-3 p-3' : 'gap-4 p-4',
      selectable ? 'cursor-pointer' : ''
    ]"
    @click="selectable && emit('toggle-select', bill)"
  >
    <div v-if="selectable" class="shrink-0">
      <div
        class="w-6 h-6 rounded-lg border-2 flex items-center justify-center transition-all duration-300"
        :class="selected
          ? 'bg-gradient-elegant border-transparent shadow-md'
          : 'border-base-content/20 hover:border-primary/50'"
      >
        <svg v-if="selected" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    </div>

    <div
      class="shrink-0 bg-gradient-to-br text-white flex items-center justify-center shadow-lg"
      :class="[
        platformInfo[bill.platform]?.color,
        compact ? 'w-11 h-11 rounded-xl' : 'w-12 h-12 rounded-2xl'
      ]"
    >
      <PlatformIcon :platform="bill.platform" size="sm" />
    </div>

    <div class="flex-1 min-w-0">
      <div class="flex items-center" :class="compact ? 'gap-2' : 'gap-2.5'">
        <span class="font-semibold text-sm truncate tracking-tight">{{ bill.name }}</span>
        <span
          class="shrink-0 text-xs font-medium px-2.5 py-1 rounded-lg bg-gradient-to-r from-base-200/60 to-base-100/40 text-base-content/70 border border-base-content/5"
          :class="compact ? '' : ''"
        >{{ t('categories.' + (bill.category || '其他')) }}</span>
      </div>
      <div class="text-xs text-base-content/40 mt-1 font-medium">
        {{ bill.date }}<template v-if="compact && bill.note"> · {{ bill.note }}</template>
      </div>
    </div>

    <template v-if="compact">
      <div class="font-bold text-sm tabular-nums shrink-0 px-2 py-1 rounded-lg" :class="bill.amount >= 0 ? 'text-success bg-success/10' : 'text-base-content bg-base-200/50'">
        {{ formatAmount(bill.amount) }}
      </div>
      <div class="flex gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-all duration-300 transform translate-x-2 group-hover:translate-x-0">
        <button @click="$emit('edit', bill)" class="p-1.5 rounded-lg hover:bg-primary/10 text-primary/60 hover:text-primary transition-all hover:scale-110">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button @click="$emit('delete', bill)" class="p-1.5 rounded-lg hover:bg-error/10 text-error/60 hover:text-error transition-all hover:scale-110">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </template>

    <template v-else>
      <div class="text-right flex items-center gap-2">
        <div class="font-bold tabular-nums mr-2 px-3 py-1.5 rounded-xl" :class="bill.amount >= 0 ? 'text-success bg-success/10' : 'text-base-content bg-base-200/50'">
          {{ formatAmount(bill.amount) }}
        </div>
        <button @click.stop="$emit('edit', bill)" class="p-2 rounded-xl opacity-0 group-hover:opacity-100 hover:bg-primary/10 text-primary/60 hover:text-primary transition-all hover:scale-110" :title="t('common.edit')">
          <svg class="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button @click.stop="$emit('delete', bill)" class="p-2 rounded-xl opacity-0 group-hover:opacity-100 hover:bg-error/10 text-error/60 hover:text-error transition-all hover:scale-110" :title="t('common.delete')">
          <svg class="w-4.5 h-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.hover-lift {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 32px rgba(0, 0, 0, 0.1),
    0 4px 16px rgba(0, 0, 0, 0.06);
}
</style>
