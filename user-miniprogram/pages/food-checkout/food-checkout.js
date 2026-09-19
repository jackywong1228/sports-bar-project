const app = getApp()
const api = require('../../utils/api')

const CART_KEY = 'food_cart'
const CTX_KEY = 'food_ctx'

function fen2text(n) {
  return (Math.round(n * 100) / 100).toFixed(2)
}

function pad2(n) {
  return String(n).padStart(2, '0')
}

function formatDate(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

// 生成取餐时段（30 分钟一档）。今天：至少 30 分钟后；明天：09:00 起。营业截到 21:30。
function buildSlots(dayOffset) {
  const slots = []
  const endMinutes = 21 * 60 + 30
  let startMinutes = 9 * 60
  if (dayOffset === 0) {
    const earliest = new Date(Date.now() + 30 * 60000)
    startMinutes = earliest.getHours() * 60 + earliest.getMinutes()
    // 向上取整到 30 分钟档
    startMinutes = Math.ceil(startMinutes / 30) * 30
  }
  for (let m = startMinutes; m <= endMinutes; m += 30) {
    slots.push(`${pad2(Math.floor(m / 60))}:${pad2(m % 60)}`)
  }
  return slots
}

// 预估优惠券抵扣（与后端 calc_coupon_discount 同规则，仅作展示，实扣以后端为准）
function estimateCouponDiscount(coupon, eligibleAmount) {
  if (!coupon || eligibleAmount <= 0) return 0
  let discount = 0
  if (coupon.type === 'cash') {
    discount = Number(coupon.discount_value || 0)
  } else if (coupon.type === 'gift') {
    discount = eligibleAmount
  } else if (coupon.type === 'discount') {
    const rate = Number(coupon.discount_value || 0)
    if (rate <= 0 || rate >= 1) return 0
    discount = eligibleAmount * (1 - rate)
  } else {
    return 0
  }
  return Math.round(Math.min(discount, eligibleAmount) * 100) / 100
}

// 优惠券展示文案
function couponLabel(c) {
  if (c.type === 'cash') return `¥${c.discount_value}`
  if (c.type === 'discount') return `${(Number(c.discount_value) * 10).toFixed(1)}折`
  if (c.type === 'gift') return '免单券'
  return c.name
}

Page({
  data: {
    // 购物车与上下文
    cart: [],
    orderType: 'dine_in',   // dine_in 堂食 / pickup 预约取餐
    tableNo: '',
    // 预约取餐时间
    pickupDay: 'today',     // today / tomorrow
    todaySlots: [],
    tomorrowSlots: [],
    currentSlots: [],
    tomorrowSlots: [],
    selectedSlot: '',
    // 金额
    totalText: '0.00',
    eligibleAmount: 0,      // 可用券商品金额（coupon_enabled=true）
    hasIneligible: false,   // 是否含不参与抵扣的商品（酒水等）
    // 优惠券
    coupons: [],
    selectedCouponId: null,
    selectedCouponLabel: '',
    discountText: '0.00',
    payText: '0.00',
    showCouponPanel: false,
    // 支付
    coinBalance: 0,
    coinEnough: true,
    payType: 'coin',
    remark: '',
    submitting: false,
  },

  onLoad() {
    if (!app.checkLogin()) {
      setTimeout(() => wx.navigateBack(), 800)
      return
    }
    const cartMap = wx.getStorageSync(CART_KEY) || {}
    const cart = Object.keys(cartMap).map(k => cartMap[k])
    if (cart.length === 0) {
      wx.showToast({ title: '购物车是空的', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 800)
      return
    }
    const ctx = wx.getStorageSync(CTX_KEY) || {}
    const orderType = ctx.mode === 'pickup' ? 'pickup' : 'dine_in'

    const todaySlots = buildSlots(0)
    const tomorrowSlots = buildSlots(1)
    const pickupDay = todaySlots.length > 0 ? 'today' : 'tomorrow'

    this.setData({
      cart,
      orderType,
      tableNo: ctx.tableNo || '',
      todaySlots,
      tomorrowSlots,
      pickupDay,
      currentSlots: pickupDay === 'today' ? todaySlots : tomorrowSlots,
      selectedSlot: '',
    })
    this.recalc()
    this.loadCoupons()
    this.loadCoinBalance()
  },

  // ==================== 金额 ====================

  recalc() {
    const { cart, coupons, selectedCouponId } = this.data
    let total = 0
    let eligible = 0
    for (const line of cart) {
      const subtotal = line.unit_price * line.quantity
      total += subtotal
      if (line.coupon_enabled) eligible += subtotal
    }
    total = Math.round(total * 100) / 100
    eligible = Math.round(eligible * 100) / 100

    const coupon = coupons.find(c => c.id === selectedCouponId) || null
    const discount = estimateCouponDiscount(coupon, eligible)
    const pay = Math.max(0, Math.round((total - discount) * 100) / 100)

    this.setData({
      totalText: fen2text(total),
      eligibleAmount: eligible,
      hasIneligible: eligible < total,
      discountText: fen2text(discount),
      payText: fen2text(pay),
      coinEnough: this.data.coinBalance >= pay,
    })
  },

  // ==================== 订单类型 ====================

  selectOrderType(e) {
    const type = e.currentTarget.dataset.type
    if (type === this.data.orderType) return
    this.setData({ orderType: type })
    if (type === 'dine_in' && !this.data.tableNo) {
      this.promptTableNo()
    }
  },

  onTableInput(e) {
    this.setData({ tableNo: e.detail.value.trim() })
  },

  promptTableNo() {
    wx.showModal({
      title: '请输入桌号',
      editable: true,
      placeholderText: '如：5',
      confirmText: '确定',
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          this.setData({ tableNo: res.content.trim() })
        }
      },
    })
  },

  selectPickupDay(e) {
    const day = e.currentTarget.dataset.day
    const slots = day === 'today' ? this.data.todaySlots : this.data.tomorrowSlots
    if (slots.length === 0) {
      wx.showToast({ title: '今日取餐时间已过，请选择明天', icon: 'none' })
      return
    }
    this.setData({ pickupDay: day, selectedSlot: '', currentSlots: slots })
  },

  selectSlot(e) {
    this.setData({ selectedSlot: e.currentTarget.dataset.slot })
  },

  // ==================== 优惠券 ====================

  async loadCoupons() {
    try {
      // applicable_type=food 后端会带上 all 通用券
      const res = await api.getMyCoupons('unused', 'food')
      const now = Date.now()
      const coupons = (res.data || [])
        // 体验券不可用于支付抵扣
        .filter(c => c.type !== 'experience')
        .map(c => {
          const startOk = !c.start_time || new Date(c.start_time.replace(/-/g, '/')).getTime() <= now
          const endOk = !c.end_time || new Date(c.end_time.replace(/-/g, '/')).getTime() >= now
          let usable = startOk && endOk
          let unusableReason = ''
          if (!startOk) unusableReason = '未生效'
          else if (!endOk) unusableReason = '已过期'
          return {
            ...c,
            label: couponLabel(c),
            usable,
            unusable_reason: unusableReason,
          }
        })
      this.setData({ coupons })
      this.refreshCouponUsable()
    } catch (err) {
      console.error('加载优惠券失败:', err)
    }
  },

  // 根据当前可用券商品金额刷新券可用状态（最低消费 / 金额需 > 0）
  refreshCouponUsable() {
    const eligible = this.data.eligibleAmount
    const coupons = this.data.coupons.map(c => {
      let usable = c.usable
      let reason = c.unusable_reason
      if (usable && eligible <= 0) {
        usable = false
        reason = '本单商品不可用券'
      } else if (usable && c.min_amount > 0 && eligible < c.min_amount) {
        usable = false
        reason = `可用券商品满 ¥${c.min_amount} 可用`
      } else if (usable) {
        reason = ''
      }
      return { ...c, usable, unusable_reason: reason }
    })
    const selected = coupons.find(c => c.id === this.data.selectedCouponId)
    this.setData({
      coupons,
      selectedCouponId: selected && selected.usable ? selected.id : null,
      selectedCouponLabel: selected && selected.usable ? selected.label : '',
    })
    this.recalc()
  },

  openCouponPanel() {
    this.setData({ showCouponPanel: true })
  },

  closeCouponPanel() {
    this.setData({ showCouponPanel: false })
  },

  noop() {},

  selectCoupon(e) {
    const { id, usable } = e.currentTarget.dataset
    if (!usable) return
    if (id === this.data.selectedCouponId) {
      this.setData({ selectedCouponId: null, selectedCouponLabel: '' })
    } else {
      const coupon = this.data.coupons.find(c => c.id === id)
      this.setData({ selectedCouponId: id, selectedCouponLabel: coupon ? coupon.label : '' })
    }
    this.recalc()
  },

  // ==================== 支付 ====================

  async loadCoinBalance() {
    try {
      const res = await app.request({ url: '/member/profile' })
      if (res.data) {
        const balance = parseFloat(res.data.coin_balance || 0)
        this.setData({ coinBalance: balance }, () => this.recalc())
      }
    } catch (err) {
      console.error('加载余额失败:', err)
    }
  },

  selectPayType(e) {
    const type = e.currentTarget.dataset.type
    if (type === 'coin' && !this.data.coinEnough) {
      wx.showToast({ title: '金币余额不足', icon: 'none' })
      return
    }
    this.setData({ payType: type })
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  async submit() {
    const { orderType, tableNo, pickupDay, selectedSlot, cart, selectedCouponId, payType, remark, submitting } = this.data
    if (submitting) return

    if (orderType === 'dine_in' && !tableNo) {
      this.promptTableNo()
      return
    }
    if (orderType === 'pickup' && !selectedSlot) {
      wx.showToast({ title: '请选择取餐时间', icon: 'none' })
      return
    }

    let pickupTime = null
    if (orderType === 'pickup') {
      const d = new Date()
      if (pickupDay === 'tomorrow') d.setDate(d.getDate() + 1)
      pickupTime = `${formatDate(d)} ${selectedSlot}`
    }

    const payload = {
      items: cart.map(line => ({
        item_id: line.item_id,
        specs: line.specs || undefined,
        quantity: line.quantity,
      })),
      order_type: orderType,
      table_no: orderType === 'dine_in' ? tableNo : undefined,
      pickup_time: pickupTime || undefined,
      coupon_id: selectedCouponId || undefined,
      pay_type: payType,
      remark: remark || undefined,
    }

    this.setData({ submitting: true })
    try {
      const res = await api.createFoodOrder(payload)
      const data = res.data || {}

      // 微信支付：拉起 wx.requestPayment + 轮询（镜像 course-detail.js 模式）
      if (data.pay_params) {
        this.handleWechatPay(data)
        return
      }

      // 金币支付 / 零元单：直接成功
      this.onOrderDone(data.order_id, '支付成功')
    } catch (err) {
      console.error('提交订单失败:', err)
      this.setData({ submitting: false })
    }
  },

  handleWechatPay(data) {
    const { order_id, pay_params } = data
    wx.requestPayment({
      ...pay_params,
      success: () => {
        wx.showLoading({ title: '支付确认中...' })
        this.pollPayStatus(order_id, 0)
      },
      fail: (err) => {
        this.setData({ submitting: false })
        if (err.errMsg && err.errMsg.includes('cancel')) {
          wx.showToast({ title: '已取消支付，可在订单详情中继续支付', icon: 'none' })
          // 订单已创建（unpaid），跳详情方便重新支付
          setTimeout(() => {
            wx.redirectTo({ url: `/pages/food-order-detail/food-order-detail?id=${order_id}` })
          }, 1200)
        } else {
          wx.showToast({ title: '支付失败', icon: 'none' })
        }
      },
    })
  },

  async pollPayStatus(orderId, attempt) {
    if (attempt >= 10) {
      wx.hideLoading()
      this.setData({ submitting: false })
      wx.showToast({ title: '支付处理中，请稍后到订单详情查看', icon: 'none' })
      this.onOrderDone(orderId)
      return
    }
    try {
      const res = await api.getFoodOrderPayStatus(orderId)
      if (res.data && res.data.status !== 'unpaid') {
        wx.hideLoading()
        this.onOrderDone(orderId, '支付成功')
        return
      }
    } catch (err) {
      console.error('查询支付状态失败:', err)
    }
    setTimeout(() => this.pollPayStatus(orderId, attempt + 1), 1000)
  },

  // 下单完成：清空购物车与上下文，跳订单详情
  onOrderDone(orderId, toastText) {
    this.setData({ submitting: false })
    wx.removeStorageSync(CART_KEY)
    wx.removeStorageSync(CTX_KEY)
    if (toastText) {
      wx.showToast({ title: toastText, icon: 'success' })
    }
    setTimeout(() => {
      wx.redirectTo({ url: `/pages/food-order-detail/food-order-detail?id=${orderId}` })
    }, 1000)
  },
})
