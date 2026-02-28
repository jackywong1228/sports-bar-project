App({
  globalData: {
    userInfo: null,
    memberInfo: null,
    token: '',
    openid: '',
    baseUrl: 'https://yunlifang.cloud/api/v1',
    cartCount: 0,
    // 教练相关
    coachInfo: null,
    coachToken: '',
    // 会员等级与权限相关（单一会员制：GUEST/MEMBER）
    memberLevel: 'GUEST',  // GUEST, MEMBER
    memberTheme: {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)'
    },
    isMember: false,          // 是否为正式会员
    memberExpireTime: null,   // 会员到期时间
    canBook: false            // 是否可以自行预约
  },

  // 会员等级主题色配置（单一会员制）
  memberThemeConfig: {
    GUEST: {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)',
      name: '普通用户'
    },
    MEMBER: {
      primary: '#C9A962',
      gradient: 'linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)',
      name: '尊享会员'
    }
  },

  // 旧等级映射到新等级（兼容后端返回旧等级名）
  legacyLevelMap: {
    TRIAL: 'GUEST',
    S: 'MEMBER',
    SS: 'MEMBER',
    SSS: 'MEMBER'
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
    const openid = wx.getStorageSync('openid')
    if (openid) {
      this.globalData.openid = openid
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
    console.log('[NETWORK TEST] 测试:', testUrl)

    wx.request({
      url: testUrl,
      method: 'GET',
      timeout: 10000,
      success: (res) => {
        console.log('[NETWORK TEST] 成功, statusCode:', res.statusCode)
      },
      fail: (err) => {
        console.error('[NETWORK TEST] 失败:', err.errMsg)
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
          // 优先使用 member_level 或 level_code，兼容旧等级名
          const rawLevel = data.member_level || data.level_code || 'GUEST'
          const levelCode = that.legacyLevelMap[rawLevel] || rawLevel
          that.setMemberTheme(levelCode)
          // 更新会员状态
          that.globalData.isMember = (levelCode === 'MEMBER')
          if (data.member_expire_time !== undefined) {
            that.globalData.memberExpireTime = data.member_expire_time
          }
          if (data.can_book !== undefined) {
            that.globalData.canBook = data.can_book
          }
        }
      }
    })
  },

  // 设置会员主题（兼容旧等级名）
  setMemberTheme(level) {
    // 兼容旧等级名，映射到新的 GUEST/MEMBER
    const mappedLevel = this.legacyLevelMap[level] || level
    const theme = this.memberThemeConfig[mappedLevel] || this.memberThemeConfig.GUEST
    this.globalData.memberLevel = mappedLevel
    this.globalData.isMember = (mappedLevel === 'MEMBER')
    this.globalData.memberTheme = {
      primary: theme.primary,
      gradient: theme.gradient,
      name: theme.name
    }
    // 根据会员状态设置预约权限
    this.globalData.canBook = (mappedLevel === 'MEMBER')
  },

  // 获取当前会员主题
  getMemberTheme() {
    return this.globalData.memberTheme
  },

  // 检查是否可以预约
  checkCanBook() {
    return this.globalData.canBook
  },

  // 检查是否为正式会员
  checkIsMember() {
    return this.globalData.isMember
  },

  // 退出登录
  logout() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('openid')
    this.globalData.token = ''
    this.globalData.openid = ''
    this.globalData.memberInfo = null
    this.globalData.cartCount = 0
    // 重置会员状态
    this.globalData.memberLevel = 'GUEST'
    this.globalData.isMember = false
    this.globalData.memberExpireTime = null
    this.globalData.memberTheme = {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)'
    }
    this.globalData.canBook = false
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
