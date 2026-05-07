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
    icon: 'M12 18a6 6 0 11 0-12 6 6 0 010 12zm0-2a4 4 0 100-8 4 4 0 000 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z',
    gradient: 'from-amber-500 to-orange-400'
  },
  {
    id: 'finance',
    label: t('settings.finance'),
    desc: t('settings.financeDesc'),
    icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.94-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L10 14v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z',
    gradient: 'from-emerald-500 to-teal-400'
  },
  {
    id: 'ai',
    label: t('settings.aiSection'),
    desc: t('settings.aiSectionDesc'),
    icon: 'M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z',
    gradient: 'from-purple-500 to-pink-400'
  },
  {
    id: 'data',
    label: t('settings.data'),
    desc: t('settings.dataDesc'),
    icon: 'M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z',
    gradient: 'from-sky-500 to-blue-400'
  },
  {
    id: 'account',
    label: t('settings.account'),
    desc: t('settings.accountDesc'),
    icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z',
    gradient: 'from-rose-500 to-red-400'
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
  formUrl.value = detail.api_url
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
  <div class="min-h-full animate-elegant-in">
    <div class="mb-8">
      <h1 class="text-3xl font-bold tracking-tight mb-1">
        <span class="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">{{ t('settings.title') }}</span>
      </h1>
      <p class="text-sm text-base-content/50 font-medium">{{ t('settings.subtitle') }}</p>
    </div>

    <div class="flex flex-col lg:flex-row gap-6 lg:gap-8">
      <nav class="hidden lg:flex flex-col w-64 flex-shrink-0">
        <div class="sticky top-24 space-y-2">
          <button v-for="sec in sections" :key="sec.id"
            @click="activeSection = sec.id"
            class="w-full flex items-center gap-4 px-5 py-4 rounded-2xl text-left transition-elegant group hover-lift"
            :class="activeSection === sec.id
              ? 'glass-elegant shadow-elegant-lg'
              : 'hover:bg-base-200/50'">
            <div class="w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300"
              :class="activeSection === sec.id 
                ? `bg-gradient-to-br ${sec.gradient} text-white shadow-lg` 
                : 'bg-base-200/50 group-hover:bg-base-200'">
              <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path :d="sec.icon" />
              </svg>
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-sm font-bold tracking-tight" :class="activeSection === sec.id ? 'text-primary' : 'text-base-content'">{{ sec.label }}</div>
              <div class="text-[11px] text-base-content/40 mt-0.5 leading-relaxed">{{ sec.desc }}</div>
            </div>
            <svg v-if="activeSection === sec.id" class="w-5 h-5 text-primary opacity-60" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </nav>

      <div class="lg:hidden grid grid-cols-5 gap-2 mb-6">
        <button v-for="sec in sections" :key="sec.id"
          @click="activeSection = sec.id"
          class="flex flex-col items-center gap-2 px-2 py-4 rounded-2xl text-xs font-semibold transition-elegant hover-lift"
          :class="activeSection === sec.id
            ? 'bg-gradient-elegant text-white shadow-elevated'
            : 'glass-elegant text-base-content/60'">
          <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
            <path :d="sec.icon" />
          </svg>
          <span class="truncate w-full text-center text-[10px]">{{ sec.label }}</span>
        </button>
      </div>

      <div class="flex-1 min-w-0 max-w-2xl">
        <transition name="section" mode="out-in">

          <div v-if="activeSection === 'appearance'" key="appearance" class="space-y-5 animate-elegant-in">
            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-orange-400 to-rose-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-amber-500/5 via-transparent to-orange-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-5">
                  <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/10 flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 21l5.25-11.25L21 21m-9-3h7.5M3 5.621a48.474 48.474 0 016-.371m0 0c1.12 0 2.233.038 3.334.114M9 5.25V3m3.334 2.364C11.176 10.658 7.69 15.08 3 17.502m9.334-12.138c.896.061 1.785.147 2.666.257m-4.589 8.495a18.023 18.023 0 01-3.827-5.802" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg tracking-tight">{{ t('settings.language') }}</h3>
                    <p class="text-xs text-base-content/50 font-medium">{{ t('settings.languageDesc') }}</p>
                  </div>
                </div>
                <div class="flex gap-3">
                  <button v-for="opt in localeOptions" :key="opt.value" @click="switchLocale(opt.value)"
                    class="flex-1 px-5 py-4 rounded-xl text-sm font-semibold transition-elegant hover-lift shadow-elegant"
                    :class="locale === opt.value
                      ? 'bg-gradient-elegant text-white shadow-elevated'
                      : 'bg-base-200/50 hover:bg-base-200 text-base-content/70'">
                    {{ opt.label }}
                  </button>
                </div>
              </div>
            </div>

            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-pink-400 to-rose-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-5">
                  <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/10 flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg tracking-tight">{{ t('settings.theme') }}</h3>
                    <p class="text-xs text-base-content/50 font-medium">{{ t('theme.darkLight') }}</p>
                  </div>
                </div>
                <div class="flex items-center justify-between p-5 rounded-xl bg-gradient-to-r from-base-200/40 to-base-100/20">
                  <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300"
                      :class="currentTheme === 'dark' ? 'bg-gradient-to-br from-purple-500/20 to-pink-500/20' : 'bg-gradient-to-br from-amber-500/20 to-orange-500/20'">
                      <span class="text-2xl transition-transform duration-300" :class="currentTheme === 'dark' ? 'rotate-0' : 'rotate-0'">{{ currentTheme === 'dark' ? '🌙' : '☀️' }}</span>
                    </div>
                    <div>
                      <div class="text-sm font-bold">{{ currentTheme === 'dark' ? t('theme.darkMode') : t('theme.lightMode') }}</div>
                      <div class="text-[11px] text-base-content/40 font-medium">{{ t('theme.current') }}</div>
                    </div>
                  </div>
                  <button @click="toggleTheme"
                    class="relative w-16 h-9 rounded-full transition-all duration-300 ease-out shadow-inner cursor-pointer"
                    :class="currentTheme === 'dark' ? 'bg-gradient-to-r from-purple-500 to-pink-500 shadow-purple-500/30' : 'bg-gradient-to-r from-amber-400 to-orange-400 shadow-amber-500/30'">
                    <div class="absolute top-1 w-7 h-7 rounded-full bg-white shadow-lg transition-all duration-300 ease-out flex items-center justify-center"
                      :class="currentTheme === 'dark' ? 'left-8 scale-110' : 'left-1'">
                      <div class="w-4 h-4 rounded-full transition-colors duration-300"
                        :class="currentTheme === 'dark' ? 'bg-purple-500' : 'bg-amber-400'"></div>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeSection === 'finance'" key="finance" class="space-y-5 animate-elegant-in">
            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-teal-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-teal-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-5">
                  <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10 flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg tracking-tight">{{ t('budget.monthlyTotal') }}</h3>
                    <p class="text-xs text-base-content/50 font-medium">{{ t('budget.monthlyTotalPlaceholder') }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-4 p-5 rounded-xl bg-gradient-to-r from-base-200/40 to-base-100/20 shadow-inset">
                  <span class="text-base-content/40 text-lg font-bold">¥</span>
                  <input v-model="monthlyTotal" type="number" min="0" step="100"
                    :placeholder="t('budget.monthlyTotalPlaceholder')"
                    class="flex-1 bg-transparent border-0 focus:outline-none text-lg font-bold placeholder:text-base-content/30" />
                </div>
              </div>
            </div>

            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-cyan-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-5">
                  <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/10 flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg tracking-tight">{{ t('budget.categoryBudget') }}</h3>
                    <p class="text-xs text-base-content/50 font-medium">{{ t('budget.categoryBudgetPlaceholder') }}</p>
                  </div>
                </div>
                <div class="space-y-2">
                  <div v-for="cat in expenseCategories" :key="cat"
                    class="flex items-center justify-between px-4 py-3.5 rounded-xl bg-base-200/30 hover:bg-base-200/50 transition-elegant hover-lift">
                    <span class="text-sm font-semibold">{{ t('categories.' + cat) }}</span>
                    <div class="flex items-center gap-2">
                      <span class="text-base-content/30 text-sm font-bold">¥</span>
                      <input v-model="categoryBudgets[cat]" type="number" min="0" step="100"
                        :placeholder="t('budget.categoryBudgetPlaceholder')"
                        class="w-28 bg-transparent border-0 focus:outline-none text-right font-semibold placeholder:text-base-content/30" />
                    </div>
                  </div>
                </div>
                <div class="mt-6">
                  <button @click="handleSaveBudget" :disabled="isSavingBudget"
                    class="w-full py-3.5 rounded-xl font-semibold text-sm transition-elegant hover-lift shadow-elevated disabled:opacity-50"
                    :class="isSavingBudget ? 'bg-base-200 text-base-content/50' : 'bg-gradient-elegant text-white'">
                    <span v-if="isSavingBudget" class="flex items-center justify-center gap-2">
                      <svg class="w-4 h-4 animate-elegant-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {{ t('common.loading') }}
                    </span>
                    <span v-else>{{ t('common.save') }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else-if="activeSection === 'ai'" key="ai" class="space-y-5 animate-elegant-in">
            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 via-pink-400 to-rose-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-3">
                  <div class="w-12 h-12 rounded-xl bg-gradient-elegant flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z"/>
                    </svg>
                  </div>
                  <h3 class="font-bold text-lg tracking-tight">{{ t('ai.title') }}</h3>
                </div>
                <p class="text-xs text-base-content/40 mb-5 ml-16 font-medium">{{ t('ai.configDesc') }}</p>

                <div v-if="aiConfigs.length" class="space-y-3 mb-5">
                  <transition-group name="list">
                    <div v-for="config in aiConfigs" :key="config.id"
                      class="group relative p-4 rounded-xl border transition-elegant hover-lift"
                      :class="[showAiForm && editingConfig?.id === config.id ? 'border-primary/40 bg-primary/[0.02]' : 'border-elegant/30 bg-base-200/30 hover:bg-base-200/50']">
                      <div class="flex items-start justify-between gap-3">
                        <div class="flex items-start gap-3 flex-1 min-w-0">
                          <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg"
                            :style="{ background: providerOptions.find(p => p.value === config.provider)?.color + '20' }">
                            <span class="text-xl">{{ providerOptions.find(p => p.value === config.provider)?.icon || '🤖' }}</span>
                          </div>
                          <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 flex-wrap">
                              <span class="font-bold text-sm tracking-tight truncate">{{ config.name }}</span>
                              <span class="px-2.5 py-1 rounded-lg text-xs font-semibold"
                                :style="{ background: providerOptions.find(p => p.value === config.provider)?.color + '15', color: providerOptions.find(p => p.value === config.provider)?.color }">
                                {{ providerLabel(config.provider) }}
                              </span>
                            </div>
                            <div class="flex items-center gap-2 mt-2 flex-wrap">
                              <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-base-200/60 text-[11px] text-base-content/50 font-semibold">
                                {{ config.model }}
                              </span>
                              <span class="text-[11px] text-base-content/30 font-mono">
                                •••{{ config.api_key.slice(-4) }}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div class="flex gap-1 flex-shrink-0 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity pt-1">
                          <button @click="handleEditConfig(config)" class="btn btn-ghost btn-xs btn-square hover:bg-primary/10 hover:text-primary transition-elegant">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125"/></svg>
                          </button>
                          <button @click="handleDeleteConfig(config)" class="btn btn-ghost btn-xs btn-square text-error/70 hover:text-error hover:bg-error/10 transition-elegant">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/></svg>
                          </button>
                        </div>
                      </div>
                    </div>
                  </transition-group>
                </div>

                <button v-if="!showAiForm" @click="handleAddConfig"
                  class="btn btn-outline w-full border-dashed rounded-xl hover:border-primary/40 hover:text-primary group transition-elegant hover-lift font-semibold">
                  <svg class="w-5 h-5 transition-transform group-hover:rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
                  {{ t('ai.addConfig') }}
                </button>

                <transition name="slide-fade">
                  <div v-if="showAiForm" class="mt-5 space-y-4 p-5 rounded-xl bg-gradient-to-br from-base-200/40 to-base-100/20 border border-elegant/30">
                    <div class="flex items-center justify-between">
                      <h4 class="font-bold text-sm tracking-tight">{{ editingConfig ? t('ai.editConfig') : t('ai.addConfig') }}</h4>
                      <button @click="resetForm" class="btn btn-ghost btn-xs btn-circle hover:bg-base-200 transition-elegant">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                      </button>
                    </div>

                    <div>
                      <label class="block text-xs font-semibold mb-2 text-base-content/60">{{ t('ai.configName') }}</label>
                      <input v-model="formName" type="text" :placeholder="t('ai.configNamePlaceholder')"
                        class="w-full px-4 py-3 rounded-xl bg-base-200/50 border border-transparent focus:border-primary/40 transition-elegant text-sm font-medium placeholder:text-base-content/30 shadow-inset" />
                    </div>

                    <div>
                      <label class="block text-xs font-semibold mb-2 text-base-content/60">{{ t('ai.provider') }}</label>
                      <div class="grid grid-cols-3 gap-3">
                        <button v-for="opt in providerOptions" :key="opt.value"
                          @click="formProvider = opt.value; handleProviderChange()"
                          class="px-3 py-3.5 rounded-xl text-xs font-semibold transition-elegant hover-lift border cursor-pointer"
                          :class="formProvider === opt.value
                            ? 'bg-gradient-elegant text-white shadow-elevated border-transparent'
                            : 'bg-base-200/50 hover:bg-base-200 text-base-content/70 border-elegant/30'">
                          <div class="flex flex-col items-center gap-2">
                            <span class="text-2xl">{{ opt.icon }}</span>
                            <span>{{ opt.label }}</span>
                          </div>
                        </button>
                      </div>
                    </div>

                    <div>
                      <label class="block text-xs font-semibold mb-2 text-base-content/60">
                        {{ t('ai.apiKey') }} <span class="text-error">*</span>
                      </label>
                      <input v-model="formApiKey" type="password" :placeholder="t('ai.apiKeyPlaceholder')"
                        class="w-full px-4 py-3 rounded-xl bg-base-200/50 border border-transparent focus:border-primary/40 transition-elegant text-sm font-mono placeholder:text-base-content/30 shadow-inset" />
                    </div>

                    <div v-if="formProvider === 'custom' || formProvider === 'openai'">
                      <label class="block text-xs font-semibold mb-2 text-base-content/60">{{ t('ai.apiUrl') }}</label>
                      <input v-model="formApiUrl" type="url"
                        :placeholder="formProvider === 'openai' ? 'https://api.openai.com' : t('ai.apiUrlPlaceholder')"
                        class="w-full px-4 py-3 rounded-xl bg-base-200/50 border border-transparent focus:border-primary/40 transition-elegant text-sm font-mono placeholder:text-base-content/30 shadow-inset" />
                    </div>

                    <div>
                      <label class="block text-xs font-semibold mb-2 text-base-content/60">{{ t('ai.model') }}</label>
                      <input v-model="formModel" type="text" :placeholder="t('ai.modelPlaceholder')"
                        class="w-full px-4 py-3 rounded-xl bg-base-200/50 border border-transparent focus:border-primary/40 transition-elegant text-sm font-mono placeholder:text-base-content/30 shadow-inset" />
                    </div>

                    <div class="flex gap-3 pt-2">
                      <button @click="handleTestConnection" :disabled="isTestingAi || !formApiKey.trim()"
                        class="flex-1 py-3 rounded-xl font-semibold text-sm transition-elegant hover-lift border-dashed"
                        :class="isTestingAi || !formApiKey.trim() ? 'bg-base-200 text-base-content/50' : 'bg-base-200/50 hover:bg-success/10 text-success hover:border-success/40 border border-elegant/30'">
                        <span v-if="isTestingAi" class="flex items-center justify-center gap-2">
                          <svg class="w-4 h-4 animate-elegant-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        </span>
                        <span v-else>{{ t('ai.testConnection') }}</span>
                      </button>
                      <button @click="handleSaveAiConfig" :disabled="isSavingAi || !formApiKey.trim()"
                        class="flex-1 py-3 rounded-xl font-semibold text-sm transition-elegant hover-lift shadow-elevated disabled:opacity-50"
                        :class="isSavingAi || !formApiKey.trim() ? 'bg-base-200 text-base-content/50' : 'bg-gradient-elegant text-white'">
                        <span v-if="isSavingAi" class="flex items-center justify-center gap-2">
                          <svg class="w-4 h-4 animate-elegant-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        </span>
                        <span v-else>{{ t('common.save') }}</span>
                      </button>
                    </div>
                  </div>
                </transition>
              </div>
            </div>
          </div>

          <div v-else-if="activeSection === 'data'" key="data" class="space-y-5 animate-elegant-in">
            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-sky-500 to-blue-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-sky-500/5 via-transparent to-blue-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-3">
                  <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-sky-500/20 to-blue-500/10 flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-sky-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg tracking-tight">{{ t('settings.backup') }}</h3>
                    <p class="text-xs text-base-content/50 font-medium">{{ t('settings.backupDesc') }}</p>
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4 mt-5">
                  <button @click="exportDatabase"
                    class="flex items-center justify-center gap-3 px-5 py-4 rounded-xl bg-base-200/40 hover:bg-base-200 transition-elegant hover-lift font-semibold text-sm shadow-elegant border border-elegant/30 group">
                    <svg class="w-5 h-5 text-base-content/40 group-hover:text-primary transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
                    {{ t('settings.exportBackup') }}
                  </button>
                  <button @click="triggerImport"
                    class="flex items-center justify-center gap-3 px-5 py-4 rounded-xl bg-gradient-to-r from-primary/10 to-purple-500/10 hover:from-primary/20 hover:to-purple-500/20 text-primary transition-elegant hover-lift font-semibold text-sm shadow-elegant border border-primary/20 group">
                    <svg class="w-5 h-5 opacity-70 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                    {{ t('settings.importBackup') }}
                  </button>
                </div>
                <input ref="fileInput" type="file" accept=".json" class="hidden" @change="handleImportFile">
              </div>
            </div>
          </div>

          <div v-else-if="activeSection === 'account'" key="account" class="space-y-5 animate-elegant-in">
            <div class="relative overflow-hidden rounded-2xl glass-elegant shadow-elegant hover-lift transition-elegant group">
              <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 to-red-400"></div>
              <div class="absolute inset-0 bg-gradient-to-br from-rose-500/5 via-transparent to-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div class="relative p-6">
                <div class="flex items-center gap-4 mb-5">
                  <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-rose-500/20 to-red-500/10 flex items-center justify-center shadow-lg">
                    <svg class="w-6 h-6 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="font-bold text-lg tracking-tight">{{ t('settings.account') }}</h3>
                    <p class="text-xs text-base-content/50 font-medium">{{ t('settings.accountDesc') }}</p>
                  </div>
                </div>

                <div v-if="user" class="flex items-center gap-4 p-5 rounded-xl bg-gradient-to-r from-base-200/40 to-base-100/20 mb-5 shadow-inset">
                  <div class="w-14 h-14 rounded-xl bg-gradient-elegant flex items-center justify-center text-white font-bold text-xl shadow-lg">
                    {{ user.username.charAt(0).toUpperCase() }}
                  </div>
                  <div>
                    <div class="font-bold text-lg">{{ user.username }}</div>
                    <div class="text-[11px] text-base-content/40 font-medium">{{ t('settings.accountDesc') }}</div>
                  </div>
                </div>

                <p class="text-xs text-base-content/40 mb-5 font-medium">{{ t('settings.logoutHint') }}</p>

                <button @click="handleLogout"
                  class="w-full flex items-center justify-center gap-3 px-5 py-4 rounded-xl bg-error/10 hover:bg-error/20 text-error transition-elegant hover-lift font-semibold text-sm border border-error/20 group">
                  <svg class="w-5 h-5 transition-transform group-hover:translate-x-[-2px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
                  </svg>
                  {{ t('auth.logout') }}
                </button>
              </div>
            </div>
          </div>

        </transition>
      </div>
    </div>

    <transition name="modal">
      <div v-if="showImportConfirm" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/20 backdrop-blur-md" @click="cancelImport"></div>
        <div class="relative w-full max-w-md glass-elegant rounded-2xl shadow-elegant-lg overflow-hidden animate-elegant-in">
          <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-warning via-amber-400 to-orange-400"></div>
          <div class="p-8 text-center">
            <div class="w-16 h-16 mx-auto mb-5 rounded-2xl bg-warning/10 flex items-center justify-center">
              <svg class="w-8 h-8 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
            </div>
            <h3 class="text-xl font-bold mb-3">{{ t('settings.importConfirmTitle') }}</h3>
            <p class="text-sm text-base-content/60 mb-6 font-medium">{{ t('settings.importConfirmDesc') }}</p>
            <div class="flex gap-3">
              <button @click="cancelImport" class="flex-1 py-3 rounded-xl bg-base-200 text-base-content/70 font-semibold text-sm hover:bg-base-200/80 transition-elegant">
                {{ t('common.cancel') }}
              </button>
              <button @click="confirmImport" class="flex-1 py-3 rounded-xl bg-gradient-elegant text-white font-semibold text-sm shadow-elevated hover-lift transition-elegant">
                {{ t('common.confirm') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <transition name="slide-down">
      <div v-if="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-[100] px-5 py-3 rounded-xl shadow-elevated text-white text-sm font-semibold backdrop-blur-md"
        :class="toast.type === 'success' ? 'bg-gradient-to-r from-success to-green-500' : toast.type === 'warning' ? 'bg-gradient-to-r from-warning to-amber-500 text-warning-content' : 'bg-gradient-to-r from-error to-red-500'">
        {{ toast.message }}
      </div>
    </transition>
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

.slide-down-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-down-enter-from,
.slide-down-leave-to {
  transform: translate(-50%, -1.5rem);
  opacity: 0;
}

.scrollbar-none::-webkit-scrollbar { display: none; }
.scrollbar-none { -ms-overflow-style: none; scrollbar-width: none; }
</style>
