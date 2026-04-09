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
const {
  aiConfigs, fetchConfigs, saveConfig, updateConfig, deleteConfig,
  testConnection, getConfigDetail
} = useAiApi()
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

// ===== AI 多模型配置 =====
const providerOptions = computed(() => [
  { value: 'deepseek', label: 'DeepSeek', desc: t('ai.deepseekDesc'), defaultModel: 'deepseek-chat' },
  { value: 'openai', label: 'OpenAI', desc: t('ai.openaiDesc'), defaultModel: 'gpt-3.5-turbo' },
  { value: 'custom', label: 'Custom', desc: t('ai.customDesc'), defaultModel: '' }
])

// 表单状态
const editingConfig = ref(null) // null = 新增模式, 对象 = 编辑模式
const formName = ref('')
const formProvider = ref('deepseek')
const formApiKey = ref('')
const formApiUrl = ref('')
const formModel = ref('deepseek-chat')
const isTestingAi = ref(false)
const isSavingAi = ref(false)
const showAiForm = ref(false) // 控制表单显示

const currentProviderDefaultModel = () => {
  const found = providerOptions.value.find(p => p.value === formProvider.value)
  return found ? found.defaultModel : ''
}

const handleProviderChange = () => {
  const def = currentProviderDefaultModel()
  if (def) formModel.value = def
}

// 重置表单
const resetForm = () => {
  editingConfig.value = null
  formName.value = ''
  formProvider.value = 'deepseek'
  formApiKey.value = ''
  formApiUrl.value = ''
  formModel.value = 'deepseek-chat'
  showAiForm.value = false
}

// 新增配置
const handleAddConfig = () => {
  resetForm()
  showAiForm.value = true
}

// 编辑配置
const handleEditConfig = async (config) => {
  // 获取完整配置（含完整 API Key）
  const detail = await getConfigDetail(config.id)
  if (!detail) {
    showToast(t('ai.loadFailed'), 'error')
    return
  }
  editingConfig.value = config
  formName.value = detail.name
  formProvider.value = detail.provider
  formApiKey.value = detail.api_key
  formApiUrl.value = detail.api_url
  formModel.value = detail.model
  showAiForm.value = true
}

// 删除配置
const handleDeleteConfig = async (config) => {
  const result = await deleteConfig(config.id)
  if (result.success) {
    showToast(t('ai.configDeleted'), 'success')
  } else {
    showToast(result.message || t('ai.deleteFailed'), 'error')
  }
}

// 测试连接
const handleTestConnection = async () => {
  if (!formApiKey.value.trim()) {
    showToast(t('ai.apiKey'), 'warning')
    return
  }
  isTestingAi.value = true
  const result = await testConnection({
    provider: formProvider.value,
    apiKey: formApiKey.value.trim(),
    apiUrl: formApiUrl.value.trim(),
    model: formModel.value.trim() || currentProviderDefaultModel()
  })
  if (result.success) {
    showToast(t('ai.connectionSuccess'), 'success')
  } else {
    showToast(`${t('ai.connectionFailed')}: ${result.message}`, 'error')
  }
  isTestingAi.value = false
}

// 保存配置（新增或更新）
const handleSaveAiConfig = async () => {
  if (!formApiKey.value.trim()) {
    showToast(t('ai.apiKey'), 'warning')
    return
  }
  isSavingAi.value = true
  const payload = {
    name: formName.value.trim() || `${formProvider.value}-${formModel.value}`,
    provider: formProvider.value,
    api_key: formApiKey.value.trim(),
    api_url: formApiUrl.value.trim(),
    model: formModel.value.trim() || currentProviderDefaultModel()
  }

  let result
  if (editingConfig.value) {
    result = await updateConfig(editingConfig.value.id, payload)
  } else {
    result = await saveConfig(payload)
  }

  if (result.success) {
    showToast(t('ai.saved'), 'success')
    resetForm()
  } else {
    showToast(result.message || t('ai.saveFailed'), 'error')
  }
  isSavingAi.value = false
}

// Provider 标签映射
const providerLabel = (val) => {
  const found = providerOptions.value.find(p => p.value === val)
  return found ? found.label : val
}

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', onThemeChange)
  loadBudget()
  fetchConfigs()
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

        <p class="text-sm text-base-content/60 mb-4">
          {{ t('ai.configDesc') }}
        </p>

        <!-- 已保存的配置列表 -->
        <div v-if="aiConfigs.length" class="space-y-2 mb-4">
          <div
            v-for="config in aiConfigs"
            :key="config.id"
            class="flex items-center justify-between p-3 bg-base-200 rounded-lg"
          >
            <div class="flex-1 min-w-0">
              <div class="font-medium text-sm truncate">{{ config.name }}</div>
              <div class="text-xs text-base-content/50">
                {{ providerLabel(config.provider) }} · {{ config.model }} · {{ config.api_key }}
              </div>
            </div>
            <div class="flex gap-1 ml-2">
              <button @click="handleEditConfig(config)" class="btn btn-ghost btn-xs">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"/>
                </svg>
              </button>
              <button @click="handleDeleteConfig(config)" class="btn btn-ghost btn-xs text-error">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- 新增按钮 -->
        <button v-if="!showAiForm" @click="handleAddConfig" class="btn btn-outline btn-sm w-full mb-4">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/>
          </svg>
          {{ t('ai.addConfig') }}
        </button>

        <!-- 配置表单 -->
        <div v-if="showAiForm" class="space-y-4 p-4 bg-base-200/50 rounded-lg border border-base-300">
          <div class="flex items-center justify-between mb-2">
            <h3 class="font-semibold text-sm">
              {{ editingConfig ? t('ai.editConfig') : t('ai.addConfig') }}
            </h3>
            <button @click="resetForm" class="btn btn-ghost btn-xs">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>

          <!-- 配置名称 -->
          <div>
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.configName') }}</label>
            <input
              v-model="formName"
              type="text"
              :placeholder="t('ai.configNamePlaceholder')"
              class="input input-bordered w-full text-sm"
            />
          </div>

          <!-- Provider -->
          <div>
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.provider') }}</label>
            <div class="grid grid-cols-3 gap-2">
              <button
                v-for="opt in providerOptions"
                :key="opt.value"
                @click="formProvider = opt.value; handleProviderChange()"
                class="px-3 py-2 rounded-xl text-xs font-medium transition-all border"
                :class="formProvider === opt.value
                  ? 'border-primary bg-primary/10 text-primary shadow-sm'
                  : 'border-transparent bg-base-200/80 text-base-content/60 hover:bg-base-300'"
              >
                <div class="font-semibold">{{ opt.label }}</div>
              </button>
            </div>
            <p class="text-xs text-base-content/40 mt-2">{{ providerOptions.find(p => p.value === formProvider)?.desc }}</p>
          </div>

          <!-- API Key -->
          <div>
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.apiKey') }} <span class="text-error">*</span></label>
            <input
              v-model="formApiKey"
              type="password"
              :placeholder="t('ai.apiKeyPlaceholder')"
              class="input input-bordered w-full text-sm"
            />
          </div>

          <!-- API URL -->
          <div v-if="formProvider === 'custom' || formProvider === 'openai'">
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.apiUrl') }}</label>
            <input
              v-model="formApiUrl"
              type="text"
              :placeholder="formProvider === 'openai' ? 'https://api.openai.com (留空使用默认)' : t('ai.apiUrlPlaceholder')"
              class="input input-bordered w-full text-sm"
            />
            <p class="text-xs text-base-content/40 mt-1">DeepSeek 默认: https://api.deepseek.com | OpenAI 默认: https://api.openai.com</p>
          </div>

          <!-- Model -->
          <div>
            <label class="block text-sm font-semibold mb-1.5">{{ t('ai.model') }}</label>
            <input
              v-model="formModel"
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
              :disabled="isTestingAi || !formApiKey.trim()"
              class="flex-1 btn btn-outline btn-sm"
            >
              <span v-if="isTestingAi" class="loading loading-spinner loading-xs"></span>
              {{ isTestingAi ? '' : t('ai.testConnection') }}
            </button>
            <button
              @click="handleSaveAiConfig"
              :disabled="isSavingAi || !formApiKey.trim()"
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
