<script setup>
import { ref, onMounted } from 'vue'
import { getCurrentTheme, toggleDarkLight } from '../utils/theme.js'

const currentTheme = ref('light')

// 初始化
onMounted(() => {
  currentTheme.value = getCurrentTheme()
  
  // 监听主题变化
  window.addEventListener('themechange', (event) => {
    currentTheme.value = event.detail.theme
  })
})

// 切换深色/浅色
const toggleTheme = () => {
  currentTheme.value = toggleDarkLight()
}
</script>

<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">设置</h1>
    
    <!-- 主题设置 -->
    <div class="card bg-base-100 shadow-lg mb-6">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">主题设置</h2>
        
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 bg-base-200 rounded-lg">
            <div>
              <h3 class="font-semibold">深色/浅色模式</h3>
              <p class="text-sm opacity-70">当前: {{ currentTheme === 'dark' ? '深色模式' : '浅色模式' }}</p>
            </div>
            <button @click="toggleTheme" class="btn btn-primary">
              <span v-if="currentTheme === 'dark'">🌙 切换到浅色</span>
              <span v-else>☀️ 切换到深色</span>
            </button>
          </div>
          
          <div class="text-sm opacity-70">
            <p>💡 点击按钮切换深色/浅色模式</p>
            <p>🌓 系统会自动跟随您的操作系统主题偏好</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 其他设置 -->
    <div class="card bg-base-100 shadow-lg">
      <div class="card-body">
        <h2 class="card-title text-xl mb-4">其他设置</h2>
        <p>其他设置功能将在后续版本中添加。</p>
      </div>
    </div>
  </div>
</template>