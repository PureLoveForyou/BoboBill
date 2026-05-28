import { ref } from 'vue'
import { API_BASE } from '../config'
import { getAuthHeaders } from '../utils/api'

export function useBudgetApi() {
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
        return true
      } else {
        return false
      }
    } catch (error) {
      console.error('save budget failed:', error)
      return false
    }
  }

  return {
    budget, budgetStatus,
    fetchBudget, fetchBudgetStatus, saveBudget
  }
}
