const app = getApp()
const api = require('../../utils/api')

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

// 「2026-01-24」→「周六 01-24」（今天/明天特殊处理）
function formatSessionDate(dateStr) {
  if (!dateStr) return ''
  const dt = new Date(dateStr.replace(/-/g, '/'))
  if (isNaN(dt.getTime())) return dateStr
  const now = new Date()
  const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const targetStart = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate()).getTime()
  const diffDays = Math.round((targetStart - dayStart) / 86400000)
  if (diffDays === 0) return '今天'
  if (diffDays === 1) return '明天'
  return `${WEEKDAYS[dt.getDay()]} ${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

Page({
  data: {
    courseId: null,
    course: null,
    sessions: [],
    loading: true,
    selectedSessionId: null,
    coinBalance: 0,
    // 支付弹层
    showPayModal: false,
    selectedPayType: 'coin',
    submitting: false,
  },

  onLoad(options) {
    if (!options || !options.id) {
      wx.showToast({ title: '课程参数错误', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }
    this.setData({ courseId: Number(options.id) })
    this.loadDetail()
  },

  onShow() {
    this.loadCoinBalance()
  },

  async loadDetail() {
    this.setData({ loading: true })
    try {
      const res = await api.getCourseDetail(this.data.courseId)
      const course = res.data
      // WXML 不支持方法调用，头像兜底首字符在 JS 预计算
      course.coach_initial = course.coach && course.coach.name ? course.coach.name.charAt(0) : '教'
      const sessions = (course.sessions || []).map(s => ({
        ...s,
        date_text: formatSessionDate(s.session_date),
      }))
      this.setData({ course, sessions })
    } catch (err) {
      console.error('加载课程详情失败:', err)
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  async loadCoinBalance() {
    try {
      const res = await app.request({ url: '/member/profile' })
      if (res.data) {
        this.setData({ coinBalance: parseFloat(res.data.coin_balance || 0) })
      }
    } catch (err) {
      console.error('加载余额失败:', err)
    }
  },

  // 选择课次（已约满/已开始的不可选）
  selectSession(e) {
    const { id, bookable } = e.currentTarget.dataset
    if (!bookable) return
    this.setData({
      selectedSessionId: id === this.data.selectedSessionId ? null : id,
    })
  },

  getSelectedSession() {
    return this.data.sessions.find(s => s.id === this.data.selectedSessionId) || null
  },

  // 打开支付弹层
  openPayModal() {
    if (!this.data.selectedSessionId) {
      wx.showToast({ title: '请先选择课次', icon: 'none' })
      return
    }
    this.setData({ showPayModal: true, selectedPayType: 'coin' })
  },

  closePayModal() {
    this.setData({ showPayModal: false })
  },

  noop() {},

  selectPayType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ selectedPayType: this.data.selectedPayType === type ? '' : type })
  },

  // 确认支付 → 提交报名
  async confirmPay() {
    const { selectedPayType, selectedSessionId, submitting, course, coinBalance } = this.data
    if (submitting) return
    if (!selectedPayType) {
      wx.showToast({ title: '请选择支付方式', icon: 'none' })
      return
    }
    if (selectedPayType === 'coin' && course && coinBalance < course.price) {
      wx.showToast({ title: '金币余额不足', icon: 'none' })
      return
    }

    this.setData({ submitting: true, showPayModal: false })
    try {
      const res = await api.createCourseBooking({
        session_id: selectedSessionId,
        pay_type: selectedPayType,
      })
      const data = res.data || {}

      // 微信支付：拉起支付
      if (data.pay_params) {
        this.handleWechatPay(data)
        return
      }

      // 金币支付：直接成功
      wx.showToast({ title: '预约成功', icon: 'success' })
      this.onBookingSuccess()
    } catch (err) {
      console.error('报名失败:', err)
      wx.showToast({ title: err.message || '报名失败', icon: 'none' })
      this.setData({ submitting: false })
    }
  },

  // 处理微信支付
  handleWechatPay(data) {
    const { booking_id, pay_params } = data
    wx.requestPayment({
      ...pay_params,
      success: () => {
        wx.showLoading({ title: '支付确认中...' })
        this.pollPayStatus(booking_id, 0)
      },
      fail: (err) => {
        this.setData({ submitting: false })
        if (err.errMsg && err.errMsg.includes('cancel')) {
          wx.showToast({ title: '已取消支付，可在「我的预约」中继续支付', icon: 'none' })
        } else {
          wx.showToast({ title: '支付失败', icon: 'none' })
        }
      },
    })
  },

  // 轮询支付状态（confirmed = 支付成功）
  async pollPayStatus(bookingId, attempt) {
    if (attempt >= 10) {
      wx.hideLoading()
      this.setData({ submitting: false })
      wx.showToast({ title: '支付处理中，请稍后到「我的预约」查看', icon: 'none' })
      this.onBookingSuccess()
      return
    }
    try {
      const res = await api.getCourseBookingPayStatus(bookingId)
      if (res.data && res.data.status === 'confirmed') {
        wx.hideLoading()
        this.setData({ submitting: false })
        wx.showToast({ title: '预约成功', icon: 'success' })
        this.onBookingSuccess()
        return
      }
    } catch (err) {
      console.error('查询支付状态失败:', err)
    }
    setTimeout(() => this.pollPayStatus(bookingId, attempt + 1), 1000)
  },

  // 报名成功后：刷新课次余量并跳我的预约
  onBookingSuccess() {
    this.setData({ submitting: false, selectedSessionId: null })
    this.loadDetail()
    setTimeout(() => {
      wx.redirectTo({ url: '/pages/course-bookings/course-bookings' })
    }, 1200)
  },
})
