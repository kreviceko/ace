import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '', name: 'create', component: () => import('@/pages/CreatePage.vue') },
      { path: 'library', name: 'library', component: () => import('@/pages/LibraryPage.vue') },
      { path: 'lyrics', name: 'lyrics', component: () => import('@/pages/LyricsPage.vue') },
      { path: 'settings', name: 'settings', component: () => import('@/pages/SettingsPage.vue') },
    ],
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
