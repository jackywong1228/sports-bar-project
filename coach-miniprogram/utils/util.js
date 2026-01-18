/**
 * 格式化日期
 * @param {Date} date 日期对象
 * @param {string} format 格式化模板
 * @returns {string}
 */
const formatDate = (date, format = 'YYYY-MM-DD') => {
  if (!date) return ''
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

/**
 * 格式化时间（小时:分钟）
 * @param {string} time 时间字符串
 * @returns {string}
 */
const formatTime = (time) => {
  if (!time) return ''
  return time.substring(0, 5)
}

/**
 * 获取星期几
 * @param {Date} date 日期对象
 * @returns {string}
 */
const getWeekDay = (date) => {
  const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return weekDays[date.getDay()]
}

/**
 * 获取日期数组（一周）
 * @param {Date} startDate 起始日期
 * @returns {Array}
 */
const getWeekDates = (startDate = new Date()) => {
  const dates = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(startDate)
    date.setDate(startDate.getDate() + i)
    dates.push({
      date: formatDate(date, 'YYYY-MM-DD'),
      day: date.getDate(),
      weekDay: getWeekDay(date),
      isToday: formatDate(new Date(), 'YYYY-MM-DD') === formatDate(date, 'YYYY-MM-DD')
    })
  }
  return dates
}

/**
 * 生成时间段列表（小时制）
 * @param {number} startHour 开始时间
 * @param {number} endHour 结束时间
 * @returns {Array}
 */
const generateTimeSlots = (startHour = 8, endHour = 22) => {
  const slots = []
  for (let hour = startHour; hour < endHour; hour++) {
    slots.push({
      start: `${String(hour).padStart(2, '0')}:00`,
      end: `${String(hour + 1).padStart(2, '0')}:00`,
      label: `${String(hour).padStart(2, '0')}:00 - ${String(hour + 1).padStart(2, '0')}:00`
    })
  }
  return slots
}

/**
 * 获取预约状态文本
 * @param {string} status 状态码
 * @returns {object}
 */
const getReservationStatus = (status) => {
  const statusMap = {
    'pending': { text: '待确认', class: 'status-pending' },
    'confirmed': { text: '已确认', class: 'status-confirmed' },
    'in_progress': { text: '进行中', class: 'status-confirmed' },
    'completed': { text: '已完成', class: 'status-completed' },
    'cancelled': { text: '已取消', class: 'status-cancelled' }
  }
  return statusMap[status] || { text: '未知', class: '' }
}

/**
 * 格式化金币/积分数量
 * @param {number} amount 数量
 * @returns {string}
 */
const formatAmount = (amount) => {
  if (amount === null || amount === undefined) return '0'
  return Number(amount).toFixed(0)
}

/**
 * 防抖函数
 * @param {Function} fn 函数
 * @param {number} delay 延迟时间
 * @returns {Function}
 */
const debounce = (fn, delay = 300) => {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

/**
 * 节流函数
 * @param {Function} fn 函数
 * @param {number} delay 延迟时间
 * @returns {Function}
 */
const throttle = (fn, delay = 300) => {
  let lastTime = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastTime >= delay) {
      fn.apply(this, args)
      lastTime = now
    }
  }
}

/**
 * 格式化金额（带小数）
 * @param {number} price 金额
 * @returns {string}
 */
const formatPrice = (price) => {
  if (price === undefined || price === null) return '0.00'
  return Number(price).toFixed(2)
}

/**
 * 格式化手机号（隐藏中间4位）
 * @param {string} phone 手机号
 * @returns {string}
 */
const formatPhone = (phone) => {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 格式化有效期天数
 * @param {number} days 天数
 * @returns {string}
 */
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

/**
 * 获取相对时间（多久前）
 * @param {string} datetime 时间字符串
 * @returns {string}
 */
const getRelativeTime = (datetime) => {
  const now = new Date().getTime()
  const time = new Date(datetime).getTime()
  const diff = now - time

  if (diff < 0) return '刚刚'

  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  const month = 30 * day

  if (diff < minute) return '刚刚'
  if (diff < hour) return Math.floor(diff / minute) + '分钟前'
  if (diff < day) return Math.floor(diff / hour) + '小时前'
  if (diff < month) return Math.floor(diff / day) + '天前'
  return Math.floor(diff / month) + '个月前'
}

/**
 * 获取订单状态
 * @param {string} status 状态码
 * @returns {object}
 */
const getOrderStatus = (status) => {
  const statusMap = {
    'pending': { text: '待支付', class: 'status-pending', color: '#ff976a' },
    'paid': { text: '已支付', class: 'status-paid', color: '#07c160' },
    'processing': { text: '处理中', class: 'status-processing', color: '#1890ff' },
    'completed': { text: '已完成', class: 'status-completed', color: '#999' },
    'cancelled': { text: '已取消', class: 'status-cancelled', color: '#999' },
    'refunded': { text: '已退款', class: 'status-refunded', color: '#ee0a24' }
  }
  return statusMap[status] || { text: '未知', class: '', color: '#999' }
}

/**
 * 获取结算状态
 * @param {string} status 状态码
 * @returns {object}
 */
const getSettlementStatus = (status) => {
  const statusMap = {
    'pending': { text: '待结算', class: 'status-pending', color: '#ff976a' },
    'settled': { text: '已结算', class: 'status-settled', color: '#07c160' },
    'withdrawn': { text: '已提现', class: 'status-withdrawn', color: '#1890ff' }
  }
  return statusMap[status] || { text: '未知', class: '', color: '#999' }
}

/**
 * 深拷贝
 * @param {any} obj 对象
 * @returns {any}
 */
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

/**
 * 延迟执行
 * @param {number} ms 毫秒数
 * @returns {Promise}
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * rpx转px
 * @param {number} rpx rpx值
 * @returns {number}
 */
const rpxToPx = (rpx) => {
  const systemInfo = wx.getSystemInfoSync()
  return rpx * (systemInfo.windowWidth / 750)
}

/**
 * 格式化数字（千分位）
 * @param {number} num 数字
 * @returns {string}
 */
const formatNumber = (num) => {
  if (num === undefined || num === null) return '0'
  return String(num).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

module.exports = {
  formatDate,
  formatTime,
  getWeekDay,
  getWeekDates,
  generateTimeSlots,
  getReservationStatus,
  formatAmount,
  debounce,
  throttle,
  formatPrice,
  formatPhone,
  formatDuration,
  getRelativeTime,
  getOrderStatus,
  getSettlementStatus,
  deepClone,
  sleep,
  rpxToPx,
  formatNumber
}
