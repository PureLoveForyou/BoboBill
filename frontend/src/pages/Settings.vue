<script setup>
defineOptions({ name: 'Settings' })
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'
import { API_BASE } from '../config'
import { useToast } from '../composables/useToast'
import { useBudgetApi } from '../composables/useBudgetApi'
import { useAiApi } from '../composables/useAiApi'
import { useAuth } from '../composables/useAuth'
import { CATEGORIES } from '../constants/bill'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const { toast, showToast } = useToast()
const { user, logout } = useAuth()
const { budget, fetchBudget, saveBudget } = useBudgetApi()
const {
  aiConfigs, fetchConfigs, saveConfig, updateConfig, deleteConfig,
  testConnection, getConfigDetail
} = useAiApi()
const currentTheme = ref('light')
const fileInput = ref(null)
const showImportConfirm = ref(false)
const importFile = ref(null)
const activeSection = ref('appearance')

watch(() => route.query.section, (section) => {
  if (section && ['appearance', 'finance', 'ai', 'data', 'account'].includes(section)) {
    activeSection.value = section
  }
}, { immediate: true })

const sections = computed(() => [
  {
    id: 'appearance',
    label: t('settings.appearance'),
    desc: t('settings.appearanceDesc'),
    icon: 'M12 18a6 6 0 11 0-12 6 6 0 010 12zm0-2a4 4 0 100-8 4 4 0 000 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z'
  },
  {
    id: 'finance',
    label: t('settings.finance'),
    desc: t('settings.financeDesc'),
    icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L10 14v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z'
  },
  {
    id: 'ai',
    label: t('settings.aiSection'),
    desc: t('settings.aiSectionDesc'),
    icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z'
  },
  {
    id: 'data',
    label: t('settings.data'),
    desc: t('settings.dataDesc'),
    icon: 'M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z'
  },
  {
    id: 'account',
    label: t('settings.account'),
    desc: t('settings.accountDesc'),
    icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'
  }
])

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

const onThemeChange = (event) => { currentTheme.value = event.detail.theme }

const providerOptions = computed(() => [
  { value: 'deepseek', label: 'DeepSeek', desc: t('ai.deepseekDesc'), icon: '🔮', defaultModel: 'deepseek-chat', color: '#4D6BFE' },
  { value: 'openai', label: 'OpenAI', desc: t('ai.openaiDesc'), icon: '🤖', defaultModel: 'gpt-3.5-turbo', color: '#10A37F' },
  { value: 'custom', label: 'Custom', desc: t('ai.customDesc'), icon: '⚙️', defaultModel: '', color: '#6366F1' }
])

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

const handleLogout = () => {
  logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-full">
    <div class="mb-6 lg:mb-8">
      <h1 class="text-xl lg:text-2xl font-bold tracking-tight">{{ t('settings.title') }}</h1>
      <p class="text-xs lg:text-sm text-base-content/50 mt-1">{{ t('settings.subtitle') }}</p>
    </div>

    <div class="flex flex-col lg:flex-row gap-4 lg:gap-8">
      <nav class="hidden lg:flex flex-col w-56 flex-shrink-0">
        <div class="sticky top-24 space-y-1">
          <button v-for="sec in sections" :key="sec.id"
            @click="activeSection = sec.id"
            class="w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-left transition-all duration-200 group"
            :class="activeSection === sec.id
              ? 'bg-primary/10 text-primary'
              : 'text-base-content/50 hover:text-base-content/80 hover:bg-base-200/40'">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200"
              :class="activeSection === sec.id ? 'bg-primary/15' : 'bg-base-200/60 group-hover:bg-base-200'">
              <svg class="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="currentColor">
                <path :d="sec.icon" />
              </svg>
            </div>
            <div class="min-w-0">
              <div class="text-sm font-semibold truncate">{{ sec.label }}</div>
              <div class="text-[11px] opacity-60 truncate leading-tight mt-0.5">{{ sec.desc }}</div>
            </div>
          </button>
        </div>
      </nav>

      <div class="lg:hidden grid grid-cols-5 gap-2">
        <button v-for="sec in sections" :key="sec.id"
          @click="activeSection = sec.id"
          class="flex flex-col items-center gap-1.5 px-2 py-3 rounded-2xl text-xs font-medium transition-all duration-200"
          :class="activeSection === sec.id
            ? 'bg-primary text-primary-content shadow-lg shadow-primary/20'
            : 'bg-base-200/60 text-base-content/60 hover:bg-base-200'">
          <svg class="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path :d="sec.icon" />
          </svg>
          <span class="truncate w-full text-center">{{ sec.label }}</span>
        </button>
      </div>

      <div class="flex-1 min-w-0 max-w-2xl">
        <transition name="section" mode="out-in">

          <!-- Appearance Section -->
          <div v-if="activeSection === 'appearance'" key="appearance" class="space-y-4 lg:space-y-5">
            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-4 lg:mb-5">
                <div class="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                  <svg class="w-4 h-4 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-base">{{ t('settings.language') }}</h3>
                  <p class="text-xs text-base-content/50">{{ t('settings.languageDesc') }}</p>
                </div>
              </div>
              <div class="flex gap-2">
                <button v-for="opt in localeOptions" :key="opt.value" @click="switchLocale(opt.value)"
                  class="flex-1 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200"
                  :class="locale === opt.value
                    ? 'bg-primary text-primary-content shadow-md shadow-primary/20'
                    : 'bg-base-200/50 text-base-content/60 hover:bg-base-200 hover:text-base-content/80'">
                  {{ opt.label }}
                </button>
              </div>
            </div>

            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-4 lg:mb-5">
                <div class="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                  <svg class="w-4 h-4 text-violet-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-base">{{ t('settings.theme') }}</h3>
                  <p class="text-xs text-base-content/50">{{ t('theme.darkLight') }}</p>
                </div>
              </div>
              <div class="flex items-center justify-between p-4 rounded-xl bg-base-200/30">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                    :class="currentTheme === 'dark' ? 'bg-indigo-500/10' : 'bg-amber-500/10'">
                    <span class="text-lg">{{ currentTheme === 'dark' ? '🌙' : '☀️' }}</span>
                  </div>
                  <div>
                    <div class="text-sm font-medium">{{ currentTheme === 'dark' ? t('theme.darkMode') : t('theme.lightMode') }}</div>
                    <div class="text-[11px] text-base-content/40">{{ t('theme.current') }}</div>
                  </div>
                </div>
                <button @click="toggleTheme"
                  class="relative w-14 h-8 rounded-full transition-all duration-300 ease-out"
                  :class="currentTheme === 'dark' ? 'bg-primary shadow-inner shadow-primary/30' : 'bg-base-300'">
                  <div class="absolute top-1 w-6 h-6 rounded-full bg-white shadow-md transition-all duration-300 ease-out"
                    :class="currentTheme === 'dark' ? 'left-7' : 'left-1'">
                  </div>
                </button>
              </div>
            </div>
          </div>

          <!-- Finance Section -->
          <div v-else-if="activeSection === 'finance'" key="finance" class="space-y-4 lg:space-y-5">
            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-4 lg:mb-5">
                <div class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <svg class="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-base">{{ t('budget.monthlyTotal') }}</h3>
                  <p class="text-xs text-base-content/50">{{ t('budget.monthlyTotalPlaceholder') }}</p>
                </div>
              </div>
              <div class="flex items-center gap-3 p-4 rounded-xl bg-base-200/30">
                <span class="text-base-content/40 text-sm font-medium">¥</span>
                <input v-model="monthlyTotal" type="number" min="0" step="100"
                  :placeholder="t('budget.monthlyTotalPlaceholder')"
                  class="input input-sm input-bordered flex-1 bg-transparent border-base-200/60 focus:border-primary focus:ring-primary/10" />
              </div>
            </div>

            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-4 lg:mb-5">
                <div class="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <svg class="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-base">{{ t('budget.categoryBudget') }}</h3>
                  <p class="text-xs text-base-content/50">{{ t('budget.categoryBudgetPlaceholder') }}</p>
                </div>
              </div>
              <div class="space-y-1.5 lg:space-y-2">
                <div v-for="cat in expenseCategories" :key="cat"
                  class="flex items-center justify-between px-3 lg:px-4 py-2.5 lg:py-3 rounded-xl bg-base-200/20 hover:bg-base-200/40 transition-colors">
                  <span class="text-sm font-medium">{{ t('categories.' + cat) }}</span>
                  <div class="flex items-center gap-1.5 lg:gap-2">
                    <span class="text-base-content/30 text-xs">¥</span>
                    <input v-model="categoryBudgets[cat]" type="number" min="0" step="100"
                      :placeholder="t('budget.categoryBudgetPlaceholder')"
                      class="input input-xs input-bordered w-24 lg:w-28 bg-transparent border-base-200/60 focus:border-primary focus:ring-primary/10" />
                  </div>
                </div>
              </div>
              <div class="mt-5">
                <button @click="handleSaveBudget" :disabled="isSavingBudget"
                  class="btn btn-primary btn-sm w-full rounded-xl shadow-lg shadow-primary/15">
                  <span v-if="isSavingBudget" class="loading loading-spinner loading-xs"></span>
                  {{ t('common.save') }}
                </button>
              </div>
            </div>
          </div>

          <!-- AI Section -->
          <div v-else-if="activeSection === 'ai'" key="ai" class="space-y-4 lg:space-y-5">
            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                  <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/>
                  </svg>
                </div>
                <h3 class="font-semibold text-base">{{ t('ai.title') }}</h3>
              </div>
              <p class="text-xs text-base-content/40 mb-5 pl-11">{{ t('ai.configDesc') }}</p>

              <div v-if="aiConfigs.length" class="space-y-2.5 mb-4">
                <transition-group name="list">
                  <div v-for="config in aiConfigs" :key="config.id"
                    class="group relative p-3 lg:p-4 rounded-xl border transition-all duration-200 hover:shadow-sm"
                    :class="[showAiForm && editingConfig?.id === config.id ? 'border-primary/40 bg-primary/[0.02]' : 'border-base-200/50 bg-base-50/50']">
                    <div class="flex items-start justify-between gap-2 lg:gap-3">
                      <div class="flex items-start gap-2.5 lg:gap-3 flex-1 min-w-0">
                        <div class="w-8 lg:w-9 h-8 lg:h-9 rounded-lg flex items-center justify-center flex-shrink-0 text-base mt-0.5"
                          :style="{ background: providerOptions.find(p => p.value === config.provider)?.color + '12' }">
                          {{ providerOptions.find(p => p.value === config.provider)?.icon || '🤖' }}
                        </div>
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2 flex-wrap">
                            <span class="font-medium text-sm truncate">{{ config.name }}</span>
                            <span class="px-2 py-0.5 rounded-md text-[10px] font-medium"
                              :style="{ background: providerOptions.find(p => p.value === config.provider)?.color + '14', color: providerOptions.find(p => p.value === config.provider)?.color }">
                              {{ providerLabel(config.provider) }}
                            </span>
                          </div>
                          <div class="flex items-center gap-2 mt-1 flex-wrap">
                            <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-base-200/60 text-[10px] text-base-content/50">
                              {{ config.model }}
                            </span>
                            <span class="text-[10px] text-base-content/30 font-mono">
                              •••{{ config.api_key.slice(-4) }}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div class="flex gap-0.5 flex-shrink-0 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity pt-0.5">
                        <button @click="handleEditConfig(config)" class="btn btn-ghost btn-xs btn-square">
                          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"/></svg>
                        </button>
                        <button @click="handleDeleteConfig(config)" class="btn btn-ghost btn-xs btn-square text-error/70 hover:text-error">
                          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>
                        </button>
                      </div>
                    </div>
                  </div>
                </transition-group>
              </div>

              <button v-if="!showAiForm" @click="handleAddConfig"
                class="btn btn-outline btn-sm w-full border-dashed rounded-xl hover:border-primary/40 hover:text-primary group">
                <svg class="w-4 h-4 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
                {{ t('ai.addConfig') }}
              </button>

              <transition name="slide-fade">
                <div v-if="showAiForm" class="mt-4 space-y-3 lg:space-y-4 p-4 lg:p-5 rounded-xl bg-base-200/20 border border-base-200/50">
                  <div class="flex items-center justify-between">
                    <h4 class="font-semibold text-sm">{{ editingConfig ? t('ai.editConfig') : t('ai.addConfig') }}</h4>
                    <button @click="resetForm" class="btn btn-ghost btn-xs btn-circle">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                    </button>
                  </div>

                  <div>
                    <label class="block text-xs font-medium mb-1.5 text-base-content/60">{{ t('ai.configName') }}</label>
                    <input v-model="formName" type="text" :placeholder="t('ai.configNamePlaceholder')"
                      class="input input-bordered w-full text-sm rounded-xl bg-transparent border-base-200/60 focus:border-primary focus:ring-primary/10" />
                  </div>

                  <div>
                    <label class="block text-xs font-medium mb-2 text-base-content/60">{{ t('ai.provider') }}</label>
                    <div class="grid grid-cols-3 gap-2">
                      <button v-for="opt in providerOptions" :key="opt.value"
                        @click="formProvider = opt.value; handleProviderChange()"
                        class="px-3 py-2.5 rounded-xl text-xs font-medium transition-all border cursor-pointer"
                        :class="formProvider === opt.value
                          ? 'border-primary/40 bg-primary/[0.04] text-primary'
                          : 'border-transparent bg-base-200/40 text-base-content/50 hover:bg-base-200/60'">
                        <div class="flex flex-col items-center gap-1">
                          <span class="text-lg">{{ opt.icon }}</span>
                          <span class="font-medium">{{ opt.label }}</span>
                        </div>
                      </button>
                    </div>
                  </div>

                  <div>
                    <label class="block text-xs font-medium mb-1.5 text-base-content/60">
                      {{ t('ai.apiKey') }} <span class="text-error">*</span>
                    </label>
                    <input v-model="formApiKey" type="password" :placeholder="t('ai.apiKeyPlaceholder')"
                      class="input input-bordered w-full text-sm rounded-xl bg-transparent border-base-200/60 focus:border-primary focus:ring-primary/10 font-mono text-xs" />
                  </div>

                  <div v-if="formProvider === 'custom' || formProvider === 'openai'">
                    <label class="block text-xs font-medium mb-1.5 text-base-content/60">{{ t('ai.apiUrl') }}</label>
                    <input v-model="formApiUrl" type="url"
                      :placeholder="formProvider === 'openai' ? 'https://api.openai.com' : t('ai.apiUrlPlaceholder')"
                      class="input input-bordered w-full text-sm rounded-xl bg-transparent border-base-200/60 focus:border-primary focus:ring-primary/10 font-mono text-xs" />
                  </div>

                  <div>
                    <label class="block text-xs font-medium mb-1.5 text-base-content/60">{{ t('ai.model') }}</label>
                    <input v-model="formModel" type="text" :placeholder="t('ai.modelPlaceholder')"
                      class="input input-bordered w-full text-sm rounded-xl bg-transparent border-base-200/60 focus:border-primary focus:ring-primary/10 font-mono text-xs" />
                  </div>

                  <div class="flex gap-2 pt-1">
                    <button @click="handleTestConnection" :disabled="isTestingAi || !formApiKey.trim()"
                      class="flex-1 btn btn-outline btn-sm border-dashed rounded-xl hover:border-success/40 hover:text-success">
                      <span v-if="isTestingAi" class="loading loading-spinner loading-xs"></span>
                      <template v-else>{{ t('ai.testConnection') }}</template>
                    </button>
                    <button @click="handleSaveAiConfig" :disabled="isSavingAi || !formApiKey.trim()"
                      class="flex-1 btn btn-primary btn-sm rounded-xl shadow-lg shadow-primary/15">
                      <span v-if="isSavingAi" class="loading loading-spinner loading-xs"></span>
                      <template v-else>{{ t('common.save') }}</template>
                    </button>
                  </div>
                </div>
              </transition>
            </div>
          </div>

          <!-- Data Section -->
          <div v-else-if="activeSection === 'data'" key="data" class="space-y-4 lg:space-y-5">
            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center">
                  <svg class="w-4 h-4 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-base">{{ t('settings.backup') }}</h3>
                  <p class="text-xs text-base-content/50">{{ t('settings.backupDesc') }}</p>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-2 lg:gap-3 mt-4 lg:mt-5">
                <button @click="exportDatabase"
                  class="flex items-center justify-center gap-2 px-3 lg:px-4 py-3 lg:py-3.5 rounded-xl bg-base-200/30 hover:bg-base-200/50 transition-all font-medium text-sm border border-base-200/40 hover:border-base-200/60 group">
                  <svg class="w-4 lg:w-5 h-4 lg:h-5 text-base-content/40 group-hover:text-base-content/60 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                  {{ t('settings.exportBackup') }}
                </button>
                <button @click="triggerImport"
                  class="flex items-center justify-center gap-2 px-3 lg:px-4 py-3 lg:py-3.5 rounded-xl bg-primary/[0.06] hover:bg-primary/[0.12] text-primary transition-all font-medium text-sm border border-primary/10 hover:border-primary/20 group">
                  <svg class="w-4 lg:w-5 h-4 lg:h-5 opacity-70 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                  {{ t('settings.importBackup') }}
                </button>
              </div>
              <input ref="fileInput" type="file" accept=".json" class="hidden" @change="handleImportFile">
            </div>
          </div>

          <!-- Account Section -->
          <div v-else-if="activeSection === 'account'" key="account" class="space-y-4 lg:space-y-5">
            <div class="rounded-2xl bg-base-100 border border-base-200/60 p-4 lg:p-6">
              <div class="flex items-center gap-3 mb-4 lg:mb-5">
                <div class="w-8 h-8 rounded-lg bg-rose-500/10 flex items-center justify-center">
                  <svg class="w-4 h-4 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                  </svg>
                </div>
                <div>
                  <h3 class="font-semibold text-base">{{ t('settings.account') }}</h3>
                  <p class="text-xs text-base-content/50">{{ t('settings.accountDesc') }}</p>
                </div>
              </div>

              <div v-if="user" class="flex items-center gap-3 p-4 rounded-xl bg-base-200/30 mb-4">
                <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-primary/80 to-primary/40 flex items-center justify-center text-primary-content font-bold text-base shadow-sm">
                  {{ user.username.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <div class="font-medium text-sm">{{ user.username }}</div>
                  <div class="text-[11px] text-base-content/40">{{ t('settings.accountDesc') }}</div>
                </div>
              </div>

              <p class="text-xs text-base-content/40 mb-4">{{ t('settings.logoutHint') }}</p>

              <button @click="handleLogout"
                class="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-error/[0.06] hover:bg-error/[0.12] text-error transition-all font-medium text-sm border border-error/10 hover:border-error/20">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                </svg>
                {{ t('auth.logout') }}
              </button>
            </div>
          </div>

        </transition>
      </div>
    </div>

    <!-- Import Confirm Modal -->
    <transition name="modal">
      <div v-if="showImportConfirm" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="cancelImport"></div>
        <div class="relative bg-base-100 rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl border border-base-200/50">
          <div class="text-center">
            <div class="w-12 h-12 mx-auto mb-4 rounded-full bg-warning/10 flex items-center justify-center">
              <svg class="w-6 h-6 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            </div>
            <h3 class="text-base font-semibold mb-1.5">{{ t('settings.importConfirmTitle') }}</h3>
            <p class="text-sm text-base-content/50 mb-5">{{ t('settings.importConfirmDesc') }}</p>
            <div class="flex gap-2.5">
              <button @click="cancelImport" class="flex-1 py-2.5 rounded-xl bg-base-200/60 text-base-content/60 font-medium text-sm hover:bg-base-200 transition-all">{{ t('common.cancel') }}</button>
              <button @click="confirmImport" class="flex-1 py-2.5 rounded-xl bg-primary text-primary-content font-medium text-sm hover:bg-primary/90 transition-all shadow-lg shadow-primary/15">{{ t('common.confirm') }}</button>
            </div>
          </div>
        </div>
      </div>
    </transition>

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
.list-enter-from { opacity: 0; transform: translateY(-8px); }
.list-leave-to { opacity: 0; transform: translateY(8px); }

.slide-fade-enter-active { transition: all 0.25s ease-out; }
.slide-fade-leave-active { transition: all 0.15s ease-in; }
.slide-fade-enter-from { opacity: 0; transform: translateY(-6px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.section-enter-active { transition: all 0.2s ease-out; }
.section-leave-active { transition: all 0.15s ease-in; }
.section-enter-from { opacity: 0; transform: translateX(8px); }
.section-leave-to { opacity: 0; transform: translateX(-8px); }

.modal-enter-active { transition: all 0.2s ease-out; }
.modal-leave-active { transition: all 0.15s ease-in; }
.modal-enter-from { opacity: 0; }
.modal-leave-to { opacity: 0; }
.modal-enter-active .relative { transition: all 0.2s ease-out; }
.modal-leave-active .relative { transition: all 0.15s ease-in; }
.modal-enter-from .relative { transform: scale(0.95); }
.modal-leave-to .relative { transform: scale(0.95); }

.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
</style>
