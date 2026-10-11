import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const AppLayout = () => import('../layouts/AppLayout.vue')
const AdminLayout = () => import('../layouts/AdminLayout.vue')

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'home', component: () => import('../views/HomeView.vue') },
        { path: 'books/:id', name: 'book-detail', component: () => import('../views/BookDetailView.vue') },
        { path: 'login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guestOnly: true } },
        { path: 'register', name: 'register', component: () => import('../views/RegisterView.vue'), meta: { guestOnly: true } },
        { path: 'my/borrows', name: 'my-borrows', component: () => import('../views/MyBorrowsView.vue'), meta: { requiresAuth: true } },
        { path: 'messages', name: 'messages', component: () => import('../views/MessagesView.vue'), meta: { requiresAuth: true } },
        { path: 'profile', name: 'profile', component: () => import('../views/ProfileView.vue'), meta: { requiresAuth: true } },
      ],
    },
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAdmin: true },
      children: [
        { path: '', redirect: { name: 'admin-dashboard' } },
        { path: 'dashboard', name: 'admin-dashboard', component: () => import('../views/admin/DashboardView.vue'), meta: { title: '仪表盘' } },
        { path: 'books', name: 'admin-books', component: () => import('../views/admin/BooksManageView.vue'), meta: { title: '图书管理' } },
        { path: 'categories', name: 'admin-categories', component: () => import('../views/admin/CategoriesManageView.vue'), meta: { title: '分类管理' } },
        { path: 'borrows', name: 'admin-borrows', component: () => import('../views/admin/BorrowsManageView.vue'), meta: { title: '借阅管理' } },
        { path: 'users', name: 'admin-users', component: () => import('../views/admin/UsersManageView.vue'), meta: { title: '用户管理' } },
        { path: 'messages', name: 'admin-messages', component: () => import('../views/admin/MessagesManageView.vue'), meta: { title: '消息发布' } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.requiresAdmin && (!auth.isLoggedIn || !auth.isAdmin)) {
    return auth.isAdmin ? undefined : { name: 'home' }
  }
  if (to.meta.guestOnly && auth.isLoggedIn) {
    return { name: 'home' }
  }
  return undefined
})

export default router
