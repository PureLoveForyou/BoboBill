import { ref, computed } from 'vue'
import { API_BASE } from '../config'

const user = ref(JSON.parse(localStorage.getItem('bobobill_user') || 'null'))
const token = ref(localStorage.getItem('bobobill_token') || '')

export function useAuth() {
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  const setAuth = (data) => {
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('bobobill_token', data.access_token)
    localStorage.setItem('bobobill_user', JSON.stringify(data.user))
  }

  const fetchWithTimeout = (url, options, timeout = 10000) => {
    return Promise.race([
      fetch(url, options),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('timeout')), timeout)
      )
    ])
  }

  const register = async (username, password) => {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      if (response.ok) {
        const data = await response.json()
        setAuth(data)
        return { success: true }
      }
      let message = '注册失败'
      try {
        const result = await response.json()
        message = result.detail || message
      } catch {}
      if (response.status === 422) {
        message = '请求参数错误'
      }
      return { success: false, message }
    } catch (e) {
      if (e.message === 'timeout') {
        return { success: false, message: '请求超时，请检查网络连接' }
      }
      return { success: false, message: '网络连接失败，请检查服务是否启动' }
    }
  }

  const login = async (username, password) => {
    try {
      const response = await fetchWithTimeout(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      if (response.ok) {
        const data = await response.json()
        setAuth(data)
        return { success: true }
      }
      let message = '登录失败'
      try {
        const result = await response.json()
        message = result.detail || message
      } catch {}
      if (response.status === 401) {
        message = '用户名或密码错误'
      } else if (response.status === 422) {
        message = '请求参数错误'
      }
      return { success: false, message }
    } catch (e) {
      if (e.message === 'timeout') {
        return { success: false, message: '请求超时，请检查网络连接' }
      }
      return { success: false, message: '网络连接失败，请检查服务是否启动' }
    }
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('bobobill_token')
    localStorage.removeItem('bobobill_user')
  }

  const authHeaders = computed(() => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token.value}`
  }))

  return {
    user,
    token,
    isLoggedIn,
    register,
    login,
    logout,
    authHeaders
  }
}
