import { defineStore } from 'pinia'
import axios from 'axios'
import type { TokenPair, User } from '../types'
import { messagesApi } from '../api'

const TOKEN_KEY = 'library.accessToken'
const REFRESH_KEY = 'library.refreshToken'
const USER_KEY = 'library.user'

function readJSON<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem(TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_KEY) || '',
    user: readJSON<User>(USER_KEY),
    unreadCount: 0,
  }),
  getters: {
    isLoggedIn: (s) => !!s.accessToken,
    isAdmin: (s) => s.user?.role === 'admin',
  },
  actions: {
    setSession(payload: TokenPair) {
      this.accessToken = payload.accessToken
      this.refreshToken = payload.refreshToken
      this.user = payload.user
      localStorage.setItem(TOKEN_KEY, payload.accessToken)
      localStorage.setItem(REFRESH_KEY, payload.refreshToken)
      localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
    },
    setUser(user: User) {
      this.user = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    /** 用 RefreshToken 换新的双 Token（供 axios 拦截器调用） */
    async refresh(): Promise<string> {
      if (!this.refreshToken) throw new Error('无刷新凭证')
      // 直接用原生 axios，避免触发拦截器死循环
      const { data } = await axios.post<TokenPair>('/api/auth/refresh', {
        refreshToken: this.refreshToken,
      })
      this.setSession(data)
      return data.accessToken
    },
    logout() {
      this.accessToken = ''
      this.refreshToken = ''
      this.user = null
      this.unreadCount = 0
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
      localStorage.removeItem(USER_KEY)
    },
    async fetchUnread() {
      if (!this.isLoggedIn) {
        this.unreadCount = 0
        return
      }
      try {
        const { data } = await messagesApi.unreadCount()
        this.unreadCount = data.unreadCount
      } catch {
        /* 静默失败，不打扰用户 */
      }
    },
  },
})
