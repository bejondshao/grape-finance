import dayjs from 'dayjs'

export const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-'
  return `¥${Number(value).toFixed(2)}`
}

export const formatPercent = (value) => {
  if (value === null || value === undefined) return '-'
  return `${Number(value).toFixed(2)}%`
}

export const formatNumber = (value) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString()
}

export const formatDate = (date) => {
  if (!date) return '-'
  return dayjs(date).format('YYYY-MM-DD')
}

export const debounce = (func, wait) => {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
