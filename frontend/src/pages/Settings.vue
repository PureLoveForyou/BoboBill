<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'
import { API_BASE } from '../config'
import { useToast } from '../composables/useToast'
import { useBudgetApi } from '../composables/useBudgetApi'
import { useAiApi } from '../composables/useAiApi'
import { CATEGORIES } from '../constants/bill'

const { t, locale } = useI18n()
const { toast, showToast } = useToast()
const { budget, fetchBudget, saveBudget } = useBudgetApi()
const { saveConfig: saveAiConfigSync } = useAiApi()
const currentTheme = ref('light')
const fileInput = ref(null)
const showImportConfirm = ref(false)
const importFile = ref(null)

// Budget
const monthlyTotal = ref(0)
const categoryBudgets = ref({})
const isSavingBudget = ref(false)

const expenseCategories = computed(() => CATEGORIES.filter(c => c !== '工资' && c !== '投资'))

const loadBudget = async () => {
  await fetchBudget()
  monthlyTotal.value = budget.value.monthly_total || 0
  categoryBudgets.value = { ...budget.value.category_budgets } || {}
}

const handleSaveBudget = async () => {
  isSavingBudget.value = true
  const data = {
    monthly_total: parseFloat(monthlyTotal.value) || 0,
    category_budgets: {}
  }
  for (const [cat, val] of Object.entries(categoryBudgets.value)) {
    if (val && parseFloat(val) > 0) {
      data.category_budgets[cat] = parseFloat(val)
    }
  }
  await saveBudget(data)
  isSavingBudget.value = false
}

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

// AI Configuration
const aiProvider = ref('deepseek')
const aiApiKey = ref('')
const aiApiUrl = ref('')
const aiModel = ref('deepseek-chat')
const isTestingAi = ref(false)
const isSavingAi = ref(false)

const providerOptions = computed(() => [
  { value: 'deepseek', label: 'DeepSeek', desc: t('ai.deepseekDesc'), defaultModel: 'deepseek-chat' },
  { value: 'openai', label: 'OpenAI', desc: t('ai.openaiDesc'), defaultModel: 'gpt-3.5-turbo' },
  { value: 'custom', label: 'Custom', desc: t('ai.customDesc'), defaultModel: '' }
])

const loadAiConfig = () => {
  const saved = JSON.parse(localStorage.getItem('bobobill_ai_config') || '{}')
  aiProvider.value = saved.provider || 'deepseek'
  aiApiKey.value = saved.apiKey || ''
  aiApiUrl.value = saved.apiUrl || ''
  aiModel.value = saved.model || 'deepseek-chat'
}

const currentProviderDefaultModel = () => {
  const found = providerOptions.value.find(p => p.value === aiProvider.value)
  return found ? found.defaultModel : ''
}

const handleProviderChange = () => {
  const def = currentProviderDefaultModel()
  if (def) aiModel.value = def
}

const handleTestConnection = async () => {
  if (!aiApiKey.value.trim()) {
    showToast(t('ai.apiKey'), 'warning')
    return
  }
  isTestingAi.value = true
  try {
    const params = new URLSearchParams({
      provider: aiProvider.value,
      api_key: aiApiKey.value.trim(),
      api_url: aiApiUrl.value.trim(),
      model: aiModel.value.trim() || currentProviderDefaultModel()
    })
    const response = await fetch(`${API_BASE}/ai/test-connection?${params}`)
    const data = await response.json()
    if (data.success) {
      showToast(t('ai.connectionSuccess'), 'success')
    } else {
      showToast(`${t('ai.connectionFailed')}: ${data.message}`, 'error')
    }
  } catch {
    showToast(t('ai.connectionFailed'), 'error')
  }
  isTestingAi.value = false
}

const handleSaveAiConfig = () => {
  if (!aiApiKey.value.trim()) {
    showToast(t('ai.apiKey'), 'warning')
    return
  }
  isSavingAi.value = true
  const config = {
    provider: aiProvider.value,
    apiKey: aiApiKey.value.trim(),
    apiUrl: aiApiUrl.value.trim(),
    model: aiModel.value.trim() || currentProviderDefaultModel()
  }
  saveAiConfigSync(config)
  showToast(t('ai.saved'), 'success')
  isSavingAi.value = false
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', onThemeChange)
  loadBudget()
  loadAiConfig()
})

onUnmounted(() => {
  window.removeEventListener('themechange', onThemeChange)
})

const toggleTheme = () => {
  currentTheme.value = toggleDarkLight()
}

// Backup & Restore
const exportDatabase = () => {
  const token = localStorage.getItem('bobobill_token')
  const a = document.createElement('a')
  a.href = `${API_BASE}/backup/export?token=${token}`
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

    const token = localStorage.getItem('bobobill_token')
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`

    const response = await fetch(`${API_BASE}/backup/import`, {
      method: 'POST',
      headers,
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
    
    <!-- Budget -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('budget.title') }}</h2>

        <div class="space-y-5">
          <!-- Monthly Total -->
          <div class="p-4 bg-base-200 rounded-lg">
            <label class="block text-sm font-semibold mb-2">{{ t('budget.monthlyTotal') }}</label>
            <div class="flex items-center gap-2">
              <span class="text-base-content/60 text-sm">¥</span>
              <input
                v-model="monthlyTotal"
                type="number"
                min="0"
                step="100"
                :placeholder="t('budget.monthlyTotalPlaceholder')"
                class="input input-sm input-bordered flex-1 bg-base-100"
              />
            </div>
          </div>

          <!-- Category Budgets -->
          <div>
            <h3 class="text-sm font-semibold mb-3">{{ t('budget.categoryBudget') }}</h3>
            <div class="space-y-2">
              <div
                v-for="cat in expenseCategories"
                :key="cat"
                class="flex items-center justify-between p-3 bg-base-200/60 rounded-lg"
              >
                <span class="text-sm font-medium">{{ t('categories.' + cat) }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-base-content/60 text-xs">¥</span>
                  <input
                    v-model="categoryBudgets[cat]"
                    type="number"
                    min="0"
                    step="100"
                    :placeholder="t('budget.categoryBudgetPlaceholder')"
                    class="input input-xs input-bordered w-28 bg-base-100"
                  />
                </div>
              </div>
            </div>
          </div>

          <button
            @click="handleSaveBudget"
            :disabled="isSavingBudget"
            class="btn btn-primary btn-sm w-full"
          >
            <span v-if="isSavingBudget" class="loading loading-spinner loading-xs"></span>
            {{ t('common.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- AI Assistant -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('ai.title') }}</h2>

        <p class="text-sm text-base-content/60 mb-6">
          配置 AI 服务后，可在「AI 助手」页面通过自然语言查询账单、获取消费分析建议。
          支持 DeepSeek 和 OpenAI 兼容接口。
        </p>

        <div class="space-y-5">
          <!-- Provider -->
          <div class="p-4 bg-base-200 rounded-lg">
            <label class="block text-sm font-semibold mb-3">{{ t('ai.provider') }}</label>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="opt in providerOptions"
                :key="opt.value"
                @click="aiProvider = opt.value; handleProviderChange()"
                class="px-3 py-2.5 rounded-xl text-xs font-medium transition-all border"
                :class="aiProvider === opt.value
                  ? 'border-primary bg-primary/10 text-primary shadow-sm'
                  : 'border-transparent bg-base-200/80 text-base-content/60 hover:bg-base-300'"
              >
                <div class="font-semibold">{{ opt.label }}</div>
              </button>
            </div>
            <p class="text-xs text-base-content/40 mt-2">{{ providerOptions.find(p => p.value === aiProvider)?.desc }}</p>
          </div>

          <!-- API Key -->
          <div>
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.apiKey') }} <span class="text-error">*</span></label>
            <input
              v-model="aiApiKey"
              type="password"
              :placeholder="t('ai.apiKeyPlaceholder')"
              class="input input-bordered w-full text-sm"
            />
          </div>

          <!-- API URL (for custom) -->
          <div v-if="aiProvider === 'custom' || aiProvider === 'openai'">
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.apiUrl') }}</label>
            <input
              v-model="aiApiUrl"
              type="text"
              :placeholder="aiProvider === 'openai' ? 'https://api.openai.com (留空使用默认)' : t('ai.apiUrlPlaceholder')"
              class="input input-bordered w-full text-sm"
            />
            <p class="text-xs text-base-content/40 mt-1">DeepSeek 默认: https://api.deepseek.com | OpenAI 默认: https://api.openai.com</p>
          </div>

          <!-- Model -->
          <div>
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.model') }}</label>
            <input
              v-model="aiModel"
              type="text"
              :placeholder="t('ai.modelPlaceholder')"
              class="input input-bordered w-full text-sm"
            />
            <p class="text-xs text-base-content/40 mt-1">
              推荐模型: deepseek-chat / deepseek-reasoner / gpt-4o-mini / gpt-3.5-turbo / claude-3-haiku 等
            </p>
          </div>

          <!-- Actions -->
          <div class="flex gap-3 pt-1">
            <button
              @click="handleTestConnection"
              :disabled="isTestingAi || !aiApiKey.trim()"
              class="flex-1 btn btn-outline btn-sm"
            >
              <span v-if="isTestingAi" class="loading loading-spinner loading-xs"></span>
              {{ isTestingAi ? '' : t('ai.testConnection') }}
            </button>
            <button
              @click="handleSaveAiConfig"
              :disabled="isSavingAi || !aiApiKey.trim()"
              class="flex-1 btn btn-primary btn-sm"
            >
              <span v-if="isSavingAi" class="loading loading-spinner loading-xs"></span>
              {{ isSavingAi ? t('ai.saving') : t('common.save') }}
            </button>
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
    <!-- Toast -->
    <div v-if="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-[100] px-4 py-2.5 rounded-xl shadow-lg text-white text-sm font-medium animate-slide-down"
      :class="toast.type === 'success' ? 'bg-success' : toast.type === 'warning' ? 'bg-warning text-warning-content' : 'bg-error'">
      {{ toast.message }}
    </div>
  </div>
</template>
