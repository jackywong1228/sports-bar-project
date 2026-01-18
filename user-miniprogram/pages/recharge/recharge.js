const app = getApp()

Page({
  data: {
    packages: [],
    selectedPackage: null,
    loading: false
  },

  onLoad() {
    this.loadPackages()
  },

  // 加载充值套餐
  async loadPackages() {
    try {
      const res = await app.request({ url: '/payment/packages' })
      if (res.data && res.data.length > 0) {
        this.setData({ packages: res.data })
      }
    } catch (err) {
      console.error('加载套餐失败:', err)
      // 使用默认套餐
      this.setData({
        packages: [
          { id: 1, amount: 10, coins: 100, bonus: 0, label: '10元=100金币' },
          { id: 2, amount: 50, coins: 500, bonus: 50, label: '50元=550金币' },
          { id: 3, amount: 100, coins: 1000, bonus: 150, label: '100元=1150金币' },
          { id: 4, amount: 200, coins: 2000, bonus: 400, label: '200元=2400金币' },
          { id: 5, amount: 500, coins: 5000, bonus: 1500, label: '500元=6500金币' },
          { id: 6, amount: 1000, coins: 10000, bonus: 4000, label: '1000元=14000金币' }
        ]
      })
    }
  },

  // 选择套餐
  selectPackage(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ selectedPackage: id })
  },

  // 确认充值
  async confirmRecharge() {
    const { selectedPackage, packages } = this.data

    if (!selectedPackage) {
      wx.showToast({ title: '请选择充值套餐', icon: 'none' })
      return
    }

    const pkg = packages.find(p => p.id === selectedPackage)
    if (!pkg) {
      wx.showToast({ title: '套餐不存在', icon: 'none' })
      return
    }

    // 检查登录状态
    const memberInfo = app.globalData.memberInfo
    if (!memberInfo || !memberInfo.id) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      setTimeout(() => {
        wx.navigateTo({ url: '/pages/login/login' })
      }, 1500)
      return
    }

    this.setData({ loading: true })

    try {
      // 获取用户openid（实际项目中应该在登录时获取并存储）
      const openid = app.globalData.openid || ''

      if (!openid) {
        // 如果没有openid，尝试获取
        const loginRes = await new Promise((resolve, reject) => {
          wx.login({
            success: res => resolve(res),
            fail: err => reject(err)
          })
        })
        // 这里应该调用后端接口用code换取openid
        // 简化处理：模拟支付成功
        wx.showModal({
          title: '提示',
          content: '请先完成微信授权登录',
          showCancel: false
        })
        this.setData({ loading: false })
        return
      }

      // 创建充值订单
      const res = await app.request({
        url: '/payment/create-order',
        method: 'POST',
        data: {
          member_id: memberInfo.id,
          package_id: selectedPackage,
          openid: openid
        }
      })

      if (res.code !== 0) {
        throw new Error(res.message || '创建订单失败')
      }

      const { order_no, pay_params } = res.data

      // 调用微信支付
      await this.callWxPay(pay_params)

      // 支付成功，查询订单状态确认
      await this.checkOrderStatus(order_no)

      wx.showToast({ title: '充值成功', icon: 'success' })

      // 刷新会员信息
      setTimeout(() => {
        app.getMemberInfo()
        wx.navigateBack()
      }, 1500)

    } catch (err) {
      console.error('充值失败:', err)
      if (err.errMsg && err.errMsg.includes('cancel')) {
        wx.showToast({ title: '已取消支付', icon: 'none' })
      } else {
        wx.showToast({ title: err.message || '充值失败', icon: 'none' })
      }
    } finally {
      this.setData({ loading: false })
    }
  },

  // 调用微信支付
  callWxPay(payParams) {
    return new Promise((resolve, reject) => {
      wx.requestPayment({
        timeStamp: payParams.timeStamp,
        nonceStr: payParams.nonceStr,
        package: payParams.package,
        signType: payParams.signType,
        paySign: payParams.paySign,
        success: res => resolve(res),
        fail: err => reject(err)
      })
    })
  },

  // 查询订单状态
  async checkOrderStatus(orderNo) {
    try {
      const res = await app.request({
        url: `/payment/order/${orderNo}`
      })
      if (res.data && res.data.status === 'paid') {
        return true
      }
    } catch (err) {
      console.error('查询订单状态失败:', err)
    }
    return false
  }
})
