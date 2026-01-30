App({
  globalData: {
    userInfo: null,
    memberInfo: null,
    token: '',
    baseUrl: 'https://yunlifang.cloud/api/v1',
    cartCount: 0,
    // 教练相关
    coachInfo: null,
    coachToken: '',
    // 会员等级与预约权限相关
    memberLevel: 'TRIAL',  // TRIAL, S, SS, SSS
    memberTheme: {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)'
    },
    canBook: false,          // 是否可以自行预约
    bookingQuota: 0,         // 每日预约额度（小时）
    usedQuota: 0,            // 已使用额度
    foodDiscount: 1,         // 餐饮折扣 (1=无折扣)
    violations: []           // 违规记录
  },

  // 会员等级主题色配置
  memberThemeConfig: {
    TRIAL: {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)',
      name: '体验会员'
    },
    S: {
      primary: '#4A90E2',
      gradient: 'linear-gradient(135deg, #4A90E2 0%, #6BA8F0 100%)',
      name: 'S级会员'
    },
    SS: {
      primary: '#9B59B6',
      gradient: 'linear-gradient(135deg, #9B59B6 0%, #B07CC8 100%)',
      name: 'SS级会员'
    },
    SSS: {
      primary: '#F39C12',
      gradient: 'linear-gradient(135deg, #F39C12 0%, #F5B041 100%)',
      name: 'SSS级会员'
    }
  },

  onLaunch() {
    console.log('[APP] onLaunch 开始')
    console.log('[APP] baseUrl:', this.globalData.baseUrl)

    // 网络连接测试
    this.testNetworkConnection()

    // 检查会员登录状态
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      this.getMemberInfo()
    }
    // 检查教练登录状态
    const coachToken = wx.getStorageSync('coach_token')
    if (coachToken) {
      this.globalData.coachToken = coachToken
      this.getCoachInfo()
    }
  },

  // 测试网络连接
  testNetworkConnection() {
    const testUrl = `${this.globalData.baseUrl}/member/venue-types`
    console.log('[NETWORK TEST] 开始测试:', testUrl)

    wx.request({
      url: testUrl,
      method: 'GET',
      timeout: 10000,
      success: (res) => {
        console.log('[NETWORK TEST] 成功!')
        console.log('[NETWORK TEST] statusCode:', res.statusCode)
        console.log('[NETWORK TEST] data:', JSON.stringify(res.data).substring(0, 200))
      },
      fail: (err) => {
        console.error('[NETWORK TEST] 失败!')
        console.error('[NETWORK TEST] errMsg:', err.errMsg)
        console.error('[NETWORK TEST] errno:', err.errno)
        console.error('[NETWORK TEST] 完整错误:', JSON.stringify(err))

        // 尝试获取网络状态
        wx.getNetworkType({
          success: (netRes) => {
            console.log('[NETWORK TEST] 当前网络类型:', netRes.networkType)
          }
        })
      }
    })
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
          // 更新会员等级相关信息
          const data = res.data.data
          // 优先使用 member_level 或 level_code
          const levelCode = data.member_level || data.level_code || 'TRIAL'
          that.setMemberTheme(levelCode)
          // 更新预约权限信息
          if (data.can_book !== undefined) {
            that.globalData.canBook = data.can_book
          }
          if (data.booking_quota !== undefined) {
            that.globalData.bookingQuota = data.booking_quota
          }
          if (data.used_quota !== undefined) {
            that.globalData.usedQuota = data.used_quota
          }
          if (data.food_discount !== undefined) {
            that.globalData.foodDiscount = data.food_discount
          }
        }
      }
    })
  },

  // 设置会员主题
  setMemberTheme(level) {
    const theme = this.memberThemeConfig[level] || this.memberThemeConfig.TRIAL
    this.globalData.memberLevel = level
    this.globalData.memberTheme = {
      primary: theme.primary,
      gradient: theme.gradient,
      name: theme.name
    }
    // 根据等级设置预约权限
    this.globalData.canBook = level !== 'TRIAL'
    // 设置每日预约额度
    const quotaMap = {
      TRIAL: 0,
      S: 2,
      SS: 4,
      SSS: 8
    }
    this.globalData.bookingQuota = quotaMap[level] || 0
  },

  // 获取当前会员主题
  getMemberTheme() {
    return this.globalData.memberTheme
  },

  // 检查是否可以预约
  checkCanBook() {
    return this.globalData.canBook
  },

  // 获取剩余预约额度
  getRemainingQuota() {
    return Math.max(0, this.globalData.bookingQuota - this.globalData.usedQuota)
  },

  // 退出登录
  logout() {
    wx.removeStorageSync('token')
    this.globalData.token = ''
    this.globalData.memberInfo = null
    this.globalData.cartCount = 0
    // 重置会员状态
    this.globalData.memberLevel = 'TRIAL'
    this.globalData.memberTheme = {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)'
    }
    this.globalData.canBook = false
    this.globalData.bookingQuota = 0
    this.globalData.usedQuota = 0
    this.globalData.foodDiscount = 1
    this.globalData.violations = []
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
  },

  // ==================== 教练相关方法 ====================

  // 检查教练登录状态
  checkCoachLogin() {
    if (!this.globalData.coachToken) {
      wx.navigateTo({
        url: '/pages/coach-login/coach-login'
      })
      return false
    }
    return true
  },

  // 获取教练信息
  getCoachInfo() {
    const that = this
    wx.request({
      url: `${this.globalData.baseUrl}/coach/profile`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${this.globalData.coachToken}`
      },
      success(res) {
        if (res.data.code === 200) {
          that.globalData.coachInfo = res.data.data
        }
      }
    })
  },

  // 教练退出登录
  coachLogout() {
    wx.removeStorageSync('coach_token')
    this.globalData.coachToken = ''
    this.globalData.coachInfo = null
    wx.navigateTo({
      url: '/pages/coach-login/coach-login'
    })
  },

  // 教练端请求方法
  coachRequest(options) {
    const that = this
    return new Promise((resolve, reject) => {
      wx.request({
        url: `${this.globalData.baseUrl}${options.url}`,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Authorization': `Bearer ${this.globalData.coachToken}`,
          'Content-Type': 'application/json',
          ...options.header
        },
        success(res) {
          if (res.data.code === 200) {
            resolve(res.data)
          } else if (res.statusCode === 401) {
            // token过期，跳转教练登录
            wx.removeStorageSync('coach_token')
            that.globalData.coachToken = ''
            wx.showToast({
              title: '登录已过期',
              icon: 'none'
            })
            wx.navigateTo({
              url: '/pages/coach-login/coach-login'
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
