<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'
import { useAuth } from '../composables/useAuth'

const { t, locale } = useI18n()
const router = useRouter()
const { user, logout } = useAuth()
const currentTheme = ref('light')
const route = useRoute()

const handleLogout = () => {
  logout()
  router.push('/login')
}

const onThemeChange = (event) => {
  currentTheme.value = event.detail.theme
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', onThemeChange)
})

onUnmounted(() => {
  window.removeEventListener('themechange', onThemeChange)
})

const toggleTheme = () => {
  currentTheme.value = toggleDarkLight()
}

const navItems = computed(() => [
  { path: '/dashboard', label: t('nav.dashboard'), icon: 'M3 13h1v7c0 1.103.897 2 2 2h12c1.103 0 2-.897 2-2v-7h1a1 1 0 00.707-1.707l-9-9a.999.999 0 00-1.414 0l-9 9A1 1 0 003 13zm7 7v-5h4v5h-4zm2-15.586l6 6V20h-3v-5c0-1.103-.897-2-2-2h-4c-1.103 0-2 .897-2 2v5H6v-9.586l6-6z' },
  { path: '/bills', label: t('nav.bills'), icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' },
  { path: '/settings', label: t('nav.settings'), icon: 'M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z' }
])

const isActive = (path) => route.path === path
</script>

<template>
  <div class="drawer-side z-40">
    <label for="sidebar-drawer" class="drawer-overlay"></label>
    <div class="m-4 w-64 min-h-[calc(100vh-2rem)] bg-base-100/80 backdrop-blur-xl text-base-content flex flex-col rounded-[28px] shadow-[0_8px_32px_rgba(0,0,0,0.08),0_2px_8px_rgba(0,0,0,0.04)] overflow-hidden border border-white/20">
      
      <!-- Logo -->
      <div class="p-6 pb-4">
        <div class="flex items-center gap-3.5">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary via-primary to-primary/60 flex items-center justify-center shadow-lg shadow-primary/30 relative overflow-hidden">
            <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent"></div>
            <svg class="w-6 h-6 text-base-100 relative z-10" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 1.5l-9 4.5 9 4.5 9-4.5-9-4.5zM3 10.5l9 4.5 9-4.5M3 15l9 4.5 9-4.5"/>
            </svg>
          </div>
          <div class="flex flex-col">
            <h1 class="text-xl font-bold text-base-content tracking-tight">{{ t('app.brand') }}</h1>
            <p class="text-xs text-base-content/60 font-medium tracking-wide mt-0.5">{{ t('app.subtitle') }}</p>
          </div>
        </div>
        <div class="mt-6 h-px bg-gradient-to-r from-base-200 via-base-200/50 to-transparent"></div>
      </div>

      <!-- Navigation -->
      <div class="flex-1 px-5 py-2">
        <nav class="flex flex-col gap-1">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 px-4 py-3 rounded-[14px] transition-all duration-250 ease-out group relative overflow-hidden"
            :class="isActive(item.path)
              ? 'bg-gradient-to-r from-primary/95 to-primary/90 text-base-100 font-semibold shadow-lg shadow-primary/25'
              : 'hover:bg-base-200/60 text-base-content/70 hover:text-base-content'"
          >
            <svg class="w-5 h-5 flex-shrink-0 transition-all duration-250" viewBox="0 0 24 24" fill="currentColor"
              :class="isActive(item.path) ? 'scale-110' : 'group-hover:scale-105'">
              <path :d="item.icon" />
            </svg>
            <span class="font-medium tracking-tight">{{ item.label }}</span>
            <div v-if="isActive(item.path)" class="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent"></div>
          </router-link>
        </nav>
      </div>

      <!-- User Info -->
      <div v-if="user" class="px-5 pb-2 pt-2">
        <div class="flex items-center gap-3 px-4 py-3 rounded-[14px] bg-base-200/40">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-primary/80 to-primary/40 flex items-center justify-center text-base-100 font-bold text-sm shadow-sm">
            {{ user.username.charAt(0).toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-base-content truncate">{{ user.username }}</p>
          </div>
          <button @click="handleLogout" class="p-1.5 rounded-lg hover:bg-base-200/80 transition-all text-base-content/40 hover:text-error" :title="t('auth.logout')">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Theme Toggle -->
      <div class="px-5 pb-5 pt-2">
        <div 
          @click="toggleTheme"
          class="flex items-center justify-between px-4 py-3 rounded-[14px] cursor-pointer transition-all duration-250 ease-out hover:bg-base-200/60 group"
          :title="currentTheme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')"
        >
          <div class="flex items-center gap-3">
            <svg class="w-5 h-5 transition-all duration-250 group-hover:scale-105" viewBox="0 0 24 24" fill="currentColor">
              <path v-if="currentTheme === 'dark'" d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 007.92 12.446A9 9 0 1112 3z"/>
              <path v-else d="M12 18a6 6 0 11 0-12 6 6 0 010 12zm0-2a4 4 0 100-8 4 4 0 000 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z"/>
            </svg>
            <span class="font-medium text-base-content/70 group-hover:text-base-content tracking-tight">{{ currentTheme === 'dark' ? t('theme.darkMode') : t('theme.lightMode') }}</span>
          </div>
          <div class="relative">
            <div class="w-12 h-6.5 rounded-full transition-all duration-250 ease-out shadow-inner" 
              :class="currentTheme === 'dark' ? 'bg-primary shadow-primary/40' : 'bg-base-300'">
            </div>
            <div class="absolute top-0.75 w-5 h-5 rounded-full bg-base-100 transition-all duration-250 ease-out shadow-md"
              :class="currentTheme === 'dark' ? 'left-6.5 scale-110' : 'left-0.75'">
            </div>
          </div>
        </div>
      </div>
      
    </div>
  </div>
</template>
