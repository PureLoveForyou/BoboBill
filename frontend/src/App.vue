<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { initTheme, toggleDarkLight, getCurrentTheme } from './utils/theme.js'
import Sidebar from './components/Sidebar.vue'
import EchoAssistant from './components/EchoAssistant.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const currentTheme = ref('light')

const isLoginPage = computed(() => route.path === '/login')

const onThemeChange = (event) => {
  currentTheme.value = event.detail.theme
}

onMounted(() => {
  initTheme()
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', onThemeChange)
})

onUnmounted(() => {
  window.removeEventListener('themechange', onThemeChange)
})

const toggleTheme = () => {
  const newTheme = toggleDarkLight()
  currentTheme.value = newTheme
}

watch(() => router.currentRoute.value.path, () => {
  const drawerCheckbox = document.getElementById('sidebar-drawer')
  if (drawerCheckbox && window.innerWidth < 1024) {
    drawerCheckbox.checked = false
  }
})
</script>

<template>
  <div v-if="isLoginPage" class="min-h-screen">
    <router-view />
  </div>

  <div v-else class="min-h-screen bg-gradient-mesh">
    <div class="drawer lg:drawer-open">
      <input id="sidebar-drawer" type="checkbox" class="drawer-toggle" />
      
      <div class="drawer-content flex flex-col">
        <div class="sticky top-0 z-10 lg:hidden">
          <div class="glass-elegant border-b border-elegant/50 px-4 py-3">
            <div class="flex items-center justify-between max-w-7xl mx-auto">
              <div class="flex items-center gap-3">
                <label for="sidebar-drawer" class="btn btn-ghost p-2 hover:bg-base-content/5 rounded-xl transition-elegant-fast">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </label>
                <h1 class="text-lg font-bold bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">{{ t('app.brand') }}</h1>
              </div>
              <button @click="toggleTheme" class="btn btn-ghost p-2 hover:bg-base-content/5 rounded-xl transition-elegant-fast">
                <span v-if="currentTheme === 'dark'" class="text-lg">🌙</span>
                <span v-else class="text-lg">☀️</span>
              </button>
            </div>
          </div>
        </div>
        
        <div class="flex-1 p-4 lg:p-8 relative z-0">
          <div class="max-w-[1600px] mx-auto">
            <router-view v-slot="{ Component }">
              <keep-alive :include="['Dashboard', 'Bills', 'AIAssistant', 'Settings']">
                <component :is="Component" />
              </keep-alive>
            </router-view>
          </div>
        </div>
      </div>
      
      <Sidebar />
      
      <EchoAssistant />
    </div>
  </div>
</template>
