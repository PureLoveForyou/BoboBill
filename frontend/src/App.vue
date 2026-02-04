<script setup>
import { useRouter } from 'vue-router'
import { ref, watch, onMounted } from 'vue'
import { initTheme, toggleDarkLight, getCurrentTheme } from './utils/theme.js'
import Sidebar from './components/Sidebar.vue'

const router = useRouter()
const currentTheme = ref('light')

// 初始化主题
onMounted(() => {
  initTheme()
  currentTheme.value = getCurrentTheme()
  
  // 监听主题变化
  window.addEventListener('themechange', (event) => {
    currentTheme.value = event.detail.theme
  })
})

// 切换深色/浅色模式
const toggleTheme = () => {
  const newTheme = toggleDarkLight()
  currentTheme.value = newTheme
}

// 监听路由变化，在移动端关闭侧边栏
watch(() => router.currentRoute.value.path, () => {
  const drawerCheckbox = document.getElementById('sidebar-drawer')
  if (drawerCheckbox && window.innerWidth < 1024) {
    drawerCheckbox.checked = false
  }
})
</script>

<template>
  <div class="drawer lg:drawer-open">
    <input id="sidebar-drawer" type="checkbox" class="drawer-toggle" />
    
    <div class="drawer-content flex flex-col">
      <!-- 移动端固定导航栏 -->
      <div class="sticky top-0 z-10 lg:hidden">
        <div class="flex items-center justify-between bg-base-100 shadow-sm px-4 py-3">
          <div class="flex items-center">
            <label for="sidebar-drawer" class="btn btn-ghost p-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </label>
            <h1 class="text-xl font-bold ml-3">BoboBill</h1>
          </div>
          <button @click="toggleTheme" class="btn btn-ghost p-2" :title="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'">
            <span v-if="currentTheme === 'dark'" class="text-xl">🌙</span>
            <span v-else class="text-xl">☀️</span>
          </button>
        </div>
      </div>
      
      <!-- 页面内容 -->
      <div class="flex-1 p-4">
        <router-view />
      </div>
    </div>
    
    <!-- 侧边栏组件 -->
    <Sidebar />
  </div>
</template>