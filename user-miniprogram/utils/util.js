/**
 * 工具函数
 */

// 格式化日期
const formatDate = (date, format = 'YYYY-MM-DD') => {
  if (typeof date === 'string') {
    date = new Date(date)
  }
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

// 格式化时间（去掉秒）
const formatTime = (time) => {
  if (!time) return ''
  return time.substring(0, 5)
}

// 获取星期几
const getWeekDay = (date) => {
  const days = ['日', '一', '二', '三', '四', '五', '六']
  if (typeof date === 'string') {
    date = new Date(date)
  }
  return '周' + days[date.getDay()]
}

// 获取一周的日期（以传入日期为起点）
const getWeekDates = (startDate) => {
  const result = []
  const date = new Date(startDate)

  // 获取本周的周一
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day  // 周日要往前推6天
  date.setDate(date.getDate() + diff)

  for (let i = 0; i < 7; i++) {
    const d = new Date(date)
    d.setDate(d.getDate() + i)
    const today = new Date()
    const isToday = d.toDateString() === today.toDateString()

    result.push({
      date: formatDate(d, 'YYYY-MM-DD'),
      day: String(d.getDate()).padStart(2, '0'),
      weekDay: isToday ? '今天' : getWeekDay(d),
      isToday
    })
  }

  return result
}

// 获取未来N天的日期列表
const getDateList = (days = 7) => {
  const result = []
  const today = new Date()

  for (let i = 0; i < days; i++) {
    const date = new Date(today)
    date.setDate(date.getDate() + i)
    result.push({
      date: formatDate(date, 'YYYY-MM-DD'),
      day: String(date.getDate()).padStart(2, '0'),
      weekDay: i === 0 ? '今天' : (i === 1 ? '明天' : getWeekDay(date)),
      isToday: i === 0
    })
  }

  return result
}

// 生成时间段列表
const getTimeSlots = (startHour = 8, endHour = 22) => {
  const slots = []
  for (let hour = startHour; hour < endHour; hour++) {
    slots.push({
      time: `${String(hour).padStart(2, '0')}:00`,
      label: `${String(hour).padStart(2, '0')}:00 - ${String(hour + 1).padStart(2, '0')}:00`
    })
  }
  return slots
}

// 预约状态
const getReservationStatus = (status) => {
  const statusMap = {
    'pending': { text: '待确认', class: 'status-pending', color: '#ff976a' },
    'confirmed': { text: '已确认', class: 'status-confirmed', color: '#1890ff' },
    'in_progress': { text: '进行中', class: 'status-progress', color: '#07c160' },
    'completed': { text: '已完成', class: 'status-completed', color: '#999' },
    'cancelled': { text: '已取消', class: 'status-cancelled', color: '#ee0a24' }
  }
  return statusMap[status] || { text: status, class: '', color: '#999' }
}

// 订单状态
const getOrderStatus = (status) => {
  const statusMap = {
    'pending': { text: '待支付', class: 'status-pending' },
    'paid': { text: '已支付', class: 'status-paid' },
    'processing': { text: '处理中', class: 'status-processing' },
    'completed': { text: '已完成', class: 'status-completed' },
    'cancelled': { text: '已取消', class: 'status-cancelled' },
    'refunded': { text: '已退款', class: 'status-refunded' }
  }
  return statusMap[status] || { text: status, class: '' }
}

// 格式化金额
const formatPrice = (price) => {
  if (price === undefined || price === null) return '0'
  return Number(price).toFixed(2)
}

// 格式化距离
const formatDistance = (meters) => {
  if (meters < 1000) {
    return `${meters}m`
  }
  return `${(meters / 1000).toFixed(1)}km`
}

// 计算两点距离
const getDistance = (lat1, lng1, lat2, lng2) => {
  const rad = Math.PI / 180
  const R = 6371000 // 地球半径（米）
  const dLat = (lat2 - lat1) * rad
  const dLng = (lng2 - lng1) * rad
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * rad) * Math.cos(lat2 * rad) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return Math.round(R * c)
}

// 防抖
const debounce = (fn, delay = 300) => {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 节流
const throttle = (fn, delay = 300) => {
  let last = 0
  return function (...args) {
    const now = Date.now()
    if (now - last > delay) {
      last = now
      fn.apply(this, args)
    }
  }
}

// 格式化手机号（隐藏中间4位）
const formatPhone = (phone) => {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

// 格式化会员等级类型
const getMemberLevelType = (type) => {
  const typeMap = {
    'normal': { text: '普通会员', color: '#909399', icon: 'icon-member' },
    'fitness': { text: '健身会员', color: '#67C23A', icon: 'icon-fitness' },
    'ball': { text: '球类会员', color: '#409EFF', icon: 'icon-ball' },
    'vip': { text: '顶级会员', color: '#E6A23C', icon: 'icon-vip' }
  }
  return typeMap[type] || { text: type, color: '#909399', icon: 'icon-member' }
}

// 格式化有效期天数
const formatDuration = (days) => {
  if (!days) return '-'
  if (days >= 365) {
    const years = Math.floor(days / 365)
    return `${years}年`
  } else if (days >= 30) {
    const months = Math.floor(days / 30)
    return `${months}个月`
  } else {
    return `${days}天`
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + 'KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(2) + 'MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(2) + 'GB'
}

// 格式化数字（千分位）
const formatNumber = (num) => {
  if (num === undefined || num === null) return '0'
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 校验手机号
const isValidPhone = (phone) => {
  return /^1[3-9]\d{9}$/.test(phone)
}

// 校验身份证号
const isValidIdCard = (idCard) => {
  return /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/.test(idCard)
}

// 深拷贝
const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj)
  if (obj instanceof Array) return obj.map(item => deepClone(item))
  const cloned = {}
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key])
    }
  }
  return cloned
}

// 生成UUID
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0
    const v = c === 'x' ? r : (r & 0x3 | 0x8)
    return v.toString(16)
  })
}

// 延迟执行
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

// 计算倒计时
const getCountdown = (endTime) => {
  const now = new Date().getTime()
  const end = new Date(endTime).getTime()
  const diff = end - now

  if (diff <= 0) {
    return { expired: true, days: 0, hours: 0, minutes: 0, seconds: 0 }
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  const seconds = Math.floor((diff % (1000 * 60)) / 1000)

  return { expired: false, days, hours, minutes, seconds }
}

// 相对时间（多久前）
const getRelativeTime = (datetime) => {
  const now = new Date().getTime()
  const time = new Date(datetime).getTime()
  const diff = now - time

  if (diff < 0) return '刚刚'

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const month = 30 * day
  const year = 365 * day

  if (diff < minute) return '刚刚'
  if (diff < hour) return Math.floor(diff / minute) + '分钟前'
  if (diff < day) return Math.floor(diff / hour) + '小时前'
  if (diff < month) return Math.floor(diff / day) + '天前'
  if (diff < year) return Math.floor(diff / month) + '个月前'
  return Math.floor(diff / year) + '年前'
}

// rpx转px
const rpxToPx = (rpx) => {
  const systemInfo = wx.getSystemInfoSync()
  return rpx * (systemInfo.windowWidth / 750)
}

// px转rpx
const pxToRpx = (px) => {
  const systemInfo = wx.getSystemInfoSync()
  return px * (750 / systemInfo.windowWidth)
}

module.exports = {
  formatDate,
  formatTime,
  getWeekDay,
  getWeekDates,
  getDateList,
  getTimeSlots,
  getReservationStatus,
  getOrderStatus,
  formatPrice,
  formatDistance,
  getDistance,
  debounce,
  throttle,
  formatPhone,
  getMemberLevelType,
  formatDuration,
  formatFileSize,
  formatNumber,
  isValidPhone,
  isValidIdCard,
  deepClone,
  generateUUID,
  sleep,
  getCountdown,
  getRelativeTime,
  rpxToPx,
  pxToRpx
}
