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
    // 会员等级与权限相关（三级会员制：S/SS/SSS）
    memberLevel: 'S',  // S, SS, SSS
    memberTheme: {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)'
    },
    isMember: false,          // 是否为付费会员(SS/SSS)
    memberExpireTime: null,   // 会员到期时间
    canBook: false,           // 是否可以预约场馆
    _loginPromptShowing: false // checkLogin showModal 防抖 flag
  },

  // 会员等级主题色配置（三级会员制）
  memberThemeConfig: {
    S: {
      primary: '#999999',
      gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)',
      name: 'S级会员'
    },
    SS: {
      primary: '#C9A962',
      gradient: 'linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)',
      name: 'SS级会员'
    },
    SSS: {
      primary: '#8B7355',
      gradient: 'linear-gradient(135deg, #8B7355 0%, #C9A962 50%, #E8D5A3 100%)',
      name: 'SSS级会员'
    }
  },

  // 旧等级映射到新等级（兼容后端返回旧等级名）
  legacyLevelMap: {
    GUEST: 'S',
    TRIAL: 'S',
    MEMBER: 'SS'
  },

  onLaunch() {
    console.log('[APP] onLaunch 开始')
    console.log('[APP] baseUrl:', this.globalData.baseUrl)

    // 检查小程序更新（有新版本时弹窗提示立即重启）
    this.checkForUpdate()

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

  // 小程序热更新检测
  checkForUpdate() {
    if (!wx.getUpdateManager) {
      console.log('[UPDATE] 当前微信版本过低，无法使用自动更新')
      return
    }
    const updateManager = wx.getUpdateManager()
    updateManager.onCheckForUpdate((res) => {
      console.log('[UPDATE] hasUpdate:', res.hasUpdate)
    })
    updateManager.onUpdateReady(() => {
      wx.showModal({
        title: '更新提示',
        content: '发现新版本，是否立即重启体验？',
        confirmText: '立即更新',
        cancelText: '稍后',
        success: (res) => {
          if (res.confirm) {
            // 新版本已下载，调用 applyUpdate 应用并重启
            updateManager.applyUpdate()
          }
        }
      })
    })
    updateManager.onUpdateFailed(() => {
      console.error('[UPDATE] 新版本下载失败')
      wx.showToast({
        title: '新版本下载失败，请稍后重试',
        icon: 'none',
        duration: 2000
      })
    })
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

  // 将服务器相对路径转为完整URL（小程序中 /uploads/ 会被当作本地路径）
  resolveImageUrl(url) {
    if (!url) return ''
    if (url.startsWith('http://') || url.startsWith('https://')) return url
    if (url.startsWith('/uploads/')) {
      return this.globalData.baseUrl.replace('/api/v1', '') + url
    }
    return url
  },

  // 检查登录状态，未登录则弹出 modal 提示（满足审核：不强制跳转）
  // 同步返回 boolean，调用方按 `if (!app.checkLogin()) return` 模式短路
  checkLogin() {
    if (!this.globalData.token) {
      // 防抖：避免并发 onLoad/onShow 弹多个 modal
      if (!this.globalData._loginPromptShowing) {
        this.globalData._loginPromptShowing = true
        wx.showModal({
          title: '提示',
          content: '该功能需要登录，是否前往登录？',
          confirmText: '去登录',
          cancelText: '取消',
          success: (res) => {
            if (res.confirm) {
              wx.navigateTo({ url: '/pages/login/login' })
            }
          },
          complete: () => {
            this.globalData._loginPromptShowing = false
          }
        })
      }
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
        if (res.statusCode === 401) {
          // token 已过期，清除登录状态
          console.log('[APP] token 已过期，清除登录状态')
          that.globalData.token = ''
          wx.removeStorageSync('token')
          return
        }
        if (res.data.code === 200) {
          const data = res.data.data
          // 解析头像URL（/uploads/... → 完整URL）
          if (data.avatar) {
            data.avatar = that.resolveImageUrl(data.avatar)
          }
          that.globalData.memberInfo = data
          // 更新会员等级相关信息
          // 优先使用 level_code 或 member_level，兼容旧等级名
          const rawLevel = data.level_code || data.member_level || 'S'
          const levelCode = that.legacyLevelMap[rawLevel] || rawLevel
          that.setMemberTheme(levelCode)
          // 更新会员状态
          that.globalData.isMember = (levelCode === 'SS' || levelCode === 'SSS')
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
    // 兼容旧等级名，映射到 S/SS/SSS
    const mappedLevel = this.legacyLevelMap[level] || level
    const theme = this.memberThemeConfig[mappedLevel] || this.memberThemeConfig.S
    this.globalData.memberLevel = mappedLevel
    this.globalData.isMember = (mappedLevel === 'SS' || mappedLevel === 'SSS')
    this.globalData.memberTheme = {
      primary: theme.primary,
      gradient: theme.gradient,
      name: theme.name
    }
    // SS/SSS 可预约场馆
    this.globalData.canBook = (mappedLevel === 'SS' || mappedLevel === 'SSS')
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
    this.globalData.memberLevel = 'S'
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
