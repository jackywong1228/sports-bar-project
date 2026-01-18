const app = getApp()
const util = require('../../utils/util.js')

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
    selectedTimeIndex: 0
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
      dateOptions,
      timeOptions
    })
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

  async submitOrder() {
    const { cart, remark, orderType, dateOptions, selectedDateIndex, timeOptions, selectedTimeIndex } = this.data

    if (cart.length === 0) {
      wx.showToast({ title: '购物车为空', icon: 'none' })
      return
    }

    // 构建请求数据
    const requestData = {
      items: cart,
      remark: remark,
      order_type: orderType
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

      wx.removeStorageSync('foodCart')

      // 显示成功消息
      let successMsg = '下单成功'
      if (orderType === 'scheduled') {
        successMsg = `预约成功，${requestData.scheduled_date} ${requestData.scheduled_time} 取餐`
      }

      wx.showToast({
        title: successMsg,
        icon: 'success',
        duration: 2000
      })

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
  }
})
