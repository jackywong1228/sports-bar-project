const app = getApp()
const util = require('../../utils/util.js')
const api = require('../../utils/api.js')

Page({
  data: {
    cart: [],
    total: 0,
    remark: '',
    submitting: false,
    // 取餐方式
    orderType: 'immediate', // immediate立即取餐 / scheduled预约取餐
    // 预约日期选项
    dateOptions: [],
    selectedDateIndex: 0,
    // 预约时间选项
    timeOptions: [],
    selectedTimeIndex: 0,
    // 优惠券相关
    availableCoupons: [],
    selectedCouponIndex: -1,
    couponDiscount: 0,
    payAmount: 0,
    // 支付弹窗
    showPayModal: false,
    selectedPayType: 'coin',
    coinBalance: 0
  },

  onLoad() {
    const cart = wx.getStorageSync('foodCart') || []
    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)

    // 生成日期选项（今天和未来6天）
    const dateOptions = this.generateDateOptions()
    // 生成时间选项
    const timeOptions = this.generateTimeOptions()

    this.setData({
      cart,
      total,
      payAmount: total,
      dateOptions,
      timeOptions,
      coinBalance: app.globalData.memberInfo?.coin_balance || 0
    })

    this.loadAvailableCoupons(total)
  },

  // 加载可用优惠券
  async loadAvailableCoupons(totalPrice) {
    try {
      const res = await api.getMyCoupons('unused', 'food')
      const coupons = (res.data || []).filter(c => {
        if (c.type === 'experience') return false
        if (c.min_amount && c.min_amount > totalPrice) return false
        // 严格过滤：只允许 food 和 all 类型的券用于餐饮消费
        if (c.applicable_type && c.applicable_type !== 'food' && c.applicable_type !== 'all') return false
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
    const { availableCoupons, selectedCouponIndex, total } = this.data

    if (index === selectedCouponIndex) {
      this.setData({
        selectedCouponIndex: -1,
        couponDiscount: 0,
        payAmount: total
      })
    } else {
      const coupon = availableCoupons[index]
      let discount = 0
      if (coupon.type === 'cash') {
        discount = Math.min(coupon.discount_value || 0, total)
      } else if (coupon.type === 'gift') {
        discount = total
      }
      this.setData({
        selectedCouponIndex: index,
        couponDiscount: discount,
        payAmount: Math.max(0, total - discount)
      })
    }
  },

  // 生成日期选项
  generateDateOptions() {
    const options = []
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const today = new Date()

    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)

      const dateStr = util.formatDate(date, 'YYYY-MM-DD')
      const month = date.getMonth() + 1
      const day = date.getDate()
      const weekDay = weekDays[date.getDay()]
      const label = i === 0 ? `今天 ${month}/${day}` : `${weekDay} ${month}/${day}`

      options.push({
        value: dateStr,
        label: label
      })
    }

    return options
  },

  // 生成时间选项（8:00 - 21:00，每30分钟一个选项）
  generateTimeOptions() {
    const options = []
    for (let hour = 8; hour <= 21; hour++) {
      options.push({
        value: `${String(hour).padStart(2, '0')}:00`,
        label: `${String(hour).padStart(2, '0')}:00`
      })
      if (hour < 21) {
        options.push({
          value: `${String(hour).padStart(2, '0')}:30`,
          label: `${String(hour).padStart(2, '0')}:30`
        })
      }
    }
    return options
  },

  // 切换取餐方式
  onOrderTypeChange(e) {
    this.setData({
      orderType: e.detail.value
    })
  },

  // 选择日期
  onDateChange(e) {
    this.setData({
      selectedDateIndex: parseInt(e.detail.value)
    })
  },

  // 选择时间
  onTimeChange(e) {
    this.setData({
      selectedTimeIndex: parseInt(e.detail.value)
    })
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  // 点击下单按钮
  submitOrder() {
    const { cart, payAmount } = this.data
    if (cart.length === 0) {
      wx.showToast({ title: '购物车为空', icon: 'none' })
      return
    }
    // 全额券抵扣 → 直接下单，不弹支付弹窗
    if (payAmount <= 0) {
      this.doSubmit('coin')
      return
    }
    // 弹出支付方式选择
    this.setData({ showPayModal: true })
  },

  // 选择支付方式
  selectPayType(e) {
    this.setData({ selectedPayType: e.currentTarget.dataset.type })
  },

  // 关闭支付弹窗
  closePayModal() {
    this.setData({ showPayModal: false })
  },

  // 阻止冒泡
  noop() {},

  // 确认支付
  confirmPay() {
    this.setData({ showPayModal: false })
    this.doSubmit(this.data.selectedPayType)
  },

  // 执行下单
  async doSubmit(payType) {
    const { cart, remark, orderType, dateOptions, selectedDateIndex, timeOptions, selectedTimeIndex } = this.data

    // 获取选中的优惠券ID
    const { availableCoupons, selectedCouponIndex } = this.data
    const couponId = selectedCouponIndex >= 0 ? availableCoupons[selectedCouponIndex].id : null

    // 构建请求数据
    const requestData = {
      items: cart,
      remark: remark,
      order_type: orderType,
      coupon_id: couponId,
      pay_type: payType
    }

    // 如果是预约取餐，添加预约时间
    if (orderType === 'scheduled') {
      requestData.scheduled_date = dateOptions[selectedDateIndex].value
      requestData.scheduled_time = timeOptions[selectedTimeIndex].value
    }

    this.setData({ submitting: true })

    try {
      const res = await app.request({
        url: '/member/food-orders',
        method: 'POST',
        data: requestData
      })

      const data = res.data || res

      // 微信支付：拉起支付
      if (data.pay_params) {
        this.handleWechatPay(data)
        return
      }

      // 金币支付/全额抵扣：直接成功
      wx.removeStorageSync('foodCart')
      let successMsg = '下单成功'
      if (orderType === 'scheduled') {
        successMsg = `预约成功，${requestData.scheduled_date} ${requestData.scheduled_time} 取餐`
      }

      wx.showToast({
        title: successMsg,
        icon: 'success',
        duration: 2000
      })

      // 刷新金币余额
      if (payType === 'coin' && app.globalData.memberInfo) {
        app.globalData.memberInfo.coin_balance = (app.globalData.memberInfo.coin_balance || 0) - (this.data.payAmount || 0)
      }

      setTimeout(() => wx.navigateBack({ delta: 2 }), 2000)
    } catch (err) {
      console.error('下单失败:', err)
      wx.showToast({
        title: err.message || '下单失败',
        icon: 'none'
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 处理微信支付
  handleWechatPay(data) {
    const payParams = data.pay_params
    const orderId = data.order_id

    wx.requestPayment({
      timeStamp: payParams.timeStamp,
      nonceStr: payParams.nonceStr,
      package: payParams.package,
      signType: payParams.signType || 'RSA',
      paySign: payParams.paySign,
      success: () => {
        wx.removeStorageSync('foodCart')
        this.pollPaymentStatus(orderId, 0)
      },
      fail: (err) => {
        console.error('微信支付取消或失败:', err)
        this.setData({ submitting: false })
        if (err.errMsg && err.errMsg.includes('cancel')) {
          wx.showToast({ title: '已取消支付', icon: 'none' })
        } else {
          wx.showToast({ title: '支付失败，请重试', icon: 'none' })
        }
      }
    })
  },

  // 轮询支付状态
  pollPaymentStatus(orderId, attempt) {
    if (attempt >= 10) {
      this.setData({ submitting: false })
      wx.showToast({ title: '支付确认中，请稍后查看订单', icon: 'none' })
      setTimeout(() => wx.navigateBack({ delta: 2 }), 2000)
      return
    }

    setTimeout(async () => {
      try {
        const res = await app.request({
          url: `/member/food-orders/${orderId}/pay-status`,
          method: 'GET'
        })
        const status = (res.data || res).status
        if (status === 'paid') {
          this.setData({ submitting: false })
          wx.showToast({ title: '支付成功', icon: 'success', duration: 2000 })
          setTimeout(() => wx.navigateBack({ delta: 2 }), 2000)
        } else {
          this.pollPaymentStatus(orderId, attempt + 1)
        }
      } catch (err) {
        console.error('查询支付状态失败:', err)
        this.pollPaymentStatus(orderId, attempt + 1)
      }
    }, 1000)
  }
})
