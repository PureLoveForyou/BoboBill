import { ref, onUnmounted } from 'vue'

export function useToast() {
  const toast = ref('')
  const toastTimer = ref(null)

  const showToast = (msg) => {
    toast.value = msg
    clearTimeout(toastTimer.value)
    toastTimer.value = setTimeout(() => { toast.value = '' }, 3000)
  }

  onUnmounted(() => {
    clearTimeout(toastTimer.value)
  })

  return { toast, showToast }
}
