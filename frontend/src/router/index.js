import {createRouter, createWebHistory} from 'vue-router'
import Dashboard from '../pages/Dashboard.vue'
import Bills from '../pages/Bills.vue'
import Settings from '../pages/Settings.vue'

const routes = [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard },
    { path: '/bills', component: Bills },
    { path: '/settings', component: Settings }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router