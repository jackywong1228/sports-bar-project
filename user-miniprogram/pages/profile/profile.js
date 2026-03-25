const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    memberInfo: null,
    isLoggedIn: false,
    isCoach: false,
    // 会员等级相关（S/SS/SSS）
    memberLevel: 'S',
    isMember: false,
    memberTheme: null,
    // 编辑相关
    isEditingNickname: false,
    editNickname: '',
    checkinStats: {
      month_count: 0,
      month_duration: 0,
      month_points: 0
    },
    menus: [
      { icon: '/assets/icons/order.png', text: '我的订单', url: '/pages/orders/orders' },
      { icon: '/assets/icons/reservation.png', text: '我的预约', url: '/pages/orders/orders?type=reservation' },
      { icon: '/assets/icons/coupon.png', text: '我的优惠券', url: '/pages/coupons/coupons' },
      { icon: '/assets/icons/team-entry.png', text: '我的组队', url: '/pages/my-teams/my-teams' },
      { icon: '/assets/icons/member-card.png', text: '会员中心', url: '/pages/member/member' }
    ],
    tools: [
      { icon: '/assets/icons/feedback.png', text: '意见反馈', action: 'feedback' },
      { icon: '/assets/icons/settings.png', text: '设置', url: '/pages/settings/settings' },
      { icon: '/assets/icons/about.png', text: '关于我们', action: 'about' }
    ]
  },

  onLoad() {
    this.checkLoginStatus()
  },

  onShow() {
    this.checkLoginStatus()
  },

  // 检查登录状态
  checkLoginStatus() {
    const isLoggedIn = !!app.globalData.token
    const memberInfo = app.globalData.memberInfo
    // 优先从 memberInfo 获取会员等级，确保与后端数据一致
    const memberLevel = this.getMemberLevelFromInfo(memberInfo) || app.globalData.memberLevel || 'S'

    this.setData({
      isLoggedIn,
      memberInfo: memberInfo,
      memberLevel: memberLevel,
      isMember: app.globalData.isMember || (memberLevel === 'SS' || memberLevel === 'SSS'),
      memberTheme: app.globalData.memberTheme
    })

    // 登录状态下始终刷新会员信息，确保等级等数据最新
    if (isLoggedIn) {
      this.refreshMemberInfo()
      this.checkCoachStatus()
      this.loadCheckinStats()
    }
  },

  // 刷新会员信息（通过回调更新，避免硬编码延时）
  refreshMemberInfo() {
    const that = this
    wx.request({
      url: `${app.globalData.baseUrl}/member/profile`,
      method: 'GET',
      header: {
        'Authorization': `Bearer ${app.globalData.token}`
      },
      success(res) {
        if (res.data.code === 200) {
          const data = res.data.data
          // 解析头像URL（/uploads/... → 完整URL）
          if (data.avatar) {
            data.avatar = app.resolveImageUrl(data.avatar)
          }
          app.globalData.memberInfo = data
          // 兼容旧等级名，映射到 S/SS/SSS
          const rawLevel = data.member_level || data.level_code || 'S'
          app.setMemberTheme(rawLevel)  // setMemberTheme 内部已做映射
          const mappedLevel = app.globalData.memberLevel  // 取映射后的值
          that.setData({
            memberInfo: data,
            memberLevel: mappedLevel,
            isMember: app.globalData.isMember,
            memberTheme: app.globalData.memberTheme
          })
        }
      }
    })
  },

  // 从会员信息中获取等级代码（兼容旧等级名映射到 S/SS/SSS）
  getMemberLevelFromInfo(memberInfo) {
    if (!memberInfo) return null
    const rawLevel = memberInfo.member_level || memberInfo.level_code || null
    if (!rawLevel) return null
    // 兼容旧等级名（GUEST/TRIAL→S, MEMBER→SS）
    const legacyMap = { GUEST: 'S', TRIAL: 'S', MEMBER: 'SS' }
    return legacyMap[rawLevel] || rawLevel
  },

  // 加载打卡统计
  async loadCheckinStats() {
    try {
      const res = await api.getCheckinStats()
      if (res.code === 200) {
        this.setData({
          checkinStats: res.data
        })
      }
    } catch (err) {
      console.error('加载打卡统计失败:', err)
    }
  },

  // 检查教练身份
  async checkCoachStatus() {
    try {
      const coachToken = wx.getStorageSync('coach_token')
      if (coachToken) {
        this.setData({ isCoach: true })
        return
      }
      // 可以调用后端接口检查用户是否有教练身份
      // 这里简化处理，默认显示"申请成为教练"
    } catch (err) {
      console.error('检查教练状态失败:', err)
    }
  },

  // 跳转教练中心
  goToCoachCenter() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }

    const coachToken = wx.getStorageSync('coach_token')
    if (coachToken) {
      // 已是教练，直接进入教练首页
      wx.navigateTo({
        url: '/pages/coach-home/coach-home'
      })
    } else {
      // 未登录教练，跳转教练登录页
      wx.navigateTo({
        url: '/pages/coach-login/coach-login'
      })
    }
  },

  // 登录
  goToLogin() {
    wx.navigateTo({
      url: '/pages/login/login'
    })
  },

  // 菜单点击
  onMenuTap(e) {
    const { url } = e.currentTarget.dataset
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({ url })
  },

  // 工具点击
  onToolTap(e) {
    const { action, url } = e.currentTarget.dataset

    if (url) {
      wx.navigateTo({ url })
      return
    }

    switch (action) {
      case 'feedback':
        wx.navigateTo({ url: '/pages/feedback/feedback' })
        break
      case 'about':
        wx.showModal({
          title: '关于我们',
          content: '运动社交 v1.0.0\n专业的体育场馆服务平台',
          showCancel: false
        })
        break
    }
  },

  // 跳转钱包
  goToWallet() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/wallet/wallet'
    })
  },

  // 充值
  goToRecharge() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/recharge/recharge'
    })
  },

  // 跳转训练日历
  goToCalendar() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/checkin-calendar/checkin-calendar'
    })
  },

  // 跳转排行榜
  goToLeaderboard() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/leaderboard/leaderboard'
    })
  },

  // 会员卡片点击
  onMemberCardTap(e) {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/member/member'
    })
  },

  // ==================== 资料编辑 ====================

  // 选择头像（使用 chooseMedia 替代 chooseAvatar，避免模拟器 TLS 错误）
  async onChangeAvatar() {
    try {
      const res = await new Promise((resolve, reject) => {
        wx.chooseMedia({
          count: 1,
          mediaType: ['image'],
          sourceType: ['album', 'camera'],
          success: resolve,
          fail: reject
        })
      })
      const tempFilePath = res.tempFiles[0].tempFilePath

      wx.showLoading({ title: '上传中...' })
      const { upload } = require('../../utils/request')
      const uploadRes = await upload('/upload/member-image', tempFilePath, 'file')
      if (uploadRes.data && uploadRes.data.url) {
        const avatarUrl = uploadRes.data.url
        await api.updateUserProfile({ avatar: avatarUrl })

        // 显示用完整URL，后端存的是相对路径
        const displayUrl = app.resolveImageUrl(avatarUrl)
        const memberInfo = { ...this.data.memberInfo, avatar: displayUrl }
        app.globalData.memberInfo = memberInfo
        this.setData({ memberInfo })

        wx.showToast({ title: '头像更新成功', icon: 'success' })
      }
    } catch (err) {
      if (err.errMsg && err.errMsg.includes('cancel')) return
      console.error('更新头像失败:', err)
      wx.showToast({ title: '更新失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  // 打开昵称编辑
  onEditNickname() {
    this.setData({
      isEditingNickname: true,
      editNickname: this.data.memberInfo.nickname || ''
    })
  },

  // 昵称输入
  onNicknameInput(e) {
    this.setData({ editNickname: e.detail.value })
  },

  // 取消编辑昵称
  cancelEditNickname() {
    this.setData({ isEditingNickname: false, editNickname: '' })
  },

  // 确认修改昵称
  async confirmEditNickname() {
    const nickname = this.data.editNickname.trim()
    if (!nickname) {
      wx.showToast({ title: '昵称不能为空', icon: 'none' })
      return
    }

    wx.showLoading({ title: '保存中...' })

    try {
      await api.updateUserProfile({ nickname })

      const memberInfo = { ...this.data.memberInfo, nickname }
      app.globalData.memberInfo = memberInfo
      this.setData({
        memberInfo,
        isEditingNickname: false,
        editNickname: ''
      })

      wx.showToast({ title: '昵称修改成功', icon: 'success' })
    } catch (err) {
      console.error('修改昵称失败:', err)
      wx.showToast({ title: '修改失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  }
})
