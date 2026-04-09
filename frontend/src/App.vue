<script setup>
import { useRouter, useRoute } from 'vue-router'
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { initTheme, toggleDarkLight, getCurrentTheme } from './utils/theme.js'
import Sidebar from './components/Sidebar.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const currentTheme = ref('light')

const isLoginPage = computed(() => route.path === '/login')

// Theme
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

// Close sidebar on route change (mobile)
watch(() => router.currentRoute.value.path, () => {
  const drawerCheckbox = document.getElementById('sidebar-drawer')
  if (drawerCheckbox && window.innerWidth < 1024) {
    drawerCheckbox.checked = false
  }
})
</script>

<template>
  <!-- Login page: no sidebar -->
  <div v-if="isLoginPage">
    <router-view />
  </div>

  <!-- Main layout with sidebar -->
  <div v-else class="drawer lg:drawer-open">
    <input id="sidebar-drawer" type="checkbox" class="drawer-toggle" />
    
    <div class="drawer-content flex flex-col">
      <!-- Mobile nav bar -->
      <div class="sticky top-0 z-10 lg:hidden">
        <div class="flex items-center justify-between bg-base-100 shadow-sm px-4 py-3">
          <div class="flex items-center">
            <label for="sidebar-drawer" class="btn btn-ghost p-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </label>
            <h1 class="text-xl font-bold ml-3">{{ t('app.brand') }}</h1>
          </div>
          <button @click="toggleTheme" class="btn btn-ghost p-2" :title="currentTheme === 'dark' ? t('theme.switchToLight') : t('theme.switchToDark')">
            <span v-if="currentTheme === 'dark'" class="text-xl">🌙</span>
            <span v-else class="text-xl">☀️</span>
          </button>
        </div>
      </div>
      
      <!-- Page content -->
      <div class="flex-1 p-4 relative z-0">
        <router-view v-slot="{ Component }">
          <keep-alive :include="['Dashboard', 'Bills', 'AIAssistant', 'Settings']">
            <component :is="Component" />
          </keep-alive>
        </router-view>
      </div>
    </div>
    
    <!-- Sidebar -->
    <Sidebar />
  </div>
</template>
