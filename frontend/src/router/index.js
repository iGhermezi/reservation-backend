import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/home/HomeView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  // صفحه‌های بعدی رو این‌جا اضافه کن (lazy load):
  // { path: '/login', name: 'login', component: () => import('../views/auth/LoginView.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})