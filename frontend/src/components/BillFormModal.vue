<script setup>
import { CATEGORIES, PLATFORM_INFO } from '../constants/bill'

defineProps({
  visible: Boolean,
  bill: { type: Object, required: true },
  title: { type: String, default: '记账' },
  isSaving: { type: Boolean, default: false }
})

defineEmits(['close', 'save'])

const categories = CATEGORIES
const platformInfo = PLATFORM_INFO
</script>

<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('close')"></div>
    <div class="relative w-full max-w-md bg-base-100 rounded-3xl shadow-2xl overflow-hidden">
      <div class="p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold tracking-tight">{{ title }}</h2>
          <button @click="$emit('close')" class="p-2 rounded-xl hover:bg-base-200 transition-colors">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="space-y-4">
          <div class="flex gap-2 p-1 bg-base-200/50 rounded-2xl">
            <button
              class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
              :class="bill.type === 'expense' ? 'bg-base-100 text-error shadow-sm' : 'text-base-content/60'"
              @click="bill.type = 'expense'"
            >支出</button>
            <button
              class="flex-1 py-2.5 rounded-xl text-sm font-semibold transition-all"
              :class="bill.type === 'income' ? 'bg-base-100 text-success shadow-sm' : 'text-base-content/60'"
              @click="bill.type = 'income'"
            >收入</button>
          </div>

          <div>
            <label class="block text-sm font-medium text-base-content/60 mb-2">金额</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-base-content/40">¥</span>
              <input
                v-model="bill.amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                class="w-full pl-8 pr-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-lg font-semibold"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-base-content/60 mb-2">名称</label>
            <input
              v-model="bill.name"
              type="text"
              placeholder="例如：午餐、地铁、工资"
              class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">日期</label>
              <input
                v-model="bill.date"
                type="date"
                class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-base-content/60 mb-2">分类</label>
              <select
                v-model="bill.category"
                class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 cursor-pointer appearance-none"
              >
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-base-content/60 mb-2">平台</label>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="(info, key) in platformInfo"
                :key="key"
                @click="bill.platform = key"
                class="py-2.5 rounded-xl text-sm font-medium transition-all"
                :class="bill.platform === key
                  ? 'bg-gradient-to-br ' + info.color + ' text-white'
                  : 'bg-base-200/50 text-base-content/60 hover:bg-base-200'"
              >{{ info.name }}</button>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-base-content/60 mb-2">备注（可选）</label>
            <input
              v-model="bill.note"
              type="text"
              placeholder="添加备注..."
              class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>

        <div class="flex gap-3 mt-6">
          <button
            @click="$emit('close')"
            class="flex-1 py-3 rounded-xl bg-base-200 text-base-content font-semibold text-sm hover:bg-base-300 transition-colors"
          >取消</button>
          <button
            @click="$emit('save')"
            :disabled="!bill.name || !bill.amount || !bill.date || isSaving"
            class="flex-1 py-3 rounded-xl bg-gradient-to-r from-primary to-primary/80 text-white font-semibold text-sm shadow-lg shadow-primary/25 hover:shadow-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span v-if="isSaving" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              保存中...
            </span>
            <span v-else>保存</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
