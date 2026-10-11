export function fmtDate(value?: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function fmtDateTime(value?: string | null): string {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '—'
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${fmtDate(value)} ${hh}:${mm}`
}

export const BORROW_STATUS_TEXT: Record<string, string> = {
  borrowed: '借阅中',
  returning: '归还待确认',
  returned: '已归还',
}

export const ROLE_TEXT: Record<string, string> = {
  admin: '管理员',
  user: '普通用户',
  vip: 'VIP 用户',
}
