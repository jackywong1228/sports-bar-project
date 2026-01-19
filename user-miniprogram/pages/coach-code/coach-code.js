const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    coachInfo: {},
    todayStats: {},
    refreshTimeText: '',
    refreshTimer: null,
    codeExpireTime: null
  },

  onLoad() {
    this.loadCoachInfo()
    this.loadTodayStats()
    this.generateQRCode()
    this.startRefreshTimer()
  },

  onShow() {
    this.loadCoachInfo()
    this.loadTodayStats()
  },

  onHide() {
    this.stopRefreshTimer()
  },

  onUnload() {
    this.stopRefreshTimer()
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

  // 加载今日统计
  async loadTodayStats() {
    try {
      const today = util.formatDate(new Date(), 'YYYY-MM-DD')
      const res = await app.coachRequest({
        url: `/coach/reservations/stats?date=${today}`
      })
      this.setData({ todayStats: res.data || {} })
    } catch (err) {
      console.error('加载今日统计失败:', err)
    }
  },

  // 生成二维码
  generateQRCode() {
    // 设置过期时间（5分钟后）
    const expireTime = new Date()
    expireTime.setMinutes(expireTime.getMinutes() + 5)
    this.setData({ codeExpireTime: expireTime })

    // 生成二维码内容
    const codeData = {
      type: 'coach_code',
      coach_id: this.data.coachInfo.id || app.globalData.coachInfo?.id,
      timestamp: Date.now(),
      expire: expireTime.getTime()
    }

    // 简单的占位实现，实际需要使用二维码生成库
    const ctx = wx.createCanvasContext('coachQrcode')
    ctx.setFillStyle('#fff')
    ctx.fillRect(0, 0, 180, 180)

    // 绘制简单的二维码占位
    ctx.setFillStyle('#333')
    for (let i = 0; i < 8; i++) {
      for (let j = 0; j < 8; j++) {
        if (Math.random() > 0.5) {
          ctx.fillRect(20 + i * 17, 20 + j * 17, 15, 15)
        }
      }
    }

    // 绘制中心图标
    ctx.setFillStyle('#1890ff')
    ctx.fillRect(70, 70, 40, 40)
    ctx.setFillStyle('#fff')
    ctx.setFontSize(12)
    ctx.setTextAlign('center')
    ctx.fillText('教练', 90, 95)

    ctx.draw()

    this.updateRefreshTime()
  },

  // 更新刷新时间显示
  updateRefreshTime() {
    const { codeExpireTime } = this.data
    if (!codeExpireTime) return

    const now = new Date()
    const diff = Math.max(0, Math.floor((codeExpireTime - now) / 1000))
    const minutes = Math.floor(diff / 60)
    const seconds = diff % 60

    this.setData({
      refreshTimeText: `${minutes}分${seconds.toString().padStart(2, '0')}秒后自动刷新`
    })
  },

  // 开始刷新计时器
  startRefreshTimer() {
    this.stopRefreshTimer()

    // 每秒更新倒计时
    const timer = setInterval(() => {
      const { codeExpireTime } = this.data
      if (!codeExpireTime) return

      const now = new Date()
      if (now >= codeExpireTime) {
        // 自动刷新
        this.generateQRCode()
      } else {
        this.updateRefreshTime()
      }
    }, 1000)

    this.setData({ refreshTimer: timer })
  },

  // 停止刷新计时器
  stopRefreshTimer() {
    const { refreshTimer } = this.data
    if (refreshTimer) {
      clearInterval(refreshTimer)
      this.setData({ refreshTimer: null })
    }
  },

  // 手动刷新二维码
  refreshCode() {
    this.generateQRCode()
    wx.showToast({
      title: '已刷新',
      icon: 'success'
    })
  },

  // 跳转到钱包
  goToWallet(e) {
    const type = e.currentTarget.dataset.type
    wx.navigateTo({
      url: `/pages/coach-wallet/coach-wallet?type=${type}`
    })
  },

  // 跳转到首页
  goToIndex() {
    wx.switchTab({
      url: '/pages/coach-home/coach-home'
    })
  }
})
