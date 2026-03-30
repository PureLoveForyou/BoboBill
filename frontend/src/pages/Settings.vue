<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'
import { API_BASE } from '../config'
import { useToast } from '../composables/useToast'

const { t, locale } = useI18n()
const { showToast } = useToast()
const currentTheme = ref('light')
const fileInput = ref(null)
const showImportConfirm = ref(false)
const importFile = ref(null)

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

// Backup & Restore
const exportDatabase = () => {
  const a = document.createElement('a')
  a.href = `${API_BASE}/backup/export`
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  showToast(t('settings.exportSuccess'), 'success')
}

const triggerImport = () => {
  fileInput.value?.click()
}

const handleImportFile = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.name.endsWith('.json')) {
    showToast(t('settings.importInvalidFormat'), 'error')
    return
  }
  importFile.value = file
  showImportConfirm.value = true
  e.target.value = ''
}

const confirmImport = async () => {
  if (!importFile.value) return

  try {
    const formData = new FormData()
    formData.append('file', importFile.value)

    const response = await fetch(`${API_BASE}/backup/import`, {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      showToast(t('settings.importSuccess'), 'success')
      showImportConfirm.value = false
      importFile.value = null
    } else {
      const data = await response.json()
      showToast(data.detail || t('settings.importFailed'), 'error')
    }
  } catch (error) {
    showToast(t('settings.importFailed'), 'error')
  }
}

const cancelImport = () => {
  showImportConfirm.value = false
  importFile.value = null
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
    
    <!-- Backup & Restore -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.backup') }}</h2>

        <p class="text-sm text-base-content/60 mb-6">{{ t('settings.backupDesc') }}</p>

        <div class="grid sm:grid-cols-2 gap-4">
          <button
            @click="exportDatabase"
            class="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-base-200/60 hover:bg-base-200 transition-all font-medium text-sm"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            {{ t('settings.exportBackup') }}
          </button>

          <button
            @click="triggerImport"
            class="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-primary/10 hover:bg-primary/20 text-primary transition-all font-medium text-sm"
          >
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            {{ t('settings.importBackup') }}
          </button>
        </div>

        <input
          ref="fileInput"
          type="file"
          accept=".json"
          class="hidden"
          @change="handleImportFile"
        >
      </div>
    </div>

    <!-- Other -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.other') }}</h2>
        <p>{{ t('settings.otherHint') }}</p>
      </div>
    </div>

    <!-- Import Confirm Modal -->
    <div v-if="showImportConfirm" class="fixed inset-0 z-50 flex items-center justify-center">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="cancelImport"></div>
      <div class="relative bg-base-100 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl">
        <div class="text-center">
          <div class="w-14 h-14 mx-auto mb-4 rounded-full bg-warning/10 flex items-center justify-center">
            <svg class="w-7 h-7 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold mb-2">{{ t('settings.importConfirmTitle') }}</h3>
          <p class="text-sm text-base-content/60 mb-6">{{ t('settings.importConfirmDesc') }}</p>
          <div class="flex gap-3">
            <button @click="cancelImport" class="flex-1 py-2.5 rounded-xl bg-base-200 text-base-content/70 font-medium text-sm hover:bg-base-300 transition-all">
              {{ t('common.cancel') }}
            </button>
            <button @click="confirmImport" class="flex-1 py-2.5 rounded-xl bg-primary text-white font-medium text-sm hover:bg-primary/90 transition-all">
              {{ t('common.confirm') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
