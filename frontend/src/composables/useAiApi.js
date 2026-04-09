import { ref, computed } from 'vue'
import { API_BASE } from '../config'

// 模块级单例，所有组件共享
const aiConfigs = ref([])       // 用户的 AI 配置列表（从后端加载）
const activeConfigId = ref(0)   // 当前选中的配置 ID
const isLoading = ref(false)    // 加载状态

// 清理旧的 localStorage 配置（迁移到数据库后不再需要）
try {
  localStorage.removeItem('bobobill_ai_config')
} catch { /* ignore */ }

// 从 localStorage 恢复上次选中的配置 ID
try {
  const savedId = localStorage.getItem('bobobill_ai_active_config')
  if (savedId) activeConfigId.value = parseInt(savedId) || 0
} catch { /* ignore */ }

export function useAiApi() {
  // 当前激活的配置
  const activeConfig = computed(() => {
    return aiConfigs.value.find(c => c.id === activeConfigId.value) || null
  })

  const isConfigured = computed(() => aiConfigs.value.length > 0)

  // 当前选中的配置名（用于显示）
  const activeModelName = computed(() => {
    const c = activeConfig.value
    return c ? `${c.name} (${c.model})` : ''
  })

  // 从后端加载配置列表
  const fetchConfigs = async () => {
    try {
      const token = localStorage.getItem('bobobill_token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const response = await fetch(`${API_BASE}/ai/my-configs`, { headers })
      if (!response.ok) return
      const data = await response.json()
      aiConfigs.value = data

      // 如果当前选中的 ID 不在列表中，自动选第一个
      if (data.length && !data.find(c => c.id === activeConfigId.value)) {
        activeConfigId.value = data[0].id
        localStorage.setItem('bobobill_ai_active_config', String(data[0].id))
      }
    } catch { /* ignore */ }
  }

  // 选择配置
  const selectConfig = (id) => {
    activeConfigId.value = id
    localStorage.setItem('bobobill_ai_active_config', String(id))
  }

  // 保存配置（新增）
  const saveConfig = async (config) => {
    try {
      const token = localStorage.getItem('bobobill_token')
      if (!token) {
        return { success: false, message: '请先登录' }
      }
      const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }

      const response = await fetch(`${API_BASE}/ai/save-config`, {
        method: 'POST',
        headers,
        body: JSON.stringify(config),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        if (response.status === 401 || response.status === 403) {
          return { success: false, message: '登录已过期，请重新登录' }
        }
        return { success: false, message: data.detail || '保存失败' }
      }
      const data = await response.json()
      await fetchConfigs()
      // 自动选中新创建的配置
      if (data.id) selectConfig(data.id)
      return { success: true, id: data.id }
    } catch {
      return { success: false, message: '网络错误' }
    }
  }

  // 更新配置
  const updateConfig = async (id, config) => {
    try {
      const token = localStorage.getItem('bobobill_token')
      if (!token) {
        return { success: false, message: '请先登录' }
      }
      const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }

      const response = await fetch(`${API_BASE}/ai/update-config/${id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(config),
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        if (response.status === 401 || response.status === 403) {
          return { success: false, message: '登录已过期，请重新登录' }
        }
        return { success: false, message: data.detail || '更新失败' }
      }
      await fetchConfigs()
      return { success: true }
    } catch {
      return { success: false, message: '网络错误' }
    }
  }

  // 删除配置
  const deleteConfig = async (id) => {
    try {
      const token = localStorage.getItem('bobobill_token')
      if (!token) {
        return { success: false, message: '请先登录' }
      }
      const headers = { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }

      const response = await fetch(`${API_BASE}/ai/delete-config/${id}`, {
        method: 'DELETE',
        headers,
      })
      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        if (response.status === 401 || response.status === 403) {
          return { success: false, message: '登录已过期，请重新登录' }
        }
        return { success: false, message: data.detail || '删除失败' }
      }
      await fetchConfigs()
      return { success: true }
    } catch {
      return { success: false, message: '网络错误' }
    }
  }

  // 获取完整配置详情（含完整 API Key）
  const getConfigDetail = async (id) => {
    try {
      const token = localStorage.getItem('bobobill_token')
      if (!token) return null
      const headers = { 'Authorization': `Bearer ${token}` }

      const response = await fetch(`${API_BASE}/ai/config/${id}`, { headers })
      if (!response.ok) return null
      return await response.json()
    } catch {
      return null
    }
  }

  const _getAuthHeaders = () => {
    const token = localStorage.getItem('bobobill_token')
    const headers = { 'Content-Type': 'application/json' }
    if (token) headers['Authorization'] = `Bearer ${token}`
    return headers
  }

  const chat = async (message, history = []) => {
    if (!isConfigured.value || !activeConfigId.value) {
      return { success: false, message: '请先在设置中配置 AI 服务' }
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000)

      const response = await fetch(`${API_BASE}/ai/chat-full`, {
        method: 'POST',
        headers: _getAuthHeaders(),
        body: JSON.stringify({
          message,
          history: history.map(m => ({ role: m.role, content: m.content })),
          ai_config_id: activeConfigId.value,
        }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        let msg = data.detail || 'AI 请求失败'
        if (response.status === 504) msg = 'AI 响应超时，请稍后再试'
        return { success: false, message: msg }
      }

      const data = await response.json()
      return { success: true, reply: data.reply }
    } catch (e) {
      if (e.name === 'AbortError') {
        return { success: false, message: '请求超时（60秒），请稍后再试' }
      }
      return { success: false, message: '网络错误，请检查服务是否启动' }
    }
  }

  /**
   * 流式聊天，回调实时接收 chunk
   */
  const chatStream = async (message, history = [], onChunk = () => {}) => {
    if (!isConfigured.value || !activeConfigId.value) {
      return { success: false, message: '请先在设置中配置 AI 服务' }
    }

    try {
      const response = await fetch(`${API_BASE}/ai/chat-stream`, {
        method: 'POST',
        headers: _getAuthHeaders(),
        body: JSON.stringify({
          message,
          history: history.map(m => ({ role: m.role, content: m.content })),
          ai_config_id: activeConfigId.value,
        }),
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        let msg = data.detail || 'AI 请求失败'
        if (response.status === 504) msg = 'AI 响应超时，请稍后再试'
        return { success: false, message: msg }
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          const dataStr = trimmed.slice(6)
          try {
            const event = JSON.parse(dataStr)
            onChunk(event)
            if (event.type === 'error') {
              return { success: false, message: event.content }
            }
          } catch {
            // 忽略解析错误
          }
        }
      }

      return { success: true }
    } catch (e) {
      return { success: false, message: '网络错误，请检查服务是否启动' }
    }
  }

  const testConnection = async (config) => {
    try {
      const params = new URLSearchParams({
        provider: config.provider,
        api_key: config.apiKey || config.api_key || '',
        api_url: config.apiUrl || config.api_url || '',
        model: config.model || '',
      })
      const response = await fetch(`${API_BASE}/ai/test-connection?${params}`)
      return await response.json()
    } catch {
      return { success: false, message: '网络错误' }
    }
  }

  return {
    aiConfigs,
    activeConfigId,
    activeConfig,
    activeModelName,
    isConfigured,
    isLoading,
    fetchConfigs,
    selectConfig,
    saveConfig,
    updateConfig,
    deleteConfig,
    getConfigDetail,
    chat,
    chatStream,
    testConnection,
  }
}
