<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../composables/useAuth'
import { initTheme, getCurrentTheme } from '../utils/theme.js'
import { onMounted } from 'vue'

const { t } = useI18n()
const router = useRouter()
const { login, register } = useAuth()

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const error = ref('')
const isSubmitting = ref(false)
const currentTheme = ref('light')

onMounted(() => {
  initTheme()
  currentTheme.value = getCurrentTheme()
})

const submit = async () => {
  if (!username.value || !password.value) {
    error.value = t('auth.pleaseInput')
    return
  }
  if (!isLogin.value && password.value.length < 4) {
    error.value = t('auth.passwordTooShort')
    return
  }

  error.value = ''
  isSubmitting.value = true

  const result = isLogin.value
    ? await login(username.value, password.value)
    : await register(username.value, password.value)

  isSubmitting.value = false

  if (result.success) {
    router.push('/dashboard')
  } else {
    error.value = result.message || (isLogin.value ? t('auth.loginFailed') : t('auth.registerFailed'))
  }
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  error.value = ''
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-base-200 via-base-100 to-base-200 p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-20 h-20 mx-auto rounded-3xl bg-gradient-to-br from-primary via-primary to-primary/60 flex items-center justify-center shadow-2xl shadow-primary/30 relative overflow-hidden">
          <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent"></div>
          <svg class="w-10 h-10 text-base-100 relative z-10" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 1.5l-9 4.5 9 4.5 9-4.5-9-4.5zM3 10.5l9 4.5 9-4.5M3 15l9 4.5 9-4.5"/>
          </svg>
        </div>
        <h1 class="text-3xl font-bold mt-4 tracking-tight">{{ t('app.brand') }}</h1>
        <p class="text-base-content/50 mt-1 text-sm font-medium">{{ t('app.subtitle') }}</p>
      </div>

      <!-- Card -->
      <div class="bg-base-100/80 backdrop-blur-xl rounded-[24px] shadow-[0_8px_32px_rgba(0,0,0,0.08)] border border-white/10 p-8">
        <h2 class="text-xl font-semibold text-center mb-6">
          {{ isLogin ? t('auth.loginTitle') : t('auth.registerTitle') }}
        </h2>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-base-content/60 mb-1.5">{{ t('auth.username') }}</label>
            <input
              v-model="username"
              type="text"
              :placeholder="t('auth.usernamePlaceholder')"
              autocomplete="username"
              class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm placeholder:text-base-content/30 transition-all"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-base-content/60 mb-1.5">{{ t('auth.password') }}</label>
            <input
              v-model="password"
              type="password"
              :placeholder="t('auth.passwordPlaceholder')"
              autocomplete="current-password"
              class="w-full px-4 py-3 rounded-xl bg-base-200/50 border-0 focus:outline-none focus:ring-2 focus:ring-primary/30 text-sm placeholder:text-base-content/30 transition-all"
            />
          </div>

          <div v-if="error" class="text-sm text-error bg-error/10 rounded-xl px-4 py-2.5">
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="isSubmitting"
            class="w-full py-3.5 rounded-xl font-semibold text-sm tracking-wide transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5"
          >
            <span v-if="isSubmitting" class="flex items-center justify-center gap-2">
              <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ t('common.loading') }}
            </span>
            <span v-else>{{ isLogin ? t('auth.loginBtn') : t('auth.registerBtn') }}</span>
          </button>
        </form>

        <div class="mt-6 text-center text-sm text-base-content/50">
          {{ isLogin ? t('auth.noAccount') : t('auth.hasAccount') }}
          <button @click="toggleMode" class="text-primary font-medium hover:underline ml-1">
            {{ isLogin ? t('auth.goRegister') : t('auth.goLogin') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
