<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '../composables/useAuth'
import { initTheme, getCurrentTheme } from '../utils/theme.js'
import { onMounted } from 'vue'
import BoboBillLogo from '../components/BoboBillLogo.vue'

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
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <div class="text-center mb-8">
        <BoboBillLogo :size="72" class="mx-auto" />
        <h1 class="text-3xl font-extrabold text-[var(--bb-text)] mt-4 tracking-[-0.04em]">{{ t('app.brand') }}</h1>
        <p class="text-sm text-[var(--bb-text-secondary)] mt-1 font-medium">{{ t('app.subtitle') }}</p>
      </div>

      <div class="bb-card-glass p-8 rounded-[var(--bb-radius-lg)]">
        <h2 class="text-xl font-bold text-[var(--bb-text)] text-center mb-6">
          {{ isLogin ? t('auth.loginTitle') : t('auth.registerTitle') }}
        </h2>

        <form @submit.prevent="submit" class="space-y-4">
          <div>
            <label class="block text-sm font-semibold text-[var(--bb-text-secondary)] mb-1.5">{{ t('auth.username') }}</label>
            <input
              v-model="username"
              type="text"
              :placeholder="t('auth.usernamePlaceholder')"
              autocomplete="username"
              class="bb-input"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-[var(--bb-text-secondary)] mb-1.5">{{ t('auth.password') }}</label>
            <input
              v-model="password"
              type="password"
              :placeholder="t('auth.passwordPlaceholder')"
              autocomplete="current-password"
              class="bb-input"
            />
          </div>

          <div v-if="error" class="text-sm bg-[var(--bb-coral)]/10 text-[var(--bb-coral)] rounded-xl px-4 py-2.5 font-medium">
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="isSubmitting"
            class="bb-button-primary w-full"
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

        <div class="mt-6 text-center text-sm text-[var(--bb-text-secondary)]">
          {{ isLogin ? t('auth.noAccount') : t('auth.hasAccount') }}
          <button @click="toggleMode" class="text-primary font-semibold hover:underline ml-1">
            {{ isLogin ? t('auth.goRegister') : t('auth.goLogin') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
