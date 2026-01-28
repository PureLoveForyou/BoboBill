<script setup>
</script>

<template>
  <div class="drawer lg:drawer-open">
    <input id="sidebar-drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col">
      <!-- 移动端固定导航栏 -->
      <div class="sticky top-0 z-10 lg:hidden">
        <div class="flex items-center bg-base-100 shadow-sm px-4 py-3 min-h-[4rem]">
          <label for="sidebar-drawer" class="btn btn-ghost p-2 flex-shrink-0">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </label>
          <h1 class="text-xl font-bold ml-3 flex-1">BoboBill</h1>
        </div>
      </div>
      
      <!-- 页面内容 -->
      <div class="flex-1 p-4">
        <router-view />
      </div>
    </div>
    <div class="drawer-side">
      <label for="sidebar-drawer" class="drawer-overlay"></label>
      <ul class="menu p-4 w-80 min-h-full bg-base-200 text-base-content">
        <!-- Sidebar content here -->
        <li class="mb-4">
          <h1 class="text-xl font-bold">BoboBill</h1>
        </li>
        <li>
          <router-link to="/dashboard" class="active:bg-base-300">Dashboard</router-link>
        </li>
        <li>
          <router-link to="/settings" class="active:bg-base-300">Settings</router-link>
        </li>
      </ul>
    </div>
  </div>
</template>