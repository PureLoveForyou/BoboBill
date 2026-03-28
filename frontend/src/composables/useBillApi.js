import { ref } from 'vue'
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
        // Support both paginated {items, total} and legacy array format
        if (Array.isArray(data)) {
          bills.value = data
          total.value = data.length
        } else {
          bills.value = data.items
          total.value = data.total
        }
        onBillsChanged?.()
      } else {
        showToast('获取账单失败: ' + response.status)
      }
    } catch (error) {
      console.error('获取账单失败:', error)
      showToast('无法连接服务器，请检查网络')
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
      console.error('加载更多失败:', error)
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
        showToast('保存成功')
      } else {
        const result = await response.json()
        showToast('保存失败: ' + (result.detail || '未知错误'))
      }
    } catch (error) {
      console.error('保存失败:', error)
      showToast('无法连接服务器')
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
        showToast('更新成功')
      } else {
        const result = await response.json()
        showToast('更新失败: ' + (result.detail || '未知错误'))
      }
    } catch (error) {
      console.error('更新失败:', error)
      showToast('无法连接服务器')
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
        showToast('删除成功')
      } else {
        const result = await response.json()
        showToast('删除失败: ' + (result.detail || '未知错误'))
      }
    } catch (error) {
      console.error('删除失败:', error)
      showToast('无法连接服务器')
    }
  }

  return {
    bills, total, isLoading, fetchBills, loadMore,
    showAddModal, newBill, isSaving, openAddModal, closeAddModal, saveBill,
    showEditModal, editingBill, openEditModal, closeEditModal, updateBill,
    showDeleteModal, deletingBill, openDeleteModal, closeDeleteModal, confirmDelete
  }
}
