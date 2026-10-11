import axios from 'axios'
import { useAuthStore } from '../stores/auth'

export const http = axios.create({
  baseURL: '/api',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

const AUTH_PATHS = ['/auth/login', '/auth/register', '/auth/refresh']
let refreshing: Promise<string> | null = null

/**
 * AccessToken 过期自动续期：
 * 拦截 401，用 RefreshToken 换新的双 Token 后重放原请求；
 * 续期失败（RefreshToken 也过期）则登出并跳转登录页。
 */
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config
    const status = error.response?.status
    const isAuthApi = AUTH_PATHS.some((p) => config?.url?.includes(p))
    if (status === 401 && config && !config._retried && !isAuthApi) {
      config._retried = true
      const auth = useAuthStore()
      try {
        refreshing = refreshing ?? auth.refresh().finally(() => (refreshing = null))
        const token = await refreshing
        config.headers.Authorization = `Bearer ${token}`
        return http(config)
      } catch {
        auth.logout()
        const redirect = encodeURIComponent(
          window.location.pathname + window.location.search,
        )
        window.location.href = `/login?redirect=${redirect}`
      }
    }
    return Promise.reject(error)
  },
)

/** 从后端错误中提取可读信息 */
export function apiError(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const detail = e.response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0]
      if (first?.msg) {
        const field = first.loc?.slice(-1)[0] ?? ''
        return `参数「${field}」校验失败：${first.msg}`
      }
    }
    if (e.response?.status === 401) return '请先登录'
    if (e.response?.status === 403) return '没有权限执行此操作'
    return '网络异常，请稍后重试'
  }
  return String(e)
}
