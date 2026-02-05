<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'

const currentTheme = ref('light')
const router = useRouter()
const route = useRoute()

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', (event) => {
    currentTheme.value = event.detail.theme
  })
})

const toggleTheme = () => {
  currentTheme.value = toggleDarkLight()
}

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: 'M3 13h1v7c0 1.103.897 2 2 2h12c1.103 0 2-.897 2-2v-7h1a1 1 0 00.707-1.707l-9-9a.999.999 0 00-1.414 0l-9 9A1 1 0 003 13zm7 7v-5h4v5h-4zm2-15.586l6 6V20h-3v-5c0-1.103-.897-2-2-2h-4c-1.103 0-2 .897-2 2v5H6v-9.586l6-6z' },
  { path: '/settings', label: 'Settings', icon: 'M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z' }
]

const isActive = (path) => route.path === path
</script>

<template>
  <div class="drawer-side">
    <label for="sidebar-drawer" class="drawer-overlay"></label>
    <div class="m-4 w-60 min-h-[calc(100vh-2rem)] bg-base-100 text-base-content flex flex-col rounded-3xl shadow-xl overflow-hidden">
      
      <!-- Logo 区域 -->
      <div class="bg-gradient-to-br from-primary to-primary-content p-6 pb-8">
        <h1 class="text-2xl font-bold text-base-100">BoboBill</h1>
        <p class="text-xs text-base-100 opacity-80 mt-1">账单管理系统</p>
      </div>

      <!-- 导航区域 -->
      <div class="flex-1 p-4">
        <nav class="flex flex-col gap-2">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 p-3 rounded-xl transition-all duration-200"
            :class="isActive(item.path)
              ? 'bg-primary text-primary-foreground font-semibold shadow-md ring-2 ring-primary/30'
              : 'hover:bg-base-200 text-base-content'"
          >
            <svg class="w-5 h-5 flex-shrink-0 transition-colors duration-200" viewBox="0 0 24 24" fill="currentColor"
              :class="isActive(item.path) ? 'text-primary' : 'text-base-content'">
              <path :d="item.icon" />
            </svg>
            <span class="font-medium">{{ item.label }}</span>
          </router-link>
        </nav>
      </div>

      <!-- 主题切换区域 -->
      <div class="p-4 border-t border-base-200">
        <div 
          @click="toggleTheme"
          class="flex items-center justify-between p-3 rounded-xl cursor-pointer transition-all duration-200 hover:bg-base-200"
          :title="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'"
        >
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path v-if="currentTheme === 'dark'" d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 007.92 12.446A9 9 0 1112 3z"/>
              <path v-else d="M12 18a6 6 0 11 0-12 6 6 0 010 12zm0-2a4 4 0 100-8 4 4 0 000 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z"/>
            </svg>
            <span class="font-medium text-base-content">{{ currentTheme === 'dark' ? '深色模式' : '浅色模式' }}</span>
          </div>
          <div class="relative">
            <div class="w-12 h-6 rounded-full transition-colors duration-200" 
              :class="currentTheme === 'dark' ? 'bg-primary' : 'bg-base-300'">
            </div>
            <div class="absolute top-1 w-4 h-4 rounded-full bg-base-100 transition-all duration-200 shadow-sm"
              :class="currentTheme === 'dark' ? 'left-7' : 'left-1'">
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>