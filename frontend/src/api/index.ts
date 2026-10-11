import { http } from './client'
import type {
  Book,
  Borrow,
  Category,
  Message,
  Overview,
  Page,
  Review,
  TokenPair,
  TrendItem,
  User,
} from '../types'

export const authApi = {
  login: (data: { username: string; password: string }) =>
    http.post<TokenPair>('/auth/login', data),
  register: (data: { username: string; password: string; nickname?: string; email?: string; phone?: string }) =>
    http.post<TokenPair>('/auth/register', data),
  me: () => http.get<User>('/auth/me'),
}

export const profileApi = {
  update: (data: { nickname: string; email: string; phone: string }) =>
    http.put<User>('/profile', data),
  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<User>('/profile/avatar', form)
  },
}

export const usersApi = {
  list: (params: { keyword?: string; role?: string; page?: number; size?: number }) =>
    http.get<Page<User>>('/users', { params }),
  updateRole: (id: number, role: string) => http.put<User>(`/users/${id}/role`, { role }),
  updateStatus: (id: number, isActive: boolean) =>
    http.put<User>(`/users/${id}/status`, { isActive }),
  remove: (id: number) => http.delete(`/users/${id}`),
}

export const categoriesApi = {
  list: () => http.get<Category[]>('/categories'),
  create: (data: { name: string; description?: string }) => http.post<Category>('/categories', data),
  update: (id: number, data: { name: string; description?: string }) =>
    http.put<Category>(`/categories/${id}`, data),
  remove: (id: number) => http.delete(`/categories/${id}`),
}

export interface BookQuery {
  keyword?: string
  categoryId?: number | null
  status?: string
  tag?: string
  page?: number
  size?: number
}

export const booksApi = {
  list: (params: BookQuery) => http.get<Page<Book>>('/books', { params }),
  detail: (id: number) => http.get<Book>(`/books/${id}`),
  tags: () => http.get<string[]>('/books/tags'),
  create: (data: Record<string, unknown>) => http.post<Book>('/books', data),
  update: (id: number, data: Record<string, unknown>) => http.put<Book>(`/books/${id}`, data),
  remove: (id: number) => http.delete(`/books/${id}`),
  uploadCover: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return http.post<{ cover: string }>(`/books/${id}/cover`, form)
  },
}

export const reviewsApi = {
  list: (bookId: number, params: { page?: number; size?: number }) =>
    http.get<Page<Review>>(`/books/${bookId}/reviews`, { params }),
  create: (bookId: number, data: { rating: number; content: string }) =>
    http.post<Review>(`/books/${bookId}/reviews`, data),
  remove: (id: number) => http.delete(`/reviews/${id}`),
}

export const borrowsApi = {
  create: (bookId: number) => http.post<Borrow>('/borrows', { bookId }),
  my: (params: { status?: string; page?: number; size?: number }) =>
    http.get<Page<Borrow>>('/borrows/my', { params }),
  mySummary: () => http.get<{ borrowing: number; overdue: number; returned: number }>('/borrows/my/summary'),
  list: (params: { status?: string; keyword?: string; page?: number; size?: number }) =>
    http.get<Page<Borrow>>('/borrows', { params }),
  requestReturn: (id: number) => http.post<Borrow>(`/borrows/${id}/return`),
  confirmReturn: (id: number) => http.post<Borrow>(`/borrows/${id}/confirm-return`),
  remind: (id: number) => http.post<Borrow>(`/borrows/${id}/remind`),
}

export const messagesApi = {
  list: (params: { page?: number; size?: number }) =>
    http.get<Page<Message>>('/messages', { params }),
  unreadCount: () => http.get<{ unreadCount: number }>('/messages/unread-count'),
  markRead: (id: number) => http.post(`/messages/${id}/read`),
  markAllRead: () => http.post('/messages/read-all'),
  adminList: (params: { page?: number; size?: number }) =>
    http.get<Page<Message>>('/messages/admin/list', { params }),
  create: (data: { title: string; content: string; targetUserId?: number | null }) =>
    http.post<Message>('/messages', data),
  remove: (id: number) => http.delete(`/messages/${id}`),
}

export const statsApi = {
  overview: () => http.get<Overview>('/stats/overview'),
  borrowTrend: (granularity: 'day' | 'week' | 'month') =>
    http.get<{ granularity: string; span: number; items: TrendItem[] }>('/stats/borrow-trend', {
      params: { granularity },
    }),
}
