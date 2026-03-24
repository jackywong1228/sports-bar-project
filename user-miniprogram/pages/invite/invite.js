const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    stats: { used: 0, limit: 0, remaining: 0, month: '' },
    history: [],
    currentCode: '',
    generating: false,
    loading: true
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    this.loadData()
  },

  async loadData() {
    try {
      const [statsRes, historyRes] = await Promise.all([
        api.getInviteStats(),
        api.getInviteHistory()
      ])
      this.setData({
        stats: statsRes.data || { used: 0, limit: 0, remaining: 0 },
        history: (historyRes.data && historyRes.data.items) || [],
        loading: false
      })
    } catch (err) {
      console.error('加载邀请数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 生成邀请码
  async generateCode() {
    if (this.data.generating) return
    if (this.data.stats.remaining <= 0) {
      wx.showToast({ title: '本月邀请次数已用完', icon: 'none' })
      return
    }

    this.setData({ generating: true })
    try {
      const res = await api.generateInviteCode()
      if (res.code === 200 && res.data && res.data.success) {
        this.setData({
          currentCode: res.data.invite_code,
          'stats.remaining': res.data.remaining
        })
        wx.showToast({ title: '邀请码已生成', icon: 'success' })
        this.loadData()
      } else {
        wx.showToast({ title: res.message || '生成失败', icon: 'none' })
      }
    } catch (err) {
      wx.showToast({ title: '生成失败', icon: 'none' })
    }
    this.setData({ generating: false })
  },

  // 复制邀请码
  copyCode() {
    if (!this.data.currentCode) return
    wx.setClipboardData({
      data: this.data.currentCode,
      success: () => {
        wx.showToast({ title: '已复制', icon: 'success' })
      }
    })
  },

  // 分享给朋友
  onShareAppMessage() {
    const code = this.data.currentCode
    return {
      title: '我在云里坊等你，快来加入吧！',
      path: `/pages/invite/accept?code=${code}`,
      imageUrl: ''
    }
  }
})
