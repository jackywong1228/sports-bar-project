const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    currentTab: 'user',
    promoteStats: {},
    promoteRecords: []
  },

  onLoad(options) {
    this.setData({
      currentTab: options.type || 'user'
    })
    this.loadPromoteData()
    this.generateQRCode()
  },

  // 切换标签
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ currentTab: tab })
    this.loadPromoteData()
    this.generateQRCode()
  },

  // 加载推广数据
  async loadPromoteData() {
    try {
      const { currentTab } = this.data
      const res = await app.coachRequest({
        url: `/coach/promote/stats?type=${currentTab}`
      })
      this.setData({ promoteStats: res.data || {} })

      // 加载推广记录
      const recordRes = await app.coachRequest({
        url: `/coach/promote/records?type=${currentTab}`
      })

      const records = (recordRes.data || []).map(item => ({
        ...item,
        created_at: util.formatDate(item.created_at, 'YYYY-MM-DD')
      }))
      this.setData({ promoteRecords: records })
    } catch (err) {
      console.error('加载推广数据失败:', err)
    }
  },

  // 生成推广二维码
  generateQRCode() {
    const { currentTab } = this.data
    const coachInfo = app.globalData.coachInfo || {}

    // 简单的占位实现
    const ctx = wx.createCanvasContext('promoteQrcode')
    ctx.setFillStyle('#fff')
    ctx.fillRect(0, 0, 160, 160)

    // 绘制简单的二维码占位
    ctx.setFillStyle('#333')
    for (let i = 0; i < 8; i++) {
      for (let j = 0; j < 8; j++) {
        if (Math.random() > 0.5) {
          ctx.fillRect(10 + i * 17, 10 + j * 17, 15, 15)
        }
      }
    }

    // 绘制中心图标
    ctx.setFillStyle(currentTab === 'coach' ? '#1890ff' : '#52c41a')
    ctx.fillRect(60, 60, 40, 40)
    ctx.setFillStyle('#fff')
    ctx.setFontSize(10)
    ctx.setTextAlign('center')
    ctx.fillText(currentTab === 'coach' ? '教练' : '用户', 80, 85)

    ctx.draw()
  },

  // 保存二维码
  saveQrcode() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  },

  // 分享推广
  shareQrcode() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  },

  // 分享给朋友
  onShareAppMessage() {
    const { currentTab } = this.data
    const coachInfo = app.globalData.coachInfo || {}

    return {
      title: currentTab === 'coach' ? '邀请您加入教练团队' : '邀请您体验场馆服务',
      path: `/pages/coach-home/coach-home?invite_code=${coachInfo.invite_code}&type=${currentTab}`
    }
  }
})
