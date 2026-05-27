<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'
import { useAuth } from '../composables/useAuth'
import BoboBillLogo from './BoboBillLogo.vue'

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
  { path: '/dashboard', label: t('nav.dashboard'), icon: 'home' },
  { path: '/bills', label: t('nav.bills'), icon: 'bills' },
  { path: '/ai', label: t('nav.ai'), icon: 'ai' },
  { path: '/settings', label: t('nav.settings'), icon: 'settings' }
])

const isActive = (path) => route.path === path
</script>

<template>
  <div class="drawer-side z-40">
    <label for="sidebar-drawer" class="drawer-overlay"></label>
    <div class="m-4 w-64 min-h-[calc(100vh-2rem)] flex flex-col bb-card-glass rounded-[var(--bb-radius-xl)] p-[22px] sticky top-[84px]">

      <div class="px-2 pb-6">
        <div class="flex items-center gap-3">
          <BoboBillLogo :size="38" />
          <div class="flex flex-col min-w-0">
            <span class="text-[21px] font-extrabold text-[var(--bb-text)] tracking-[-0.055em] leading-tight">{{ t('app.brand') }}</span>
            <span class="text-[11px] font-semibold text-[var(--bb-text-secondary)] leading-tight mt-0.5">{{ t('app.subtitle') }}</span>
          </div>
        </div>
      </div>

      <nav class="flex-1 flex flex-col gap-[6px]">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-nav-link relative flex items-center gap-[10px] px-[13px] py-3 rounded-[16px] text-[14px] font-semibold no-underline whitespace-nowrap"
          :class="isActive(item.path)
            ? 'sidebar-nav-active text-[var(--bb-blue2)]'
            : 'text-[var(--bb-text-secondary)] hover:text-[var(--bb-text)] hover:bg-[var(--bb-bg-soft)]'"
        >
          <span v-if="isActive(item.path)" class="sidebar-nav-indicator"></span>
          <svg class="w-5 h-5 shrink-0 opacity-90" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">
            <template v-if="item.icon === 'home'">
              <path d="M3 11.5 12 4l9 7.5"/><path d="M5.5 10.5V20h13v-9.5"/><path d="M9.5 20v-6h5v6"/>
            </template>
            <template v-else-if="item.icon === 'bills'">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
            </template>
            <template v-else-if="item.icon === 'ai'">
              <path d="M12 3l1.7 5.1L19 10l-5.3 1.9L12 17l-1.7-5.1L5 10l5.3-1.9L12 3Z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15Z"/>
            </template>
            <template v-else>
              <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/><path d="M19.4 15a1.8 1.8 0 0 0 .36 1.98l.04.04a2 2 0 0 1-2.83 2.83l-.04-.04A1.8 1.8 0 0 0 15 19.4a1.8 1.8 0 0 0-1 .6 1.8 1.8 0 0 0-.4 1.1V21a2 2 0 0 1-4 0v-.1A1.8 1.8 0 0 0 8.6 19.4a1.8 1.8 0 0 0-1.98.36l-.04.04a2 2 0 1 1-2.83-2.83l.04-.04A1.8 1.8 0 0 0 4.6 15a1.8 1.8 0 0 0-.6-1 1.8 1.8 0 0 0-1.1-.4H3a2 2 0 0 1 0-4h.1A1.8 1.8 0 0 0 4.6 8.6a1.8 1.8 0 0 0-.36-1.98l-.04-.04a2 2 0 1 1 2.83-2.83l.04.04A1.8 1.8 0 0 0 9 4.6c.38-.16.7-.37 1-.6.3-.23.4-.68.4-1.1V3a2 2 0 0 1 4 0v.1c0 .42.1.87.4 1.1.3.23.62.44 1 .6a1.8 1.8 0 0 0 1.98-.36l.04-.04a2 2 0 1 1 2.83 2.83l-.04.04A1.8 1.8 0 0 0 19.4 9c.16.38.37.7.6 1 .23.3.68.4 1.1.4h.1a2 2 0 0 1 0 4h-.1c-.42 0-.87.1-1.1.4-.23.3-.44.62-.6 1Z"/>
            </template>
          </svg>
          <span class="font-semibold tracking-tight">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="mt-auto pt-2">
        <div class="h-px bg-[var(--bb-border)] mb-3"></div>

        <div v-if="user" class="flex items-center gap-3 px-3 py-2.5 rounded-[14px] hover:bg-[var(--bb-bg-soft)] transition-colors duration-200">
          <div class="w-8 h-8 rounded-[10px] bg-[var(--bb-blue)] flex items-center justify-center text-white font-extrabold text-xs flex-shrink-0">
            {{ user.username.charAt(0).toUpperCase() }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-[13px] font-semibold text-[var(--bb-text)] truncate leading-tight">{{ user.username }}</p>
          </div>
        </div>

        <button
          @click="toggleTheme"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-[14px] hover:bg-[var(--bb-bg-soft)] transition-colors duration-200 text-left"
          :title="currentTheme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')"
        >
          <div class="w-8 h-8 rounded-[10px] flex items-center justify-center flex-shrink-0" :class="currentTheme === 'dark' ? 'bg-indigo-400/15' : 'bg-amber-400/15'">
            <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" :class="currentTheme === 'dark' ? 'text-indigo-400' : 'text-amber-500'">
              <path v-if="currentTheme === 'dark'" d="M12 3c.132 0 .263 0 .393 0a7.5 7.5 0 007.92 12.446A9 9 0 1112 3z"/>
              <path v-else d="M12 3v1m0 16v1m-9-9h1m16 0h1M5.6 5.6l.7.7m12.1 12.1l.7.7M2 12a10 10 0 100 20 10 10 0 000-20z"/>
            </svg>
          </div>
          <span class="text-[13px] font-semibold text-[var(--bb-text-secondary)] leading-tight">
            {{ currentTheme === 'dark' ? t('theme.darkMode') : t('theme.lightMode') }}
          </span>
        </button>

        <button
          v-if="user"
          @click="handleLogout"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-[14px] hover:bg-[var(--bb-coral)]/6 transition-colors duration-200 text-left mt-0.5"
        >
          <div class="w-8 h-8 rounded-[10px] bg-[var(--bb-coral)]/10 flex items-center justify-center flex-shrink-0">
            <svg class="w-4 h-4 text-[var(--bb-coral)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
          </div>
          <span class="text-[13px] font-semibold text-[var(--bb-text-secondary)] leading-tight">{{ t('auth.logout') }}</span>
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.sidebar-nav-link {
  transition: color 0.18s ease, background 0.18s ease;
}

.sidebar-nav-active {
  background: linear-gradient(145deg, rgba(36,120,255,.12), rgba(54,211,153,.06));
}

.sidebar-nav-indicator {
  position: absolute;
  left: 0;
  width: 3px;
  height: 23px;
  border-radius: 999px;
  background: var(--bb-blue);
}
</style>
