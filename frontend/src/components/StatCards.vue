<script setup>
defineProps({
  stats: { type: Array, required: true }
})
</script>

<template>
  <div class="grid gap-4 mb-6" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
    <div
      v-for="(stat, index) in stats"
      :key="index"
      class="group relative overflow-hidden rounded-2xl bg-gradient-to-br from-base-100 via-base-100 to-base-200/50 border border-base-200/50 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-base-300/10 hover:-translate-y-0.5"
    >
      <div class="absolute inset-0 bg-gradient-to-br opacity-5" :class="{
        'from-error to-error/50': stat.type === 'expense',
        'from-success to-success/50': stat.type === 'income',
        'from-info to-info/50': stat.type === 'balance',
        'from-primary to-primary/50': stat.type === 'count'
      }"></div>

      <div class="relative p-4">
        <div class="flex items-start justify-between mb-2">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-transform duration-300 group-hover:scale-110" :class="{
            'bg-gradient-to-br from-error/20 to-error/5 text-error': stat.type === 'expense',
            'bg-gradient-to-br from-success/20 to-success/5 text-success': stat.type === 'income',
            'bg-gradient-to-br from-info/20 to-info/5 text-info': stat.type === 'balance',
            'bg-gradient-to-br from-primary/20 to-primary/5 text-primary': stat.type === 'count'
          }">
            <svg v-if="stat.type === 'expense'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <svg v-else-if="stat.type === 'income'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <svg v-else-if="stat.type === 'balance'" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
            </svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>

          <div v-if="stat.trend !== 'neutral'" class="flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold" :class="{
            'bg-success/10 text-success': (stat.type === 'expense' ? stat.trend === 'down' : stat.trend === 'up'),
            'bg-error/10 text-error': (stat.type === 'expense' ? stat.trend === 'up' : stat.trend === 'down')
          }">
            <svg v-if="stat.trend === 'up'" class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
            </svg>
            <svg v-else class="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>

        <div class="text-xs font-medium text-base-content/60 mb-1">{{ stat.title }}</div>
        <div class="text-2xl font-bold tracking-tight mb-1">{{ stat.value }}</div>
        <div class="text-xs font-medium" :class="{
          'text-error': stat.type === 'expense',
          'text-success': stat.type === 'income',
          'text-info': stat.type === 'balance',
          'text-base-content/50': stat.type === 'count'
        }">{{ stat.desc }}</div>
      </div>
    </div>
  </div>
</template>
