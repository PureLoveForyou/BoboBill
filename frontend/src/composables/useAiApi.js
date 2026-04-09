import { ref, computed } from 'vue'
import { API_BASE } from '../config'

// ===== 模块级单例：AI 配置 =====
const aiConfigs = ref([])
const activeConfigId = ref(0)
const isLoading = ref(false)

try { localStorage.removeItem('bobobill_ai_config') } catch {}
try {
  const savedId = localStorage.getItem('bobobill_ai_active_config')
  if (savedId) activeConfigId.value = parseInt(savedId) || 0
} catch {}

// ===== 模块级单例：对话历史（从数据库加载） =====
const chats = ref([])
const activeChatId = ref(null)
const streamAbortController = ref(null)

function _authHeaders() {
  const token = localStorage.getItem('bobobill_token')
  return token ? { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` } : { 'Content-Type': 'application/json' }
}

function _authGetHeaders() {
  const token = localStorage.getItem('bobobill_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

export function useAiApi() {
  // ---- AI 配置相关 ----

  const activeConfig = computed(() => aiConfigs.value.find(c => c.id === activeConfigId.value) || null)
  const isConfigured = computed(() => aiConfigs.value.length > 0)
  const activeModelName = computed(() => {
    const c = activeConfig.value
    return c ? `${c.name} (${c.model})` : ''
  })

  const fetchConfigs = async () => {
    try {
      const response = await fetch(`${API_BASE}/ai/my-configs`, { headers: _authHeaders() })
      if (!response.ok) return
      const data = await response.json()
      aiConfigs.value = data
      if (data.length && !data.find(c => c.id === activeConfigId.value)) {
        activeConfigId.value = data[0].id
        localStorage.setItem('bobobill_ai_active_config', String(data[0].id))
      }
    } catch {}
  }

  const selectConfig = (id) => {
    activeConfigId.value = id
    localStorage.setItem('bobobill_ai_active_config', String(id))
  }

  const saveConfig = async (config) => {
    try {
      if (!localStorage.getItem('bobobill_token')) return { success: false, message: '请先登录' }
      const res = await fetch(`${API_BASE}/ai/save-config`, { method: 'POST', headers: _authHeaders(), body: JSON.stringify(config) })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        if (res.status === 401 || res.status === 403) return { success: false, message: '登录已过期，请重新登录' }
        return { success: false, message: data.detail || '保存失败' }
      }
      const data = await res.json()
      await fetchConfigs()
      if (data.id) selectConfig(data.id)
      return { success: true, id: data.id }
    } catch { return { success: false, message: '网络错误' } }
  }

  const updateConfig = async (id, config) => {
    try {
      if (!localStorage.getItem('bobobill_token')) return { success: false, message: '请先登录' }
      const res = await fetch(`${API_BASE}/ai/update-config/${id}`, { method: 'PUT', headers: _authHeaders(), body: JSON.stringify(config) })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        if (res.status === 401 || res.status === 403) return { success: false, message: '登录已过期，请重新登录' }
        return { success: false, message: data.detail || '更新失败' }
      }
      await fetchConfigs()
      return { success: true }
    } catch { return { success: false, message: '网络错误' } }
  }

  const deleteConfig = async (id) => {
    try {
      if (!localStorage.getItem('bobobill_token')) return { success: false, message: '请先登录' }
      const res = await fetch(`${API_BASE}/ai/delete-config/${id}`, { method: 'DELETE', headers: _authHeaders() })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        if (res.status === 401 || res.status === 403) return { success: false, message: '登录已过期，请重新登录' }
        return { success: false, message: data.detail || '删除失败' }
      }
      await fetchConfigs()
      return { success: true }
    } catch { return { success: false, message: '网络错误' } }
  }

  const getConfigDetail = async (id) => {
    try {
      if (!localStorage.getItem('bobobill_token')) return null
      const res = await fetch(`${API_BASE}/ai/config/${id}`, { headers: _authGetHeaders() })
      if (!res.ok) return null
      return await res.json()
    } catch { return null }
  }

  // ---- 对话历史管理（数据库） ----

  // 当前活跃对话的消息列表（内存缓存）
  const currentMessages = ref([])

  const activeChat = computed(() => chats.value.find(c => c.id === activeChatId.value) || null)

  // 从后端加载所有会话列表
  const fetchChats = async () => {
    try {
      const res = await fetch(`${API_BASE}/ai/chats`, { headers: _authGetHeaders() })
      if (!res.ok) return []
      const data = await res.json()
      chats.value = data
      return data
    } catch { return [] }
  }

  // 创建新会话
  const createChatSession = async (title = '新对话') => {
    try {
      const res = await fetch(`${API_BASE}/ai/chats`, {
        method: 'POST',
        headers: _authHeaders(),
        body: JSON.stringify({ title }),
      })
      if (!res.ok) return null
      const session = await res.json()
      chats.value.unshift(session)
      activeChatId.value = session.id
      currentMessages.value = []
      return session
    } catch { return null }
  }

  // 切换会话（加载消息）
  const switchChatSession = async (chatId) => {
    if (activeChatId.value === chatId && currentMessages.value.length > 0) {
      activeChatId.value = chatId
      return true
    }
    activeChatId.value = chatId
    try {
      const res = await fetch(`${API_BASE}/ai/chats/${chatId}/messages`, { headers: _authGetHeaders() })
      if (!res.ok) { currentMessages.value = []; return false }
      const msgs = await res.json()
      // 过滤掉空的 assistant 消息（思考阶段中断产生的空气泡）
      currentMessages.value = msgs.filter(m => !(m.role === 'assistant' && !m.content && !m.reasoning))
      return true
    } catch { currentMessages.value = []; return false }
  }

  // 删除会话
  const deleteChatSession = async (chatId) => {
    try {
      const res = await fetch(`${API_BASE}/ai/chats/${chatId}`, { method: 'DELETE', headers: _authGetHeaders() })
      if (!res.ok) return false
      const idx = chats.value.findIndex(c => c.id === chatId)
      if (idx !== -1) chats.value.splice(idx, 1)
      if (activeChatId.value === chatId) {
        if (chats.value.length > 0) {
          activeChatId.value = chats.value[0].id
          await switchChatSession(chats.value[0].id)
        } else {
          activeChatId.value = null
          currentMessages.value = []
        }
      }
      return true
    } catch { return false }
  }

  // 清空当前会话的消息
  const clearChatSession = async () => {
    if (!activeChatId.value) return
    // 删除旧会话并创建新会话
    await deleteChatSession(activeChatId.value)
    if (!chats.value.length) {
      await createChatSession()
    }
  }

  // 添加消息到数据库
  const addMessage = async (sessionId, role, content, reasoning = null) => {
    try {
      const res = await fetch(`${API_BASE}/ai/chats/${sessionId}/messages`, {
        method: 'POST',
        headers: _authHeaders(),
        body: JSON.stringify({ role, content, reasoning }),
      })
      if (!res.ok) return null
      return await res.json()
    } catch { return null }
  }

  // 更新消息内容（流式完成后调用）
  const updateMessage = async (sessionId, messageId, content, reasoning) => {
    try {
      const body = {}
      if (content !== undefined) body.content = content
      if (reasoning !== undefined) body.reasoning = reasoning
      await fetch(`${API_BASE}/ai/chats/${sessionId}/messages/${messageId}`, {
        method: 'PUT',
        headers: _authHeaders(),
        body: JSON.stringify(body),
      })
    } catch {}
  }

  // 更新会话标题
  const updateChatTitle = async (chatId, title) => {
    try {
      await fetch(`${API_BASE}/ai/chats/${chatId}/title`, {
        method: 'PUT',
        headers: _authHeaders(),
        body: JSON.stringify({ title }),
      })
      const chat = chats.value.find(c => c.id === chatId)
      if (chat) chat.title = title
    } catch {}
  }

  // ---- 聊天功能 ----

  const chat = async (message, history = []) => {
    if (!isConfigured.value || !activeConfigId.value) return { success: false, message: '请先在设置中配置 AI 服务' }
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000)
      const res = await fetch(`${API_BASE}/ai/chat-full`, {
        method: 'POST', headers: _authHeaders(),
        body: JSON.stringify({ message, history: history.map(m => ({ role: m.role, content: m.content })), ai_config_id: activeConfigId.value }),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        let msg = data.detail || 'AI 请求失败'
        if (res.status === 504) msg = 'AI 响应超时，请稍后再试'
        return { success: false, message: msg }
      }
      const data = await res.json()
      return { success: true, reply: data.reply }
    } catch (e) {
      if (e.name === 'AbortError') return { success: false, message: '请求超时（60秒），请稍后再试' }
      return { success: false, message: '网络错误，请检查服务是否启动' }
    }
  }

  const chatStream = async (message, history = [], onChunk = () => {}, signal = null) => {
    if (!isConfigured.value || !activeConfigId.value) return { success: false, message: '请先在设置中配置 AI 服务' }
    try {
      const res = await fetch(`${API_BASE}/ai/chat-stream`, {
        method: 'POST', headers: _authHeaders(),
        body: JSON.stringify({ message, history: history.map(m => ({ role: m.role, content: m.content })), ai_config_id: activeConfigId.value }),
        signal,
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        let msg = data.detail || 'AI 请求失败'
        if (res.status === 504) msg = 'AI 响应超时，请稍后再试'
        return { success: false, message: msg }
      }
      const reader = res.body.getReader()
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
          try {
            const event = JSON.parse(trimmed.slice(6))
            onChunk(event)
            if (event.type === 'error') return { success: false, message: event.content }
          } catch {}
        }
      }
      return { success: true }
    } catch (e) {
      if (e.name === 'AbortError') return { success: false, message: '已中断', aborted: true }
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
      const res = await fetch(`${API_BASE}/ai/test-connection?${params}`)
      return await res.json()
    } catch { return { success: false, message: '网络错误' } }
  }

  return {
    // 配置
    aiConfigs, activeConfigId, activeConfig, isConfigured, isLoading, activeModelName,
    fetchConfigs, selectConfig, saveConfig, updateConfig, deleteConfig, getConfigDetail,
    // 对话历史
    chats, activeChatId, activeChat, currentMessages,
    fetchChats, createChatSession, switchChatSession, deleteChatSession, clearChatSession,
    addMessage, updateMessage, updateChatTitle,
    // 聊天
    chat, chatStream, streamAbortController, testConnection,
  }
}
