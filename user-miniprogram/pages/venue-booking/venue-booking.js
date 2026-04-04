const app = getApp()
const util = require('../../utils/util.js')
const api = require('../../utils/api.js')

// 场馆类型图标映射（英文key → 本地图片路径）
const SPORT_ICON_MAP = {
  tennis: '/assets/icons/sports/tennis.svg',
  pickleball: '/assets/icons/sports/pickleball.svg',
  squash: '/assets/icons/sports/squash.svg',
  golf: '/assets/icons/sports/golf.svg',
  'golf-vip': '/assets/icons/sports/golf.svg',
  golf_vip: '/assets/icons/sports/golf.svg',
  basketball: '/assets/icons/sports/basketball.svg',
  badminton: '/assets/icons/sports/badminton.svg',
}

Page({
  data: {
    venueTypes: [],
    currentTypeId: null,
    dates: [],
    selectedDate: '',
    calendarData: {
      venues: [],
      time_slots: []
    },
    selectedVenueId: null,
    selectedVenueName: '',
    selectedVenuePrice: 0,
    selectedSlots: [], // [{hour: 6}, {hour: 7}, ...]
    loading: true,
    submitting: false,
    calendarHeight: 800,
    scrollLeft: 0,
    // 会员权限相关（三级会员制）
    canBook: true,
    isMember: false,
    memberLevel: 'S',
    permissionReason: '',
    freeUsageInfo: null,  // SSS免费时长信息
    // 支付相关
    showPayModal: false,
    selectedPayType: 'coin',
    coinBalance: 0,
    estimatedPrice: 0,
    // 优惠券相关
    availableCoupons: [],
    selectedCouponIndex: -1,
    couponDiscount: 0,
    actualPrice: 0
  },

  onLoad(options) {
    // 计算日历高度（18个时间段 * 80rpx）
    const systemInfo = wx.getSystemInfoSync()
    const calendarHeight = systemInfo.windowHeight - 280 // 减去顶部高度
    this.setData({ calendarHeight })

    this.initDates()

    if (options.type_id) {
      // 直接传入 type_id（正常路径）
      this.loadVenueTypes(options.type_id).then(() => {
        this.checkMemberPermission()
      })
    } else if (options.id) {
      // 传入 venue_id（兼容旧路径）→ 先查场馆获取 type_id
      this.loadVenueTypeFromVenueId(options.id)
    } else {
      this.loadVenueTypes().then(() => {
        this.checkMemberPermission()
      })
    }
  },

  onShow() {
    if (this.data.currentTypeId) {
      this.loadCalendarData()
    }
    this.checkMemberPermission()
    this.loadCoinBalance()
  },

  // 加载金币余额
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

  // 检查会员预约权限（三级会员制）
  async checkMemberPermission() {
    const legacyMap = { GUEST: 'S', TRIAL: 'S', MEMBER: 'SS' }

    try {
      const res = await api.checkBookingPermission({
        venue_type_id: this.data.currentTypeId || 1,
        booking_date: this.data.selectedDate
      })
      if (res.code === 200) {
        const data = res.data || {}
        const levelCode = data.level_code || app.globalData.memberLevel || 'S'
        const mappedLevel = legacyMap[levelCode] || levelCode
        const isMember = (mappedLevel === 'SS' || mappedLevel === 'SSS')

        this.setData({
          canBook: data.can_book !== false,
          isMember: isMember,
          memberLevel: mappedLevel,
          permissionReason: data.reason || '',
          freeUsageInfo: data.free_usage_info || null
        })

        if (!data.can_book) {
          this.showBookingTip(mappedLevel, data.reason)
        }
      }
    } catch (err) {
      console.error('检查预约权限失败:', err)
      this.setData({
        canBook: app.checkCanBook(),
        isMember: app.globalData.isMember,
        memberLevel: app.globalData.memberLevel
      })
      if (!app.globalData.isMember) {
        this.showBookingTip(app.globalData.memberLevel, '')
      }
    }
  },

  // 显示预约权限提示（根据等级差异化）
  showBookingTip(level, reason) {
    let content = reason || ''
    if (level === 'S') {
      content = '当前为S级会员，无法预约场馆。\n开通SS会员可预约当天场馆，SSS会员可提前3天预约。'
    } else if (level === 'SS' && !content) {
      content = 'SS级会员仅可预约当天场馆。如需提前预约，请升级为SSS会员。'
    }

    wx.showModal({
      title: '预约提示',
      content: content,
      confirmText: '查看会员',
      cancelText: '知道了',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({ url: '/pages/member/member' })
        }
      }
    })
  },

  // 初始化日期列表（根据会员等级限制天数）
  initDates() {
    const dates = []
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const today = new Date()
    const level = app.globalData.memberLevel || 'S'

    // SS仅当天, SSS提前3天, 默认7天
    let maxDays = 7
    if (level === 'SS') maxDays = 1
    else if (level === 'SSS') maxDays = 4  // 今天 + 3天

    for (let i = 0; i < maxDays; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      dates.push({
        date: util.formatDate(date, 'YYYY-MM-DD'),
        day: date.getDate(),
        weekDay: i === 0 ? '今天' : weekDays[date.getDay()]
      })
    }

    this.setData({
      dates,
      selectedDate: dates[0].date
    })
  },

  // 通过 venue_id 查询其 type_id（兼容旧路径）
  async loadVenueTypeFromVenueId(venueId) {
    try {
      const res = await app.request({ url: `/member/venues/${venueId}` })
      const typeId = res.data && res.data.type_id ? res.data.type_id : null
      await this.loadVenueTypes(typeId)
      this.checkMemberPermission()
    } catch (err) {
      console.error('查询场馆类型失败:', err)
      await this.loadVenueTypes()
      this.checkMemberPermission()
    }
  },

  // 加载场馆类型
  async loadVenueTypes(defaultTypeId) {
    try {
      const res = await app.request({
        url: '/member/venue-types'
      })

      const types = (res.data || []).map(type => ({
        ...type,
        iconPath: SPORT_ICON_MAP[(type.icon || '').toLowerCase()] || SPORT_ICON_MAP.basketball
      }))
      if (types.length > 0) {
        const typeId = defaultTypeId ? parseInt(defaultTypeId) : types[0].id
        this.setData({
          venueTypes: types,
          currentTypeId: typeId
        })
        this.loadCalendarData()
      } else {
        this.setData({
          venueTypes: [],
          loading: false
        })
      }
    } catch (err) {
      console.error('加载场馆类型失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载日历数据
  async loadCalendarData() {
    this.setData({ loading: true })

    try {
      const res = await app.request({
        url: `/member/venue-calendar?type_id=${this.data.currentTypeId}&date=${this.data.selectedDate}`
      })

      this.setData({
        calendarData: res.data || { venues: [], time_slots: [] },
        loading: false
      })
    } catch (err) {
      console.error('加载日历数据失败:', err)
      this.setData({
        calendarData: { venues: [], time_slots: [] },
        loading: false
      })
    }
  },

  // 选择场馆类型
  selectType(e) {
    const typeId = e.currentTarget.dataset.id
    if (typeId === this.data.currentTypeId) return

    this.setData({
      currentTypeId: typeId,
      selectedSlots: [],
      selectedVenueId: null,
      selectedVenueName: '',
      selectedVenuePrice: 0
    })
    this.loadCalendarData()
  },

  // 选择日期
  selectDate(e) {
    const date = e.currentTarget.dataset.date
    if (date === this.data.selectedDate) return

    this.setData({
      selectedDate: date,
      selectedSlots: [],
      selectedVenueId: null,
      selectedVenueName: '',
      selectedVenuePrice: 0
    })
    this.loadCalendarData()
  },

  // 选择时间段
  selectSlot(e) {
    const { venueId, venueName, venuePrice, hour } = e.currentTarget.dataset

    // 找到对应场馆和时段的状态
    const venue = this.data.calendarData.venues.find(v => v.id === venueId)
    if (!venue) return

    const slot = venue.slots.find(s => s.hour === hour)
    if (slot.status === 'past') {
      wx.showToast({
        title: '该时段已过期',
        icon: 'none'
      })
      return
    }
    if (slot.status === 'reserved') {
      wx.showToast({
        title: '该时段已被预约',
        icon: 'none'
      })
      return
    }

    let { selectedSlots, selectedVenueId } = this.data

    // 如果选择了不同的场馆，清空已选时段
    if (selectedVenueId && selectedVenueId !== venueId) {
      selectedSlots = []
    }

    // 检查是否已选中
    const index = selectedSlots.findIndex(s => s.hour === hour)

    if (index > -1) {
      // 取消选中
      selectedSlots.splice(index, 1)
    } else {
      // 选中 - 检查是否连续
      if (selectedSlots.length > 0) {
        const hours = selectedSlots.map(s => s.hour).sort((a, b) => a - b)
        const minHour = hours[0]
        const maxHour = hours[hours.length - 1]

        // 只允许选择连续的时段
        if (hour !== minHour - 1 && hour !== maxHour + 1) {
          wx.showToast({
            title: '请选择连续的时段',
            icon: 'none'
          })
          return
        }
      }
      selectedSlots.push({ hour })
    }

    // 按时间排序
    selectedSlots.sort((a, b) => a.hour - b.hour)

    this.setData({
      selectedSlots,
      selectedVenueId: selectedSlots.length > 0 ? venueId : null,
      selectedVenueName: selectedSlots.length > 0 ? venueName : '',
      selectedVenuePrice: selectedSlots.length > 0 ? venuePrice : 0
    })
  },

  // 同步滚动
  onCalendarScroll(e) {
    this.setData({
      scrollLeft: e.detail.scrollLeft
    })
  },

  // 跳转会员中心
  goToMember() {
    wx.navigateTo({
      url: '/pages/member/member'
    })
  },

  // 提交预约 — 弹出支付选择
  submitBooking() {
    if (this.data.selectedSlots.length === 0) {
      wx.showToast({ title: '请选择时间段', icon: 'none' })
      return
    }

    if (!this.data.canBook) {
      this.showBookingTip(this.data.memberLevel, this.data.permissionReason)
      return
    }

    // 计算预估价格
    const estimatedPrice = this.data.selectedVenuePrice * this.data.selectedSlots.length

    // SSS免费时段（尚有剩余免费分钟数）或价格为0，直接提交
    const freeInfo = this.data.freeUsageInfo
    const isSSSFree = this.data.memberLevel === 'SSS' && freeInfo && freeInfo.remaining_free_minutes > 0
    if (estimatedPrice <= 0 || isSSSFree) {
      this.doSubmit('coin')
      return
    }

    // 加载优惠券并弹出支付弹窗
    this.loadAvailableCoupons(estimatedPrice)
    this.setData({
      estimatedPrice,
      actualPrice: estimatedPrice,
      selectedPayType: 'coin',
      selectedCouponIndex: -1,
      couponDiscount: 0,
      showPayModal: true
    })
  },

  // 选择支付方式
  selectPayType(e) {
    this.setData({ selectedPayType: e.currentTarget.dataset.type })
  },

  // 阻止事件冒泡（空操作）
  noop() {},

  // 关闭支付弹窗
  closePayModal() {
    this.setData({ showPayModal: false })
  },

  // 加载可用优惠券
  async loadAvailableCoupons(totalPrice) {
    try {
      const res = await api.getMyCoupons('unused', 'venue')
      const coupons = (res.data || []).filter(c => {
        if (c.type === 'experience') return false
        if (c.min_amount && c.min_amount > totalPrice) return false
        // 严格过滤：只允许 venue 和 all 类型的券用于场馆预约
        if (c.applicable_type && c.applicable_type !== 'venue' && c.applicable_type !== 'all') return false
        return true
      })
      this.setData({ availableCoupons: coupons })
    } catch (err) {
      console.error('加载优惠券失败:', err)
      this.setData({ availableCoupons: [] })
    }
  },

  // 选择/取消优惠券
  selectCoupon(e) {
    const index = e.currentTarget.dataset.index
    const { availableCoupons, selectedCouponIndex, estimatedPrice } = this.data

    if (index === selectedCouponIndex) {
      // 取消选中
      this.setData({
        selectedCouponIndex: -1,
        couponDiscount: 0,
        actualPrice: estimatedPrice
      })
    } else {
      const coupon = availableCoupons[index]
      let discount = 0
      if (coupon.type === 'cash') {
        discount = Math.min(coupon.discount_value || 0, estimatedPrice)
      } else if (coupon.type === 'gift') {
        discount = estimatedPrice
      }
      this.setData({
        selectedCouponIndex: index,
        couponDiscount: discount,
        actualPrice: Math.max(0, estimatedPrice - discount)
      })
    }
  },

  // 确认支付方式后提交
  confirmPay() {
    this.setData({ showPayModal: false })
    this.doSubmit(this.data.selectedPayType)
  },

  // 实际提交预约
  async doSubmit(payType) {
    if (this.data.submitting) return
    this.setData({ submitting: true })

    try {
      const slots = this.data.selectedSlots
      const startHour = slots[0].hour
      const endHour = slots[slots.length - 1].hour + 1

      // 获取选中的优惠券ID
      const { availableCoupons, selectedCouponIndex } = this.data
      const couponId = selectedCouponIndex >= 0 ? availableCoupons[selectedCouponIndex].id : null

      const res = await app.request({
        url: '/member/reservations',
        method: 'POST',
        data: {
          venue_id: this.data.selectedVenueId,
          reservation_date: this.data.selectedDate,
          start_time: `${String(startHour).padStart(2, '0')}:00`,
          end_time: `${String(endHour).padStart(2, '0')}:00`,
          duration: this.data.selectedSlots.length * 60,
          pay_type: payType,
          coupon_id: couponId
        }
      })

      const data = res.data || {}

      // 微信支付：拉起支付
      if (data.pay_params) {
        this.handleWechatPay(data)
        return
      }

      // 金币支付或免费：直接成功
      wx.showToast({ title: '预约成功', icon: 'success' })
      this.resetAndRefresh()

    } catch (err) {
      console.error('预约失败:', err)
      wx.showToast({ title: err.message || '预约失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 处理微信支付
  handleWechatPay(data) {
    const { reservation_id, pay_params } = data

    wx.requestPayment({
      ...pay_params,
      success: () => {
        wx.showLoading({ title: '支付确认中...' })
        this.pollPaymentStatus(reservation_id, 0)
      },
      fail: (err) => {
        this.setData({ submitting: false })
        if (err.errMsg && err.errMsg.includes('cancel')) {
          wx.showToast({ title: '已取消支付', icon: 'none' })
        } else {
          wx.showToast({ title: '支付失败', icon: 'none' })
        }
      }
    })
  },

  // 轮询支付状态
  async pollPaymentStatus(reservationId, attempt) {
    if (attempt >= 10) {
      wx.hideLoading()
      this.setData({ submitting: false })
      wx.showToast({ title: '支付处理中，请稍后查看', icon: 'none' })
      this.resetAndRefresh()
      return
    }

    try {
      const res = await app.request({
        url: `/member/reservations/${reservationId}/pay-status`
      })

      if (res.data && res.data.status === 'pending') {
        wx.hideLoading()
        this.setData({ submitting: false })
        wx.showToast({ title: '预约成功', icon: 'success' })
        this.resetAndRefresh()
        return
      }
    } catch (err) {
      console.error('查询支付状态失败:', err)
    }

    // 1秒后重试
    setTimeout(() => {
      this.pollPaymentStatus(reservationId, attempt + 1)
    }, 1000)
  },

  // 重置选择并刷新数据
  resetAndRefresh() {
    this.setData({
      selectedSlots: [],
      selectedVenueId: null,
      selectedVenueName: '',
      selectedVenuePrice: 0
    })
    this.loadCoinBalance()
    setTimeout(() => {
      this.loadCalendarData()
    }, 1000)
  }
})
