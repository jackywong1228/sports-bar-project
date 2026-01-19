const app = getApp()

Page({
  data: {
    coachInfo: {}
  },

  onLoad() {
    this.loadCoachInfo()
  },

  onShow() {
    this.loadCoachInfo()
  },

  // 加载教练信息
  async loadCoachInfo() {
    try {
      const res = await app.coachRequest({
        url: '/coach/profile'
      })
      this.setData({ coachInfo: res.data || {} })
    } catch (err) {
      console.error('加载教练信息失败:', err)
    }
  },

  // 跳转到钱包
  goToWallet(e) {
    const type = e.currentTarget.dataset.type || ''
    wx.navigateTo({
      url: `/pages/coach-wallet/coach-wallet?type=${type}`
    })
  },

  // 跳转到课程收入
  goToIncome() {
    wx.navigateTo({
      url: '/pages/coach-income/coach-income'
    })
  },

  // 跳转到订单
  goToOrders() {
    wx.navigateTo({
      url: '/pages/coach-orders/coach-orders'
    })
  },

  // 跳转到推广
  goToPromote(e) {
    const type = e.currentTarget.dataset.type || 'user'
    wx.navigateTo({
      url: `/pages/coach-promote/coach-promote?type=${type}`
    })
  },

  // 跳转到应用中心
  goToAppCenter() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  },

  // 切换到用户端
  switchToUser() {
    wx.showModal({
      title: '切换到用户端',
      content: '确定要切换到用户端吗？',
      success: (res) => {
        if (res.confirm) {
          // 跳转到用户端首页
          wx.switchTab({
            url: '/pages/index/index'
          })
        }
      }
    })
  },

  // 编辑资料
  editProfile() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  },

  // 联系客服
  contactService() {
    wx.makePhoneCall({
      phoneNumber: '400-000-0000',
      fail: () => {
        wx.showToast({
          title: '拨打失败',
          icon: 'none'
        })
      }
    })
  },

  // 意见反馈
  feedback() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  },

  // 关于我们
  about() {
    wx.showModal({
      title: '关于我们',
      content: '场馆体育社交系统 v1.0.0\n专业的体育场馆管理平台',
      showCancel: false
    })
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.coachLogout()
        }
      }
    })
  }
})
