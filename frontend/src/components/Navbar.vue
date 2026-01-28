<script setup>
</script>

<template>
  <div class="navbar bg-base-100 shadow-md">
    <div class="navbar-start">
      <a class="btn btn-ghost text-xl" href="/">BoboBill</a>
    </div>
    <div class="navbar-center hidden lg:flex">
      <ul class="menu menu-horizontal px-1">
        <li><a href="/dashboard">Dashboard</a></li>
        <li><a href="/settings">Settings</a></li>
      </ul>
    </div>
    <div class="navbar-end">
      <a class="btn btn-primary" href="/dashboard">Go to Dashboard</a>
    </div>
  </div>
</template>