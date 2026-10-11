export type Role = 'admin' | 'user' | 'vip'
export type BorrowStatus = 'borrowed' | 'returning' | 'returned'

export interface User {
  id: number
  username: string
  nickname: string
  email: string
  phone: string
  avatar: string | null
  role: Role
  isActive: boolean
  createdAt: string
}

export interface TokenPair {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
  user: User
}

export interface Category {
  id: number
  name: string
  description: string
  bookCount: number
  createdAt: string
}

export interface Book {
  id: number
  title: string
  author: string
  isbn: string
  publisher: string
  description: string
  categoryId: number | null
  categoryName: string | null
  cover: string | null
  tags: string[]
  totalCopies: number
  availableCopies: number
  ratingAvg: number
  ratingCount: number
  createdAt: string
}

export interface ReviewUser {
  id: number
  username: string
  nickname: string
  avatar: string | null
}

export interface Review {
  id: number
  bookId: number
  user: ReviewUser
  rating: number
  content: string
  createdAt: string
}

export interface BorrowUser {
  id: number
  username: string
  nickname: string
}

export interface BorrowBook {
  id: number
  title: string
  author: string
  cover: string | null
}

export interface Borrow {
  id: number
  userId: number
  user: BorrowUser
  bookId: number
  book: BorrowBook
  status: BorrowStatus
  overdue: boolean
  borrowedAt: string
  dueDate: string
  returnedAt: string | null
  remindedAt: string | null
}

export interface Message {
  id: number
  title: string
  content: string
  targetUserId: number | null
  targetUsername?: string | null
  isRead?: boolean
  createdAt: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
}

export interface Overview {
  totalBooks: number
  totalCopies: number
  availableCopies: number
  totalUsers: number
  totalReviews: number
  borrowing: number
  overdue: number
  totalMessages: number
}

export interface TrendItem {
  label: string
  count: number
}
