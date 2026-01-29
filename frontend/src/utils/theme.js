/**
 * 极简深色/浅色模式切换工具
 */

// 主题存储键名
const THEME_STORAGE_KEY = 'bobobill-theme'

/**
 * 获取当前主题
 * @returns {string} 'light' 或 'dark'
 */
export function getCurrentTheme() {
  // 1. 检查localStorage
  const storedTheme = localStorage.getItem(THEME_STORAGE_KEY)
  if (storedTheme === 'light' || storedTheme === 'dark') {
    return storedTheme
  }
  
  // 2. 检查系统偏好
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  
  // 3. 返回默认浅色主题
  return 'light'
}

/**
 * 设置主题
 * @param {string} theme 'light' 或 'dark'
 */
export function setTheme(theme) {
  // 只允许 light 或 dark
  if (theme !== 'light' && theme !== 'dark') {
    theme = 'light'
  }
  
  // 保存到localStorage
  localStorage.setItem(THEME_STORAGE_KEY, theme)
  
  // 应用到文档
  document.documentElement.setAttribute('data-theme', theme)
  
  // 触发自定义事件，让其他组件可以响应主题变化
  window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }))
  
  return theme
}

/**
 * 初始化主题
 */
export function initTheme() {
  const theme = getCurrentTheme()
  setTheme(theme)
  
  // 监听系统主题变化
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      // 只有当用户没有手动设置主题时才跟随系统
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        setTheme(e.matches ? 'dark' : 'light')
      }
    })
  }
}

/**
 * 切换深色/浅色模式
 * @returns {string} 切换后的主题
 */
export function toggleDarkLight() {
  const currentTheme = getCurrentTheme()
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark'
  return setTheme(newTheme)
}