import { createRouter, createWebHistory } from 'vue-router'
import i18n from '../i18n'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '新建对接任务' }
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('../views/TaskListView.vue'),
    meta: { title: '任务队列与历史' }
  },
  {
    path: '/result/:taskId',
    name: 'result',
    component: () => import('../views/ResultView.vue'),
    meta: { title: '对接结果分析' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('../views/SettingsView.vue'),
    meta: { title: '软件配置管理' }
  },
  {
    path: '/help',
    name: 'help',
    component: () => import('../views/HelpView.vue'),
    meta: { title: '使用说明' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.afterEach((to) => {
  const pageTitle = i18n.global.t(to.meta.title || '平台')
  const brandTitle = i18n.global.t('CADD 分子对接平台')
  document.title = `${pageTitle} | ${brandTitle}`
})

export default router
