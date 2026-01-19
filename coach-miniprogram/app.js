App({
  globalData: {
    userInfo: null,
    coachInfo: null,
    token: '',
    baseUrl: 'http://111.231.105.41/api/v1'
  },

  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('coach_token')
    if (token) {
      this.globalData.token = token
      this.getCoachInfo()
    }
  },

  // 检查登录状态，未登录则跳转登录页
  checkLogin() {
    if (!this.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      })
      return false
    }
    return true
  },

  // 退出登录
  logout() {
    wx.removeStorageSync('coach_token')
    this.globalData.token = ''
    this.globalData.coachInfo = null
    wx.redirectTo({
      url: '/pages/login/login'
    })
  },

  // 获取教练信息
  getCoachInfo() {
    const that = this
    wx.request({
      url: `${this.globalData.baseUrl}/coach/profile`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${this.globalData.token}`
      },
      success(res) {
        if (res.data.code === 200) {
          that.globalData.coachInfo = res.data.data
        }
      }
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
            // token过期，跳转登录
            wx.removeStorageSync('coach_token')
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
  }
})
