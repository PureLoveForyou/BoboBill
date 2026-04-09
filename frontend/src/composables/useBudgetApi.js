import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE } from '../config'
import { useToast } from './useToast'

function getAuthHeaders() {
  const token = localStorage.getItem('bobobill_token')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

export function useBudgetApi() {
  const { t } = useI18n()
  const { showToast } = useToast()

  const budget = ref({ monthly_total: 0, category_budgets: {} })
  const budgetStatus = ref(null)
  const isLoading = ref(false)

  const fetchBudget = async () => {
    try {
      const response = await fetch(`${API_BASE}/budget`, {
        headers: getAuthHeaders()
      })
      if (response.ok) {
        budget.value = await response.json()
      }
    } catch (error) {
      console.error('fetch budget failed:', error)
    }
  }

  const fetchBudgetStatus = async () => {
    isLoading.value = true
    try {
      const response = await fetch(`${API_BASE}/budget/status`, {
        headers: getAuthHeaders()
      })
      if (response.ok) {
        budgetStatus.value = await response.json()
      }
    } catch (error) {
      console.error('fetch budget status failed:', error)
    } finally {
      isLoading.value = false
    }
  }

  const saveBudget = async (data) => {
    try {
      const response = await fetch(`${API_BASE}/budget`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      })
      if (response.ok) {
        budget.value = await response.json()
        showToast(t('budget.saveSuccess'), 'success')
        return true
      } else {
        showToast(t('budget.saveFailed'), 'error')
        return false
      }
    } catch (error) {
      console.error('save budget failed:', error)
      showToast(t('budget.saveFailed'), 'error')
      return false
    }
  }

  return {
    budget, budgetStatus, isLoading,
    fetchBudget, fetchBudgetStatus, saveBudget
  }
}
