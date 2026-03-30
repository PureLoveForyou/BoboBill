import { ref, onUnmounted } from 'vue'

export function useToast() {
  const toast = ref(null)
  const toastTimer = ref(null)

  const showToast = (message, type = 'info') => {
    toast.value = { message, type }
    clearTimeout(toastTimer.value)
    toastTimer.value = setTimeout(() => { toast.value = null }, 3000)
  }

  onUnmounted(() => {
    clearTimeout(toastTimer.value)
  })

  return { toast, showToast }
}
