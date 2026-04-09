import {createRouter, createWebHistory} from 'vue-router'
import Dashboard from '../pages/Dashboard.vue'
import Bills from '../pages/Bills.vue'
import Settings from '../pages/Settings.vue'
import Login from '../pages/Login.vue'

const routes = [
    { path: '/login', component: Login, meta: { guest: true } },
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard, meta: { auth: true } },
    { path: '/bills', component: Bills, meta: { auth: true } },
    { path: '/settings', component: Settings, meta: { auth: true } }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('bobobill_token')
    const isLoggedIn = !!token

    if (to.meta.auth && !isLoggedIn) {
        next('/login')
    } else if (to.meta.guest && isLoggedIn) {
        next('/dashboard')
    } else {
        next()
    }
})

export default router
