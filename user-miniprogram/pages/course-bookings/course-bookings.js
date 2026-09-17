const app = getApp()
const api = require('../../utils/api')

const TABS = [
  { key: '', label: '全部' },
  { key: 'confirmed', label: '待使用' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
]

const STATUS_STYLE = {
  pending:   { text: '待支付', color: '#E6A23C' },
  confirmed: { text: '待使用', color: '#1A5D3A' },
  completed: { text: '已完成', color: '#909399' },
  cancelled: { text: '已取消', color: '#F56C6C' },
}

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

function weekdayOf(dateStr) {
  const dt = new Date((dateStr || '').replace(/-/g, '/'))
  return isNaN(dt.getTime()) ? '' : WEEKDAYS[dt.getDay()]
}

// 开课前可取消（已核销不可取消）
function computeCanCancel(item) {
  if (item.status !== 'confirmed' || item.is_verified) return false
  if (!item.session_date || !item.start_time) return false
  const start = new Date(`${item.session_date.replace(/-/g, '/')} ${item.start_time}`)
  return start.getTime() > Date.now()
}

Page({
  data: {
    tabs: TABS,
    activeTab: '',
    bookings: [],
    page: 1,
    pageSize: 10,
    total: 0,
    loading: false,
    loaded: false,
    // 详情弹层
    showDetail: false,
    detail: null,
    detailLoading: false,
  },

  onLoad() {
    this.loadBookings(true)
  },

  onShow() {
    // 从详情/支付页返回时刷新（待支付可能已变 confirmed）
    if (this.data.loaded) this.loadBookings(true)
  },

  onPullDownRefresh() {
    this.loadBookings(true).finally(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    const { page, pageSize, total, loading } = this.data
    if (loading || page * pageSize >= total) return
    this.loadBookings(false)
  },

  onTabChange(e) {
    const key = e.currentTarget.dataset.key
    if (key === this.data.activeTab) return
    this.setData({ activeTab: key })
    this.loadBookings(true)
  },

  async loadBookings(reset) {
    if (this.data.loading) return
    const page = reset ? 1 : this.data.page + 1
    this.setData({ loading: true })
    try {
      const params = { page, page_size: this.data.pageSize }
      if (this.data.activeTab) params.status = this.data.activeTab
      const res = await api.getCourseBookings(params)
      const body = res.data || {}
      const items = (body.items || []).map(item => ({
        ...item,
        cover_image: app.resolveImageUrl(item.cover_image),
        status_text_display: (STATUS_STYLE[item.status] || {}).text || item.status_text,
        status_color: (STATUS_STYLE[item.status] || {}).color || '#666',
        weekday: weekdayOf(item.session_date),
        can_cancel: computeCanCancel(item),
        coach_initial: (item.coach_name || '教').charAt(0),
      }))
      this.setData({
        bookings: reset ? items : this.data.bookings.concat(items),
        page,
        total: body.total || 0,
        loaded: true,
      })
    } catch (err) {
      console.error('加载约课列表失败:', err)
      this.setData({ loaded: true })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 打开详情弹层
  async openDetail(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ showDetail: true, detail: null, detailLoading: true })
    try {
      const res = await api.getCourseBookingDetail(id)
      const d = res.data
      this.setData({
        detail: {
          ...d,
          status_text_display: (STATUS_STYLE[d.status] || {}).text || d.status_text,
          status_color: (STATUS_STYLE[d.status] || {}).color || '#666',
          weekday: weekdayOf(d.session_date),
          can_cancel: computeCanCancel(d),
        },
      })
    } catch (err) {
      console.error('加载约课详情失败:', err)
      wx.showToast({ title: err.message || '加载失败', icon: 'none' })
      this.setData({ showDetail: false })
    } finally {
      this.setData({ detailLoading: false })
    }
  },

  closeDetail() {
    this.setData({ showDetail: false, detail: null })
  },

  noop() {},

  // 复制约课编号（员工核销用）
  copyBookingNo() {
    if (!this.data.detail) return
    wx.setClipboardData({ data: this.data.detail.booking_no })
  },

  // 取消约课
  handleCancel(e) {
    const id = e.currentTarget.dataset.id
    const payType = e.currentTarget.dataset.payType
    const refundTip = payType === 'coin'
      ? '金币将自动退回余额'
      : '将自动原路退款（1-3 个工作日到账）'
    wx.showModal({
      title: '取消预约',
      content: `确定取消该课程预约吗？${refundTip}。`,
      confirmText: '确定取消',
      confirmColor: '#F56C6C',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.cancelCourseBooking(id)
          wx.showToast({ title: '已取消', icon: 'success' })
          this.closeDetail()
          this.loadBookings(true)
        } catch (err) {
          wx.showToast({ title: err.message || '取消失败', icon: 'none' })
        }
      },
    })
  },

  // 待支付 → 重新拉起微信支付
  async handleRepay(e) {
    const id = e.currentTarget.dataset.id
    try {
      const res = await api.repayCourseBooking(id)
      const data = res.data || {}
      if (!data.pay_params) {
        wx.showToast({ title: '无法拉起支付', icon: 'none' })
        return
      }
      wx.requestPayment({
        ...data.pay_params,
        success: () => {
          wx.showLoading({ title: '支付确认中...' })
          this.pollPayStatus(id, 0)
        },
        fail: (err) => {
          if (err.errMsg && err.errMsg.includes('cancel')) {
            wx.showToast({ title: '已取消支付', icon: 'none' })
          } else {
            wx.showToast({ title: '支付失败', icon: 'none' })
          }
        },
      })
    } catch (err) {
      wx.showToast({ title: err.message || '支付失败', icon: 'none' })
    }
  },

  async pollPayStatus(bookingId, attempt) {
    if (attempt >= 10) {
      wx.hideLoading()
      wx.showToast({ title: '支付处理中，请稍后查看', icon: 'none' })
      this.loadBookings(true)
      return
    }
    try {
      const res = await api.getCourseBookingPayStatus(bookingId)
      if (res.data && res.data.status === 'confirmed') {
        wx.hideLoading()
        wx.showToast({ title: '支付成功', icon: 'success' })
        this.loadBookings(true)
        return
      }
    } catch (err) {
      console.error('查询支付状态失败:', err)
    }
    setTimeout(() => this.pollPayStatus(bookingId, attempt + 1), 1000)
  },
})
