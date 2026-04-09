<script setup>
defineOptions({ name: 'Settings' })
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
  const data = { monthly_total: parseFloat(monthlyTotal.value) || 0, category_budgets: {} }
  for (const [cat, val] of Object.entries(categoryBudgets.value)) {
    if (val && parseFloat(val) > 0) data.category_budgets[cat] = parseFloat(val)
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
const onThemeChange = (event) => { currentTheme.value = event.detail.theme }

// ===== AI 多模型配置（优化版） =====
const providerOptions = computed(() => [
  { value: 'deepseek', label: 'DeepSeek', desc: t('ai.deepseekDesc'), icon: '🔮', defaultModel: 'deepseek-chat', color: '#4D6BFE' },
  { value: 'openai', label: 'OpenAI', desc: t('ai.openaiDesc'), icon: '🤖', defaultModel: 'gpt-3.5-turbo', color: '#10A37F' },
  { value: 'custom', label: 'Custom', desc: t('ai.customDesc'), icon: '⚙️', defaultModel: '', color: '#6366F1' }
])

// 表单状态
const editingConfig = ref(null)
const formName = ref('')
const formProvider = ref('deepseek')
const formApiKey = ref('')
const formApiUrl = ref('')
const formModel = ref('deepseek-chat')
const isTestingAi = ref(false)
const isSavingAi = ref(false)
const showAiForm = ref(false)

const currentProviderDefaultModel = () => {
  const found = providerOptions.value.find(p => p.value === formProvider.value)
  return found ? found.defaultModel : ''
}

const handleProviderChange = () => {
  const def = currentProviderDefaultModel()
  if (def) formModel.value = def
}

const resetForm = () => {
  editingConfig.value = null
  formName.value = ''
  formProvider.value = 'deepseek'
  formApiKey.value = ''
  formApiUrl.value = ''
  formModel.value = 'deepseek-chat'
  showAiForm.value = false
}

const handleAddConfig = () => { resetForm(); showAiForm.value = true }

const handleEditConfig = async (config) => {
  const detail = await getConfigDetail(config.id)
  if (!detail) { showToast(t('ai.loadFailed'), 'error'); return }
  editingConfig.value = config
  formName.value = detail.name
  formProvider.value = detail.provider
  formApiKey.value = detail.api_key
  formApiUrl.value = detail.api_url
  formModel.value = detail.model
  showAiForm.value = true
}

const handleDeleteConfig = async (config) => {
  const result = await deleteConfig(config.id)
  if (result.success) showToast(t('ai.configDeleted'), 'success')
  else showToast(result.message || t('ai.deleteFailed'), 'error')
}

const handleTestConnection = async () => {
  if (!formApiKey.value.trim()) { showToast(t('ai.apiKey'), 'warning'); return }
  isTestingAi.value = true
  const result = await testConnection({
    provider: formProvider.value,
    apiKey: formApiKey.value.trim(),
    apiUrl: formApiUrl.value.trim(),
    model: formModel.value.trim() || currentProviderDefaultModel()
  })
  if (result.success) showToast(t('ai.connectionSuccess'), 'success')
  else showToast(`${t('ai.connectionFailed')}: ${result.message}`, 'error')
  isTestingAi.value = false
}

const handleSaveAiConfig = async () => {
  if (!formApiKey.value.trim()) { showToast(t('ai.apiKey'), 'warning'); return }
  isSavingAi.value = true
  const payload = {
    name: formName.value.trim() || `${formProvider.value}-${formModel.value}`,
    provider: formProvider.value,
    api_key: formApiKey.value.trim(),
    api_url: formApiUrl.value.trim(),
    model: formModel.value.trim() || currentProviderDefaultModel()
  }
  let result
  if (editingConfig.value) result = await updateConfig(editingConfig.value.id, payload)
  else result = await saveConfig(payload)

  if (result.success) { showToast(t('ai.saved'), 'success'); resetForm() }
  else showToast(result.message || t('ai.saveFailed'), 'error')
  isSavingAi.value = false
}

const providerLabel = (val) => providerOptions.value.find(p => p.value === val)?.label || val

onMounted(() => {
  currentTheme.value = getCurrentTheme()
  window.addEventListener('themechange', onThemeChange)
  loadBudget()
  fetchConfigs()
})

onUnmounted(() => window.removeEventListener('themechange', onThemeChange))

const toggleTheme = () => { currentTheme.value = toggleDarkLight() }

// Backup & Restore
const exportDatabase = () => {
  const token = localStorage.getItem('bobobill_token')
  const a = document.createElement('a')
  a.href = `${API_BASE}/backup/export?token=${token}`
  a.target = '_blank'
  document.body.appendChild(a); a.click(); document.body.removeChild(a)
  showToast(t('settings.exportSuccess'), 'success')
}

const triggerImport = () => { fileInput.value?.click() }

const handleImportFile = (e) => {
  const file = e.target.files?.[0]
  if (!file) return
  if (!file.name.endsWith('.json')) { showToast(t('settings.importInvalidFormat'), 'error'); return }
  importFile.value = file
  showImportConfirm.value = true
  e.target.value = ''
}

const confirmImport = async () => {
  if (!importFile.value) return
  try {
    const formData = new FormData(); formData.append('file', importFile.value)
    const token = localStorage.getItem('bobobill_token')
    const headers = {}
    if (token) headers['Authorization'] = `Bearer ${token}`
    const response = await fetch(`${API_BASE}/backup/import`, { method: 'POST', headers, body: formData })
    if (response.ok) { showToast(t('settings.importSuccess'), 'success'); showImportConfirm.value = false; importFile.value = null }
    else { const data = await response.json(); showToast(data.detail || t('settings.importFailed'), 'error') }
  } catch { showToast(t('settings.importFailed'), 'error') }
}

const cancelImport = () => { showImportConfirm.value = false; importFile.value = null }
</script>

<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">{{ t('settings.title') }}</h1>

    <!-- Language -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.language') }}</h2>
        <div class="flex items-center justify-between p-4 bg-base-200 rounded-lg">
          <div><h3 class="font-semibold">{{ t('settings.languageDesc') }}</h3></div>
          <div class="flex gap-2">
            <button v-for="opt in localeOptions" :key="opt.value" @click="switchLocale(opt.value)"
              class="px-4 py-2 rounded-xl text-sm font-medium transition-all"
              :class="locale === opt.value ? 'bg-primary text-white shadow-lg shadow-primary/25' : 'bg-base-300 text-base-content/70 hover:bg-base-300/80'">
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
          <div class="text-sm opacity-70"><p>{{ t('theme.hint1') }}</p><p>{{ t('theme.hint2') }}</p></div>
        </div>
      </div>
    </div>

    <!-- Budget -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('budget.title') }}</h2>
        <div class="space-y-5">
          <div class="p-4 bg-base-200 rounded-lg">
            <label class="block text-sm font-semibold mb-2">{{ t('budget.monthlyTotal') }}</label>
            <div class="flex items-center gap-2">
              <span class="text-base-content/60 text-sm">¥</span>
              <input v-model="monthlyTotal" type="number" min="0" step="100" :placeholder="t('budget.monthlyTotalPlaceholder')" class="input input-sm input-bordered flex-1 bg-base-100"/>
            </div>
          </div>
          <div>
            <h3 class="text-sm font-semibold mb-3">{{ t('budget.categoryBudget') }}</h3>
            <div class="space-y-2">
              <div v-for="cat in expenseCategories" :key="cat"
                class="flex items-center justify-between p-3 bg-base-200/60 rounded-lg">
                <span class="text-sm font-medium">{{ t('categories.' + cat) }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-base-content/60 text-xs">¥</span>
                  <input v-model="categoryBudgets[cat]" type="number" min="0" step="100" :placeholder="t('budget.categoryBudgetPlaceholder')" class="input input-xs input-bordered w-28 bg-base-100"/>
                </div>
              </div>
            </div>
          </div>
          <button @click="handleSaveBudget" :disabled="isSavingBudget" class="btn btn-primary btn-sm w-full">
            <span v-if="isSavingBudget" class="loading loading-spinner loading-xs"></span>
            {{ t('common.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- AI Assistant - 优化版UI -->
    <div class="card bg-base-100 shadow-lg mb-6 overflow-hidden">
      <div class="card-body">
        <div class="flex items-center gap-2 mb-1">
          <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-primary via-primary to-primary/60 flex items-center justify-center shadow-md">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456z"/>
            </svg>
          </div>
          <h2 class="card-title text-xl">{{ t('ai.title') }}</h2>
        </div>

        <p class="text-sm text-base-content/60 mb-4 ml-10">{{ t('ai.configDesc') }}</p>

        <!-- 已保存的配置列表 - 卡片样式 -->
        <div v-if="aiConfigs.length" class="space-y-3 mb-4">
          <transition-group name="list">
            <div v-for="config in aiConfigs" :key="config.id"
              class="group relative p-4 rounded-2xl border transition-all duration-200 hover:shadow-md"
              :class="[showAiForm && editingConfig?.id === config.id ? 'border-primary bg-primary/[0.03]' : 'border-base-200/80 bg-base-50']">
              <div class="flex items-start justify-between gap-3">
                <div class="flex items-start gap-3 flex-1 min-w-0">
                  <!-- Provider 图标 -->
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 text-lg mt-0.5"
                    :style="{ background: providerOptions.find(p => p.value === config.provider)?.color + '15' }">
                    {{ providerOptions.find(p => p.value === config.provider)?.icon || '🤖' }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="font-semibold text-sm truncate">{{ config.name }}</span>
                      <span class="px-2 py-0.5 rounded-full text-[10px] font-medium"
                        :style="{ background: providerOptions.find(p => p.value === config.provider)?.color + '18', color: providerOptions.find(p => p.value === config.provider)?.color }">
                        {{ providerLabel(config.provider) }}
                      </span>
                    </div>
                    <div class="flex items-center gap-2 mt-1.5 flex-wrap">
                      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-base-200/80 text-[11px] text-base-content/60">
                        <svg class="w-3 h-3 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.356-2.053a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"/></svg>
                        {{ config.model }}
                      </span>
                      <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-base-200/80 text-[11px] text-base-content/40 font-mono">
                        •••{{ config.api_key.slice(-4) }}
                      </span>
                    </div>
                    <p v-if="config.api_url" class="text-[10px] text-base-content/30 mt-1 truncate font-mono">{{ config.api_url }}</p>
                  </div>
                </div>
                <!-- 操作按钮 -->
                <div class="flex gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity pt-1">
                  <button @click="handleEditConfig(config)" class="btn btn-ghost btn-xs btn-square" :title="t('ai.editConfig')">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"/></svg>
                  </button>
                  <button @click="handleDeleteConfig(config)" class="btn btn-ghost btn-xs btn-square text-error hover:bg-error/10" :title="t('ai.delete')">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>
                  </button>
                </div>
              </div>
            </div>
          </transition-group>
        </div>

        <!-- 新增按钮 -->
        <button v-if="!showAiForm" @click="handleAddConfig" class="btn btn-outline btn-sm w-full border-dashed mb-4 hover:border-primary/50 hover:text-primary group">
          <svg class="w-4 h-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
          {{ t('ai.addConfig') }}
        </button>

        <!-- 配置表单 - 优化版 -->
        <transition name="slide-fade">
          <div v-if="showAiForm" class="mt-2 space-y-4 p-5 bg-gradient-to-br from-base-200/30 to-base-100 rounded-2xl border border-base-200/80 shadow-inner">
            <!-- 表单头部 -->
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-6 h-6 rounded-lg bg-primary/10 flex items-center justify-center">
                  <svg class="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  </svg>
                </div>
                <h3 class="font-bold text-sm">{{ editingConfig ? t('ai.editConfig') : t('ai.addConfig') }}</h3>
              </div>
              <button @click="resetForm" class="btn btn-ghost btn-xs btn-circle">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>

            <!-- 配置名称 -->
            <div>
              <label class="block text-xs font-semibold mb-1.5 text-base-content/80">{{ t('ai.configName') }}</label>
              <input v-model="formName" type="text" :placeholder="t('ai.configNamePlaceholder')"
                class="input input-bordered w-full text-sm focus:border-primary focus:ring-primary/20"/>
            </div>

            <!-- Provider 选择 - 卡片式 -->
            <div>
              <label class="block text-xs font-semibold mb-2 text-base-content/80">{{ t('ai.provider') }}</label>
              <div class="grid grid-cols-3 gap-2">
                <button v-for="opt in providerOptions" :key="opt.value"
                  @click="formProvider = opt.value; handleProviderChange()"
                  class="relative px-3 py-3 rounded-xl text-xs font-medium transition-all border-2 cursor-pointer"
                  :class="formProvider === opt.value ? 'border-primary bg-primary/[0.06] shadow-sm scale-[1.02]' : 'border-transparent bg-base-200/60 text-base-content/60 hover:bg-base-200 hover:border-base-300'">
                  <div class="flex flex-col items-center gap-1.5">
                    <span class="text-xl">{{ opt.icon }}</span>
                    <span class="font-semibold" :class="formProvider === opt.value ? 'text-primary' : ''">{{ opt.label }}</span>
                  </div>
                </button>
              </div>
              <p class="text-[11px] text-base-content/40 mt-1.5 pl-1">{{ providerOptions.find(p => p.value === formProvider)?.desc }}</p>
            </div>

            <!-- API Key -->
            <div>
              <label class="block text-xs font-semibold mb-1.5 text-base-content/80">
                {{ t('ai.apiKey') }} <span class="text-error">*</span>
              </label>
              <div class="relative">
                <input v-model="formApiKey" type="password" :placeholder="t('ai.apiKeyPlaceholder')"
                  class="input input-bordered w-full text-sm pr-10 focus:border-primary focus:ring-primary/20 font-mono text-xs"/>
                <div class="absolute right-3 top-1/2 -translate-y-1/2 text-base-content/20">
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z"/></svg>
                </div>
              </div>
            </div>

            <!-- API URL -->
            <div v-if="formProvider === 'custom' || formProvider === 'openai'">
              <label class="block text-xs font-semibold mb-1.5 text-base-content/80">{{ t('ai.apiUrl') }}</label>
              <input v-model="formApiUrl" type="url"
                :placeholder="formProvider === 'openai' ? 'https://api.openai.com (留空使用默认)' : t('ai.apiUrlPlaceholder')"
                class="input input-bordered w-full text-sm font-mono text-xs focus:border-primary focus:ring-primary/20"/>
              <p class="text-[11px] text-base-content/40 mt-1 pl-1">DeepSeek 默认: https://api.deepseek.com | OpenAI 默认: https://api.openai.com</p>
            </div>

            <!-- Model -->
            <div>
              <label class="block text-xs font-semibold mb-1.5 text-base-content/80">{{ t('ai.model') }}</label>
              <input v-model="formModel" type="text" :placeholder="t('ai.modelPlaceholder')"
                class="input input-bordered w-full text-sm font-mono text-xs focus:border-primary focus:ring-primary/20"/>
              <p class="text-[11px] text-base-content/40 mt-1 pl-1">推荐: deepseek-chat / deepseek-reasoner / gpt-4o-mini / claude-3-haiku 等</p>
            </div>

            <!-- Actions -->
            <div class="flex gap-3 pt-2">
              <button @click="handleTestConnection" :disabled="isTestingAi || !formApiKey.trim()"
                class="flex-1 btn btn-outline btn-sm border-dashed hover:border-success/50 hover:text-success">
                <span v-if="isTestingAi" class="loading loading-spinner loading-xs"></span>
                <template v-else>
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"/></svg>
                  {{ t('ai.testConnection') }}
                </template>
              </button>
              <button @click="handleSaveAiConfig" :disabled="isSavingAi || !formApiKey.trim()"
                class="flex-1 btn btn-primary btn-sm shadow-lg shadow-primary/20">
                <span v-if="isSavingAi" class="loading loading-spinner loading-xs"></span>
                <template v-else>
                  <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>
                  {{ isSavingAi ? t('ai.saving') : t('common.save') }}
                </template>
              </button>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!-- Backup & Restore -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">{{ t('settings.backup') }}</h2>
        <p class="text-sm text-base-content/60 mb-6">{{ t('settings.backupDesc') }}</p>
        <div class="grid sm:grid-cols-2 gap-4">
          <button @click="exportDatabase" class="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-base-200/60 hover:bg-base-200 transition-all font-medium text-sm">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            {{ t('settings.exportBackup') }}
          </button>
          <button @click="triggerImport" class="flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-primary/10 hover:bg-primary/20 text-primary transition-all font-medium text-sm">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
            {{ t('settings.importBackup') }}
          </button>
        </div>
        <input ref="fileInput" type="file" accept=".json" class="hidden" @change="handleImportFile">
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
            <svg class="w-7 h-7 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
          </div>
          <h3 class="text-lg font-semibold mb-2">{{ t('settings.importConfirmTitle') }}</h3>
          <p class="text-sm text-base-content/60 mb-6">{{ t('settings.importConfirmDesc') }}</p>
          <div class="flex gap-3">
            <button @click="cancelImport" class="flex-1 py-2.5 rounded-xl bg-base-200 text-base-content/70 font-medium text-sm hover:bg-base-300 transition-all">{{ t('common.cancel') }}</button>
            <button @click="confirmImport" class="flex-1 py-2.5 rounded-xl bg-primary text-white font-medium text-sm hover:bg-primary/90 transition-all">{{ t('common.confirm') }}</button>
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

<style scoped>
.list-enter-active { transition: all 0.3s ease-out; }
.list-leave-active { transition: all 0.2s ease-in; }
.list-enter-from { opacity: 0; transform: translateX(-20px); }
.list-leave-to { opacity: 0; transform: translateX(20px); }
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-leave-active { transition: all 0.2s ease-in; }
.slide-fade-enter-from { opacity: 0; transform: translateY(-10px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
