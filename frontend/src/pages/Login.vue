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
  <div class="min-h-screen flex items-center justify-center relative overflow-hidden">
    <div class="absolute inset-0 bg-gradient-mesh opacity-50"></div>
    
    <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-3xl animate-soft-pulse"></div>
    <div class="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-soft-pulse" style="animation-delay: 1s;"></div>
    <div class="absolute top-1/2 right-1/3 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl animate-soft-pulse" style="animation-delay: 2s;"></div>
    
    <div class="relative z-10 w-full max-w-md px-6 animate-elegant-in">
      <div class="text-center mb-10">
        <div class="relative inline-block">
          <div class="w-24 h-24 rounded-3xl bg-gradient-elegant flex items-center justify-center shadow-elevated glow-effect relative overflow-hidden group cursor-pointer hover-scale transition-elegant">
            <div class="absolute inset-0 bg-gradient-to-br from-white/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div class="absolute -inset-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500 rounded-[1.5rem] opacity-30 blur-sm group-hover:opacity-50 transition-opacity duration-300"></div>
            <svg class="w-12 h-12 text-white relative z-10 drop-shadow-lg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
        </div>
        <h1 class="text-4xl font-bold mt-6 mb-2 tracking-tight">
          <span class="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">{{ t('app.brand') }}</span>
        </h1>
        <p class="text-base-content/50 font-medium text-sm tracking-wide">{{ t('app.subtitle') }}</p>
      </div>

      <div class="glass-elegant rounded-elegant-xl shadow-elegant-lg p-8 relative overflow-hidden">
        <div class="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary via-purple-500 to-pink-500"></div>
        
        <h2 class="text-2xl font-bold text-center mb-8 tracking-tight">
          {{ isLogin ? t('auth.loginTitle') : t('auth.registerTitle') }}
        </h2>

        <form @submit.prevent="submit" class="space-y-5">
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-base-content/70 tracking-tight">{{ t('auth.username') }}</label>
            <div class="relative group">
              <input
                v-model="username"
                type="text"
                :placeholder="t('auth.usernamePlaceholder')"
                autocomplete="username"
                class="w-full px-4 py-3.5 rounded-elegant bg-base-200/50 border border-transparent group-hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm placeholder:text-base-content/30 shadow-inset"
              />
              <div class="absolute inset-0 rounded-elegant bg-gradient-to-r from-primary/5 to-purple-500/5 opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"></div>
            </div>
          </div>
          
          <div class="space-y-2">
            <label class="block text-sm font-semibold text-base-content/70 tracking-tight">{{ t('auth.password') }}</label>
            <div class="relative group">
              <input
                v-model="password"
                type="password"
                :placeholder="t('auth.passwordPlaceholder')"
                autocomplete="current-password"
                class="w-full px-4 py-3.5 rounded-elegant bg-base-200/50 border border-transparent group-hover:border-primary/20 focus:border-primary/40 transition-elegant text-sm placeholder:text-base-content/30 shadow-inset"
              />
              <div class="absolute inset-0 rounded-elegant bg-gradient-to-r from-primary/5 to-purple-500/5 opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none"></div>
            </div>
          </div>

          <Transition name="slide-fade">
            <div v-if="error" class="relative overflow-hidden rounded-elegant bg-error/10 border border-error/20 px-4 py-3">
              <div class="flex items-center gap-2 text-sm text-error font-medium">
                <svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ error }}
              </div>
            </div>
          </Transition>

          <button
            type="submit"
            :disabled="isSubmitting"
            class="relative w-full py-3.5 rounded-elegant font-semibold text-sm tracking-wide transition-elegant disabled:opacity-50 disabled:cursor-not-allowed group overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-primary via-purple-500 to-pink-500 opacity-100 group-hover:opacity-90 transition-opacity"></div>
            <div class="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 opacity-0 group-hover:opacity-100 transition-opacity transform -skew-x-12"></div>
            <span class="relative z-10 flex items-center justify-center gap-2">
              <svg v-if="isSubmitting" class="w-4 h-4 animate-elegant-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span v-if="isSubmitting">{{ t('common.loading') }}</span>
              <span v-else>{{ isLogin ? t('auth.loginBtn') : t('auth.registerBtn') }}</span>
            </span>
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-sm text-base-content/50">
            {{ isLogin ? t('auth.noAccount') : t('auth.hasAccount') }}
            <button @click="toggleMode" class="font-semibold bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent hover:opacity-80 transition-opacity ml-1">
              {{ isLogin ? t('auth.goRegister') : t('auth.goLogin') }}
            </button>
          </p>
        </div>
      </div>
      
      <p class="text-center text-xs text-base-content/30 mt-8 font-medium tracking-wide">
        {{ t('app.copyright') }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.slide-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-leave-active {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
