<script setup>
import { useRouter } from 'vue-router'
import { ref, watch } from 'vue'

const router = useRouter()

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
        <div class="flex items-center bg-base-100 shadow-sm px-4 py-3">
          <label for="sidebar-drawer" class="btn btn-ghost p-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </label>
          <h1 class="text-xl font-bold ml-3">BoboBill</h1>
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
      </ul>
    </div>
  </div>
</template>