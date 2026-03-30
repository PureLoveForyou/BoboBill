import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { API_BASE } from '../config'
import { DEFAULT_BILL } from '../constants/bill'

function buildQuery(params) {
  const qs = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') qs.append(k, v)
  }
  const s = qs.toString()
  return s ? `?${s}` : ''
}

export function useBillApi({ showToast, onBillsChanged }) {
  const { t } = useI18n()
  const bills = ref([])
  const total = ref(0)
  const isLoading = ref(false)

  const fetchBills = async (params = {}) => {
    isLoading.value = true
    try {
      const query = buildQuery(params)
      const response = await fetch(`${API_BASE}/bills${query}`)
      if (response.ok) {
        const data = await response.json()
        if (Array.isArray(data)) {
          bills.value = data
          total.value = data.length
        } else {
          bills.value = data.items
          total.value = data.total
        }
        onBillsChanged?.()
      } else {
        showToast(t('bill.fetchFailed') + ': ' + response.status, 'error')
      }
    } catch (error) {
      console.error('fetch bills failed:', error)
      showToast(t('bill.serverUnavailable'), 'error')
    } finally {
      isLoading.value = false
    }
  }

  const loadMore = async (params = {}) => {
    const currentPage = Math.ceil(bills.value.length / (params.page_size || 20)) + 1
    try {
      const query = buildQuery({ ...params, page: currentPage })
      const response = await fetch(`${API_BASE}/bills${query}`)
      if (response.ok) {
        const data = await response.json()
        const newItems = Array.isArray(data) ? data : data.items
        bills.value = [...bills.value, ...newItems]
        total.value = Array.isArray(data) ? bills.value.length : data.total
      }
    } catch (error) {
      console.error('load more failed:', error)
    }
  }

  // --- Add Modal ---
  const showAddModal = ref(false)
  const newBill = ref(DEFAULT_BILL())
  const isSaving = ref(false)

  const openAddModal = () => {
    newBill.value = DEFAULT_BILL()
    showAddModal.value = true
  }

  const closeAddModal = () => {
    showAddModal.value = false
  }

  const saveBill = async () => {
    if (!newBill.value.name || !newBill.value.amount || !newBill.value.date) return

    isSaving.value = true

    try {
      const amount = parseFloat(newBill.value.amount)
      const billData = {
        name: newBill.value.name,
        amount: newBill.value.type === 'expense' ? -Math.abs(amount) : Math.abs(amount),
        type: newBill.value.type,
        date: newBill.value.date,
        category: newBill.value.category,
        platform: newBill.value.platform,
        note: newBill.value.note || ''
      }

      const response = await fetch(`${API_BASE}/bills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(billData)
      })

      if (response.ok) {
        await fetchBills()
        closeAddModal()
        showToast(t('bill.saveSuccess'), 'success')
      } else {
        const result = await response.json()
        showToast(t('bill.saveFailed') + ': ' + (result.detail || ''), 'error')
      }
    } catch (error) {
      console.error('save failed:', error)
      showToast(t('bill.serverUnavailable'), 'error')
    } finally {
      isSaving.value = false
    }
  }

  // --- Edit Modal ---
  const showEditModal = ref(false)
  const editingBill = ref({
    id: null,
    name: '',
    amount: '',
    type: 'expense',
    date: '',
    category: '其他',
    platform: 'wechat',
    note: ''
  })

  const openEditModal = (bill) => {
    editingBill.value = {
      id: bill.id,
      name: bill.name,
      amount: Math.abs(bill.amount),
      type: bill.type || (bill.amount >= 0 ? 'income' : 'expense'),
      date: bill.date,
      category: bill.category || '其他',
      platform: bill.platform || 'wechat',
      note: bill.note || ''
    }
    showEditModal.value = true
  }

  const closeEditModal = () => {
    showEditModal.value = false
  }

  const updateBill = async () => {
    if (!editingBill.value.name || !editingBill.value.amount || !editingBill.value.date) return

    isSaving.value = true

    try {
      const amount = parseFloat(editingBill.value.amount)
      const billData = {
        name: editingBill.value.name,
        amount: editingBill.value.type === 'expense' ? -Math.abs(amount) : Math.abs(amount),
        type: editingBill.value.type,
        date: editingBill.value.date,
        category: editingBill.value.category,
        platform: editingBill.value.platform,
        note: editingBill.value.note || ''
      }

      const response = await fetch(`${API_BASE}/bills/${editingBill.value.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(billData)
      })

      if (response.ok) {
        await fetchBills()
        closeEditModal()
        showToast(t('bill.updateSuccess'), 'success')
      } else {
        const result = await response.json()
        showToast(t('bill.updateFailed') + ': ' + (result.detail || ''), 'error')
      }
    } catch (error) {
      console.error('update failed:', error)
      showToast(t('bill.serverUnavailable'), 'error')
    } finally {
      isSaving.value = false
    }
  }

  // --- Delete Modal ---
  const showDeleteModal = ref(false)
  const deletingBill = ref(null)

  const openDeleteModal = (bill) => {
    deletingBill.value = bill
    showDeleteModal.value = true
  }

  const closeDeleteModal = () => {
    showDeleteModal.value = false
    deletingBill.value = null
  }

  const confirmDelete = async () => {
    if (!deletingBill.value) return

    try {
      const response = await fetch(`${API_BASE}/bills/${deletingBill.value.id}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        await fetchBills()
        closeDeleteModal()
        showToast(t('bill.deleteSuccess'), 'success')
      } else {
        const result = await response.json()
        showToast(t('bill.deleteFailed') + ': ' + (result.detail || ''), 'error')
      }
    } catch (error) {
      console.error('delete failed:', error)
      showToast(t('bill.serverUnavailable'), 'error')
    }
  }

  const exportBills = async (params = {}) => {
    try {
      const query = buildQuery(params)
      const url = `${API_BASE}/bills/export${query}`
      const a = document.createElement('a')
      a.href = url
      a.download = 'bills.csv'
      a.target = '_blank'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    } catch (error) {
      console.error('export failed:', error)
      showToast(t('bill.exportFailed'), 'error')
    }
  }

  // --- Batch Delete ---
  const batchDeleteBills = async (ids) => {
    if (!ids || ids.length === 0) return false

    try {
      const response = await fetch(`${API_BASE}/bills/batch-delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ids)
      })

      if (response.ok) {
        const result = await response.json()
        showToast(t('bill.batchDeleteSuccess', { n: result.deleted }), 'success')
        return true
      } else {
        const result = await response.json()
        showToast(t('bill.deleteFailed') + ': ' + (result.detail || ''), 'error')
        return false
      }
    } catch (error) {
      console.error('batch delete failed:', error)
      showToast(t('bill.serverUnavailable'), 'error')
      return false
    }
  }

  return {
    bills, total, isLoading, fetchBills, loadMore, exportBills, batchDeleteBills,
    showAddModal, newBill, isSaving, openAddModal, closeAddModal, saveBill,
    showEditModal, editingBill, openEditModal, closeEditModal, updateBill,
    showDeleteModal, deletingBill, openDeleteModal, closeDeleteModal, confirmDelete
  }
}
