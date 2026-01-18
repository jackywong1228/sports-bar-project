/**
 * API接口定义（教练端）
 * 统一管理所有后端接口
 */

const { get, post, put, del, upload } = require('./request')

// ==================== 教练认证 ====================

/**
 * 微信登录
 * @param {string} code wx.login获取的code
 */
const wxLogin = (code, userInfo = {}) => {
  return post('/coach/auth/wx-login', { code, ...userInfo })
}

/**
 * 手机号登录（开发测试用）
 * @param {string} phone 手机号
 */
const loginByPhone = (phone) => {
  return post('/coach/auth/login', { phone })
}

/**
 * 获取手机号
 * @param {string} code getPhoneNumber事件获取的code
 */
const getPhoneNumber = (code) => {
  return post('/coach/auth/phone', { code })
}

/**
 * 获取当前教练信息
 */
const getCoachProfile = () => {
  return get('/coach/profile')
}

/**
 * 更新教练信息
 */
const updateCoachProfile = (data) => {
  return put('/coach/profile', data)
}

// ==================== 首页数据 ====================

/**
 * 获取首页统计数据
 */
const getDashboard = () => {
  return get('/coach/dashboard')
}

/**
 * 获取今日预约列表
 */
const getTodayReservations = () => {
  return get('/coach/reservations/today')
}

// ==================== 排期管理 ====================

/**
 * 获取排期列表
 * @param {string} date 日期 YYYY-MM-DD
 */
const getSchedule = (date) => {
  return get('/coach/schedule', { date })
}

/**
 * 批量设置排期
 * @param {Object} data 排期数据
 */
const setSchedule = (data) => {
  return post('/coach/schedule', data, { showLoading: true })
}

/**
 * 更新单个时段
 */
const updateTimeSlot = (slotId, data) => {
  return put(`/coach/schedule/${slotId}`, data)
}

/**
 * 删除时段
 */
const deleteTimeSlot = (slotId) => {
  return del(`/coach/schedule/${slotId}`)
}

/**
 * 获取周排期
 * @param {string} startDate 开始日期
 */
const getWeekSchedule = (startDate) => {
  return get('/coach/schedule/week', { start_date: startDate })
}

/**
 * 复制排期到其他日期
 */
const copySchedule = (fromDate, toDates) => {
  return post('/coach/schedule/copy', { from_date: fromDate, to_dates: toDates }, { showLoading: true })
}

// ==================== 预约管理 ====================

/**
 * 获取预约列表
 */
const getReservations = (params = {}) => {
  return get('/coach/reservations', params)
}

/**
 * 获取预约详情
 */
const getReservationDetail = (id) => {
  return get(`/coach/reservations/${id}`)
}

/**
 * 确认预约
 */
const confirmReservation = (id) => {
  return post(`/coach/reservations/${id}/confirm`, {}, { showLoading: true })
}

/**
 * 拒绝预约
 */
const rejectReservation = (id, reason = '') => {
  return post(`/coach/reservations/${id}/reject`, { reason }, { showLoading: true })
}

/**
 * 开始课程
 */
const startReservation = (id) => {
  return post(`/coach/reservations/${id}/start`, {}, { showLoading: true })
}

/**
 * 完成课程
 */
const completeReservation = (id) => {
  return post(`/coach/reservations/${id}/complete`, {}, { showLoading: true })
}

// ==================== 收入管理 ====================

/**
 * 获取收入概览
 */
const getIncomeOverview = () => {
  return get('/coach/income/overview')
}

/**
 * 获取收入明细
 */
const getIncomeRecords = (params = {}) => {
  return get('/coach/income/records', params)
}

/**
 * 获取月度收入统计
 */
const getMonthlyIncome = (year, month) => {
  return get('/coach/income/monthly', { year, month })
}

// ==================== 钱包管理 ====================

/**
 * 获取钱包信息
 */
const getWallet = () => {
  return get('/coach/wallet')
}

/**
 * 获取提现记录
 */
const getWithdrawRecords = (params = {}) => {
  return get('/coach/wallet/withdraws', params)
}

/**
 * 发起提现
 */
const createWithdraw = (amount) => {
  return post('/coach/wallet/withdraw', { amount }, { showLoading: true })
}

/**
 * 获取结算记录
 */
const getSettlementRecords = (params = {}) => {
  return get('/coach/wallet/settlements', params)
}

// ==================== 教练码 ====================

/**
 * 获取教练码
 */
const getCoachCode = () => {
  return get('/coach/code')
}

/**
 * 刷新教练码
 */
const refreshCoachCode = () => {
  return post('/coach/code/refresh', {}, { showLoading: true })
}

// ==================== 推广管理 ====================

/**
 * 获取推广统计
 */
const getPromoteStats = () => {
  return get('/coach/promote/stats')
}

/**
 * 获取推广二维码
 */
const getPromoteQRCode = () => {
  return get('/coach/promote/qrcode')
}

/**
 * 获取推广记录
 */
const getPromoteRecords = (params = {}) => {
  return get('/coach/promote/records', params)
}

/**
 * 获取我推广的会员
 */
const getPromotedMembers = (params = {}) => {
  return get('/coach/promote/members', params)
}

// ==================== 订单管理 ====================

/**
 * 获取订单列表
 */
const getOrders = (params = {}) => {
  return get('/coach/orders', params)
}

/**
 * 获取订单详情
 */
const getOrderDetail = (id) => {
  return get(`/coach/orders/${id}`)
}

// ==================== 消息通知 ====================

/**
 * 获取消息列表
 */
const getMessages = (params = {}) => {
  return get('/coach/messages', params)
}

/**
 * 标记消息已读
 */
const markMessageRead = (id) => {
  return post(`/coach/messages/${id}/read`)
}

/**
 * 标记全部已读
 */
const markAllMessagesRead = () => {
  return post('/coach/messages/read-all')
}

/**
 * 获取未读消息数
 */
const getUnreadCount = () => {
  return get('/coach/messages/unread-count')
}

// ==================== 文件上传 ====================

/**
 * 上传图片
 */
const uploadImage = (filePath) => {
  return upload('/upload/image', filePath, 'file')
}

module.exports = {
  // 认证
  wxLogin,
  loginByPhone,
  getPhoneNumber,
  getCoachProfile,
  updateCoachProfile,

  // 首页
  getDashboard,
  getTodayReservations,

  // 排期
  getSchedule,
  setSchedule,
  updateTimeSlot,
  deleteTimeSlot,
  getWeekSchedule,
  copySchedule,

  // 预约
  getReservations,
  getReservationDetail,
  confirmReservation,
  rejectReservation,
  startReservation,
  completeReservation,

  // 收入
  getIncomeOverview,
  getIncomeRecords,
  getMonthlyIncome,

  // 钱包
  getWallet,
  getWithdrawRecords,
  createWithdraw,
  getSettlementRecords,

  // 教练码
  getCoachCode,
  refreshCoachCode,

  // 推广
  getPromoteStats,
  getPromoteQRCode,
  getPromoteRecords,
  getPromotedMembers,

  // 订单
  getOrders,
  getOrderDetail,

  // 消息
  getMessages,
  markMessageRead,
  markAllMessagesRead,
  getUnreadCount,

  // 上传
  uploadImage
}
