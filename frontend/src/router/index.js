import {createRouter, createWebHistory} from 'vue-router'
import Dashboard from '../pages/Dashboard.vue'
import Settings from '../pages/Settings.vue'

const routes = [
    { path: '/dashboard', component: Dashboard },
    { path: '/settings', component: Settings }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router