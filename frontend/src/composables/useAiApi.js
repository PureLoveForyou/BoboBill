import { ref, computed } from 'vue'
import { API_BASE } from '../config'

// 模块级单例，所有组件共享
const aiConfig = ref({
  provider: 'deepseek',
  apiKey: '',
  apiUrl: '',
  model: 'deepseek-chat'
})

// 首次导入时从 localStorage 初始化
;(function init() {
  try {
    const raw = JSON.parse(localStorage.getItem('bobobill_ai_config') || '{}')
    if (raw.apiKey) {
      aiConfig.value = {
        provider: raw.provider || 'deepseek',
        apiKey: raw.apiKey || '',
        apiUrl: raw.apiUrl || '',
        model: raw.model || 'deepseek-chat'
      }
    }
  } catch { /* ignore */ }
})()

export function useAiApi() {
  const config = computed(() => aiConfig.value)
  const isConfigured = computed(() => !!aiConfig.value.apiKey)

  const saveConfig = (newConfig) => {
    aiConfig.value = { ...aiConfig.value, ...newConfig }
    localStorage.setItem('bobobill_ai_config', JSON.stringify(aiConfig.value))
  }

  const reloadConfig = () => {
    try {
      const raw = JSON.parse(localStorage.getItem('bobobill_ai_config') || '{}')
      aiConfig.value = {
        provider: raw.provider || 'deepseek',
        apiKey: raw.apiKey || '',
        apiUrl: raw.apiUrl || '',
        model: raw.model || 'deepseek-chat'
      }
    } catch { /* ignore */ }
  }

  const chat = async (message, history = []) => {
    if (!isConfigured.value) {
      return { success: false, message: '请先在设置中配置 AI 服务' }
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000)

      const token = localStorage.getItem('bobobill_token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      // 字段名必须和后端 ConfiguredChatRequest 一致！
      const response = await fetch(`${API_BASE}/ai/chat-full`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          history: history.map(m => ({ role: m.role, content: m.content })),
          ai_provider: aiConfig.value.provider,
          ai_api_key: aiConfig.value.apiKey,
          ai_api_url: aiConfig.value.apiUrl,
          ai_model: aiConfig.value.model
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
   * @param {string} message - 用户消息
   * @param {Array} history - 历史消息
   * @param {Function} onChunk - (event) => void, event = { type: 'content'|'reasoning'|'error'|'done', content?: string }
   * @returns {Promise<{success: boolean, message?: string}>}
   */
  const chatStream = async (message, history = [], onChunk = () => {}) => {
    if (!isConfigured.value) {
      return { success: false, message: '请先在设置中配置 AI 服务' }
    }

    try {
      const token = localStorage.getItem('bobobill_token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const response = await fetch(`${API_BASE}/ai/chat-stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message,
          history: history.map(m => ({ role: m.role, content: m.content })),
          ai_provider: aiConfig.value.provider,
          ai_api_key: aiConfig.value.apiKey,
          ai_api_url: aiConfig.value.apiUrl,
          ai_model: aiConfig.value.model
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
        // 保留最后一行（可能不完整）
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

  const testConnection = async () => {
    if (!isConfigured.value) {
      return { success: false, message: '请先配置 API Key' }
    }
    try {
      const params = new URLSearchParams({
        provider: aiConfig.value.provider,
        api_key: aiConfig.value.apiKey,
        api_url: aiConfig.value.apiUrl,
        model: aiConfig.value.model
      })
      const response = await fetch(`${API_BASE}/ai/test-connection?${params}`)
      const data = await response.json()
      return data
    } catch {
      return { success: false, message: '网络错误' }
    }
  }

  return { config, isConfigured, saveConfig, reloadConfig, chat, chatStream, testConnection }
}
