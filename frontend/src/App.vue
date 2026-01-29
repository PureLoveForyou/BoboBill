<script setup>
import { useRouter } from 'vue-router'
import { ref, watch, onMounted } from 'vue'
import { initTheme, toggleDarkLight, getCurrentTheme } from './utils/theme.js'

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
    <div class="drawer-side">
      <label for="sidebar-drawer" class="drawer-overlay"></label>
      <ul class="menu p-4 w-60 min-h-full bg-base-200 text-base-content">
        <!-- Sidebar content here -->
        <li class="mb-4">
          <h1 class="text-xl font-bold">BoboBill</h1>
        </li>
        <li>
          <router-link to="/dashboard">Dashboard</router-link>
        </li>
        <li>
          <router-link to="/settings">Settings</router-link>
        </li>
        <li class="mt-auto pt-4 border-t border-base-300">
          <div class="flex items-center justify-between">
            <span class="text-sm opacity-70">主题</span>
            <button @click="toggleTheme" class="btn btn-sm btn-ghost" :title="currentTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'">
              <span v-if="currentTheme === 'dark'" class="text-lg">🌙 深色</span>
              <span v-else class="text-lg">☀️ 浅色</span>
            </button>
          </div>
          <div class="text-xs opacity-50 mt-1">
            当前: {{ currentTheme }}
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>