import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE } from '../config'

export function useFileImport({ showToast, onImportSuccess }) {
  const { t } = useI18n()
  const showImportModal = ref(false)
  const importType = ref(null)
  const isDragging = ref(false)
  const uploadedFile = ref(null)
  const isUploading = ref(false)
  const uploadResult = ref(null)

  const handleDragOver = (e) => {
    e.preventDefault()
    isDragging.value = true
  }

  const handleDragLeave = () => {
    isDragging.value = false
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    isDragging.value = false
    const files = e.dataTransfer.files
    if (files.length > 0) {
      uploadedFile.value = files[0]
      await detectPlatform()
    }
  }

  const handleFileSelect = async (e) => {
    if (e.target.files.length > 0) {
      uploadedFile.value = e.target.files[0]
      await detectPlatform()
    }
    e.target.value = ''
  }

  const detectPlatform = async () => {
    if (!uploadedFile.value) return

    const formData = new FormData()
    formData.append('file', uploadedFile.value)

    try {
      const response = await fetch(`${API_BASE}/bills/detect`, {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        if (result.platform && result.platform !== 'unknown') {
          importType.value = result.platform
        }
      }
    } catch (error) {
      console.error('detect platform failed:', error)
    }
  }

  const startImport = async () => {
    if (!uploadedFile.value || !importType.value) return

    isUploading.value = true
    uploadResult.value = null

    const formData = new FormData()
    formData.append('file', uploadedFile.value)
    formData.append('platform', importType.value)

    try {
      const response = await fetch(`${API_BASE}/bills/upload`, {
        method: 'POST',
        body: formData
      })

      const result = await response.json()

      if (response.ok) {
        uploadResult.value = {
          type: 'success',
          message: result.message
        }
        await onImportSuccess?.()
        uploadedFile.value = null
        importType.value = null
      } else {
        uploadResult.value = {
          type: 'error',
          message: result.detail || t('import.importFailed')
        }
      }
    } catch (error) {
      uploadResult.value = {
        type: 'error',
        message: t('import.networkError')
      }
      console.error('upload failed:', error)
    } finally {
      isUploading.value = false
    }
  }

  const clearResult = () => {
    uploadResult.value = null
  }

  return {
    showImportModal, importType, isDragging, uploadedFile, isUploading, uploadResult,
    handleDragOver, handleDragLeave, handleDrop, handleFileSelect,
    detectPlatform, startImport, clearResult
  }
}
