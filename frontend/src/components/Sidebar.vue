<script setup>
import { ref, onMounted } from 'vue'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'

const currentTheme = ref('light')

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', (event) => {
    currentTheme.value = event.detail.theme
  })
})

const toggleTheme = () => {
  currentTheme.value = toggleDarkLight()
}
</script>

<template>
  <div class="drawer-side">
    <label for="sidebar-drawer" class="drawer-overlay"></label>
    <ul class="menu p-4 w-60 min-h-full bg-base-200 text-base-content">
      <!-- Logo -->
      <li class="mb-4">
        <h1 class="text-xl font-bold">BoboBill</h1>
      </li>
      
      <!-- 导航链接 -->
      <li>
        <router-link to="/dashboard" active-class="active">Dashboard</router-link>
      </li>
      <li>
        <router-link to="/settings" active-class="active">Settings</router-link>
      </li>
      
      <!-- 主题切换 -->
      <li class="mt-auto pt-4 border-t border-base-300">
        <div class="flex items-center justify-between">
          <span class="text-sm opacity-70">主题</span>
          <button 
            @click="toggleTheme" 
            class="btn btn-sm btn-ghost" 
            :title="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
          >
            <span v-if="currentTheme === 'dark'" class="text-lg">🌙 深色</span>
            <span v-else class="text-lg">☀️ 浅色</span>
          </button>
        </div>
        <div class="text-xs opacity-50 mt-1">
          当前: {{ currentTheme }}
        </div>
      </li>
    </ul>
  </div>
</template>