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
  { 
    path: '/dashboard', 
    label: t('nav.dashboard'), 
    icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6',
    gradient: 'from-blue-500 to-cyan-400'
  },
  { 
    path: '/bills', 
    label: t('nav.bills'), 
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
    gradient: 'from-purple-500 to-pink-400'
  },
  { 
    path: '/ai', 
    label: t('nav.ai'), 
    icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z',
    gradient: 'from-emerald-500 to-teal-400'
  },
  { 
    path: '/settings', 
    label: t('nav.settings'), 
    icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    gradient: 'from-orange-500 to-amber-400'
  }
])

const isActive = (path) => route.path === path
</script>

<template>
  <div class="drawer-side z-40">
    <label for="sidebar-drawer" class="drawer-overlay"></label>
    <div class="m-4 w-72 min-h-[calc(100vh-2rem)] glass-elegant flex flex-col rounded-3xl shadow-elegant-lg overflow-hidden border border-white/20">
      
      <div class="p-7 pb-5">
        <div class="flex items-center gap-4">
          <div class="relative group">
            <div class="w-14 h-14 rounded-2xl bg-gradient-elegant flex items-center justify-center shadow-elevated transition-elegant group-hover:scale-105 cursor-pointer relative overflow-hidden">
              <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
              <div class="absolute -inset-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500 rounded-[1.25rem] opacity-20 blur-sm group-hover:opacity-40 transition-opacity duration-300"></div>
              <svg class="w-7 h-7 text-white relative z-10 drop-shadow-lg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div class="absolute -bottom-1 -right-1 w-4 h-4 bg-success rounded-full border-2 border-white animate-soft-pulse"></div>
          </div>
          <div class="flex flex-col flex-1 min-w-0">
            <h1 class="text-xl font-bold tracking-tight truncate">
              <span class="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">{{ t('app.brand') }}</span>
            </h1>
            <p class="text-xs text-base-content/60 font-medium tracking-wide mt-0.5 truncate">{{ t('app.subtitle') }}</p>
          </div>
        </div>
        <div class="mt-6 h-px bg-gradient-to-r from-primary/20 via-purple-500/20 to-pink-500/20"></div>
      </div>

      <div class="flex-1 px-5 py-2 overflow-y-auto">
        <nav class="flex flex-col gap-1.5">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3.5 px-4 py-3.5 rounded-2xl transition-elegant group relative overflow-hidden"
            :class="isActive(item.path)
              ? 'bg-gradient-to-r from-primary/10 to-purple-500/10 text-primary font-semibold shadow-elegant'
              : 'hover:bg-base-200/50 text-base-content/70 hover:text-base-content'"
          >
            <div v-if="isActive(item.path)" class="absolute inset-0 bg-gradient-to-r from-primary/15 to-purple-500/15"></div>
            <div class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-r-full transition-all duration-300"
              :class="isActive(item.path) ? 'bg-gradient-to-b from-primary to-purple-500 opacity-100' : 'opacity-0'"></div>
            <div class="relative z-10 flex items-center gap-3.5 w-full">
              <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300"
                :class="isActive(item.path) 
                  ? `bg-gradient-to-br ${item.gradient} text-white shadow-lg` 
                  : 'bg-base-200/50 group-hover:bg-base-200'">
                <svg class="w-5 h-5 transition-transform duration-300" :class="isActive(item.path) ? 'scale-110' : 'group-hover:scale-105'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="item.icon" />
                </svg>
              </div>
              <span class="font-semibold tracking-tight flex-1">{{ item.label }}</span>
              <svg v-if="isActive(item.path)" class="w-5 h-5 text-primary opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </router-link>
        </nav>
      </div>

      <div v-if="user" class="px-5 pb-4 pt-2">
        <div class="flex items-center gap-3 px-4 py-3 rounded-2xl bg-gradient-to-r from-base-200/60 to-base-100/40 hover:from-base-200/80 hover:to-base-100/60 transition-elegant cursor-pointer group">
          <div class="w-11 h-11 rounded-xl bg-gradient-elegant flex items-center justify-center text-white font-bold text-sm shadow-md group-hover:scale-105 transition-all duration-300">
            {{ user.username.charAt(0).toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-base-content truncate">{{ user.username }}</p>
            <p class="text-xs text-base-content/50 font-medium">在线</p>
          </div>
        </div>
      </div>

      <div class="px-5 pb-6 pt-3">
        <div 
          @click="toggleTheme"
          class="flex items-center justify-between px-4 py-3.5 rounded-2xl cursor-pointer transition-elegant group hover:bg-base-200/50"
          :title="currentTheme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')"
        >
          <div class="flex items-center gap-3.5">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300"
              :class="currentTheme === 'dark' 
                ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20 text-purple-500' 
                : 'bg-gradient-to-br from-amber-500/20 to-orange-500/20 text-amber-500'">
              <svg class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" viewBox="0 0 24 24" fill="currentColor">
                <path v-if="currentTheme === 'dark'" d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 007.92 12.446A9 9 0 1112 3z"/>
                <path v-else d="M12 18a6 6 0 100-12 6 6 0 000 12zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z"/>
              </svg>
            </div>
            <span class="font-semibold text-base-content/70 group-hover:text-base-content tracking-tight">{{ currentTheme === 'dark' ? t('theme.darkMode') : t('theme.lightMode') }}</span>
          </div>
          <div class="relative">
            <div class="w-14 h-7.5 rounded-full transition-all duration-300 shadow-inner" 
              :class="currentTheme === 'dark' ? 'bg-gradient-to-r from-purple-500 to-pink-500 shadow-purple-500/30' : 'bg-gradient-to-r from-amber-400 to-orange-400 shadow-amber-500/30'">
            </div>
            <div class="absolute top-0.75 w-6 h-6 rounded-full bg-white shadow-lg transition-all duration-300 flex items-center justify-center"
              :class="currentTheme === 'dark' ? 'left-7.5 scale-110' : 'left-0.75'">
              <div class="w-3 h-3 rounded-full transition-colors duration-300"
                :class="currentTheme === 'dark' ? 'bg-purple-500' : 'bg-amber-400'"></div>
            </div>
          </div>
        </div>
        
        <button
          @click="handleLogout"
          class="w-full mt-2 flex items-center gap-3.5 px-4 py-3.5 rounded-2xl text-error/70 hover:text-error hover:bg-error/10 transition-elegant group"
        >
          <div class="w-10 h-10 rounded-xl bg-error/10 group-hover:bg-error/20 flex items-center justify-center transition-all duration-300">
            <svg class="w-5 h-5 transition-transform duration-300 group-hover:scale-110" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </div>
          <span class="font-semibold tracking-tight">{{ t('auth.logout') || '退出登录' }}</span>
        </button>
      </div>
      
    </div>
  </div>
</template>
