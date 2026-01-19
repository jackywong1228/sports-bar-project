App({
  globalData: {
    userInfo: null,
    memberInfo: null,
    token: '',
    baseUrl: 'http://111.231.105.41/api/v1',
    cartCount: 0
  },

  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      this.getMemberInfo()
    }
  },

  // 检查登录状态，未登录则跳转登录页
  checkLogin() {
    if (!this.globalData.token) {
      wx.navigateTo({
        url: '/pages/login/login'
      })
      return false
    }
    return true
  },

  // 获取会员信息
  getMemberInfo() {
    const that = this
    wx.request({
      url: `${this.globalData.baseUrl}/member/profile`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${this.globalData.token}`
      },
      success(res) {
        if (res.data.code === 200) {
          that.globalData.memberInfo = res.data.data
        }
      }
    })
  },

  // 退出登录
  logout() {
    wx.removeStorageSync('token')
    this.globalData.token = ''
    this.globalData.memberInfo = null
    this.globalData.cartCount = 0
    wx.reLaunch({
      url: '/pages/index/index'
    })
  },

  // 统一请求方法
  request(options) {
    const that = this
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${this.globalData.baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Authorization': `Bearer ${this.globalData.token}`,
          'Content-Type': 'application/json',
          ...options.header
        },
        success(res) {
          if (res.data.code === 200) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            // token过期
            wx.removeStorageSync('token')
            that.globalData.token = ''
            wx.showToast({
              title: '登录已过期',
              icon: 'none'
            })
            reject(res.data)
          } else {
            wx.showToast({
              title: res.data.message || '请求失败',
              icon: 'none'
            })
            reject(res.data)
          }
        },
        fail(err) {
          wx.showToast({
            title: '网络错误',
            icon: 'none'
          })
          reject(err)
        }
      })
    })
  },

  // 更新购物车数量
  updateCartCount(count) {
    this.globalData.cartCount = count
    if (count > 0) {
      wx.setTabBarBadge({
        index: 2,
        text: String(count)
      })
    } else {
      wx.removeTabBarBadge({
        index: 2
      })
    }
  }
})
