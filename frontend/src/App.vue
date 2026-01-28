<script setup>
</script>

<template>
  <div class="drawer lg:drawer-open">
    <input id="sidebar-drawer" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content flex flex-col">
      <!-- Page content here -->
      <label for="sidebar-drawer" class="btn btn-primary drawer-button lg:hidden">Open sidebar</label>
      <slot />
    </div>
    <div class="drawer-side">
      <label for="sidebar-drawer" class="drawer-overlay"></label>
      <ul class="menu p-4 w-80 min-h-full bg-base-200 text-base-content">
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