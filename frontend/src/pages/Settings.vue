<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'

const { t, locale } = useI18n()
const currentTheme = ref('light')

const localeOptions = computed(() => [
  { value: 'zh-CN', label: t('settings.langZh') },
  { value: 'en', label: t('settings.langEn') }
])

const switchLocale = (lang) => {
  locale.value = lang
  localStorage.setItem('locale', lang)
}

// Theme
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
</script>

<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">{{ t('settings.title') }}</h1>
    
    <!-- Language -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.language') }}</h2>
        
        <div class="flex items-center justify-between p-4 bg-base-200 rounded-lg">
          <div>
            <h3 class="font-semibold">{{ t('settings.languageDesc') }}</h3>
          </div>
          <div class="flex gap-2">
            <button
              v-for="opt in localeOptions"
              :key="opt.value"
              @click="switchLocale(opt.value)"
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all"
              :class="locale === opt.value
                ? 'bg-primary text-white shadow-lg shadow-primary/25'
                : 'bg-base-300 text-base-content/70 hover:bg-base-300/80'"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Theme -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.theme') }}</h2>
        
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-base-200 rounded-lg">
            <div>
              <h3 class="font-semibold">{{ t('theme.darkLight') }}</h3>
              <p class="text-sm opacity-70">{{ t('theme.current') }}: {{ currentTheme === 'dark' ? t('theme.darkMode') : t('theme.lightMode') }}</p>
            </div>
            <button @click="toggleTheme" class="btn btn-primary">
              <span v-if="currentTheme === 'dark'">{{ t('theme.switchToLightBtn') }}</span>
              <span v-else>{{ t('theme.switchToDarkBtn') }}</span>
            </button>
          </div>
          
          <div class="text-sm opacity-70">
            <p>{{ t('theme.hint1') }}</p>
            <p>{{ t('theme.hint2') }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Other -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.other') }}</h2>
        <p>{{ t('settings.otherHint') }}</p>
      </div>
    </div>
  </div>
</template>
