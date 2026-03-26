<script setup>
import { formatAmount } from '../utils/format'

defineProps({
  visible: Boolean,
  bill: { type: Object, default: null }
})

defineEmits(['close', 'confirm'])
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>
    <div class="relative w-full max-w-sm bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
      <div class="p-6 text-center">
        <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-error/10 flex items-center justify-center">
          <svg class="w-8 h-8 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </div>
        <h3 class="text-lg font-bold mb-2">删除账单</h3>
        <p class="text-sm text-base-content/60 mb-1">确定要删除这条账单吗？</p>
        <p v-if="bill" class="text-sm font-medium text-base-content/80">
          {{ bill.name }} · {{ formatAmount(bill.amount) }}
        </p>
      </div>
      <div class="flex border-t border-base-200">
        <button
          @click="$emit('close')"
          class="flex-1 py-4 text-sm font-semibold text-base-content/60 hover:bg-base-200/50 transition-colors"
        >取消</button>
        <button
          @click="$emit('confirm')"
          class="flex-1 py-4 text-sm font-semibold text-error hover:bg-error/10 transition-colors border-l border-base-200"
        >删除</button>
      </div>
    </div>
  </div>
</template>
