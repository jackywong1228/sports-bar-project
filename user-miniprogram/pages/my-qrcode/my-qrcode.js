const app = getApp()
const api = require('../../utils/api')
const { drawQRCode } = require('../../utils/qrcode')

const REFRESH_INTERVAL_MS = 25000  // 25s 提前刷新（后端 token 寿命 30s）
const QR_LIFETIME_S = 30

Page({
  data: {
    member: {},
    themeColor: '#1A5D3A',
    themeGradient: 'linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%)',
    themeName: '会员',
    qrReady: false,
    countdownPercent: 100,
    countdownText: '30秒',
    errorMsg: '',
  },

  refreshTimer: null,
  countdownTimer: null,
  qrGeneratedAt: 0,
  pageActive: false,

  onLoad() {
    this.loadMemberInfo()
  },

  onShow() {
    if (!app.globalData.token) {
      wx.showToast({ title: '请先登录', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1000)
      return
    }
    this.pageActive = true
    this.loadMemberInfo()
    this.refreshQrCode()
    this.startTimers()
  },

  onHide() {
    this.pageActive = false
    this.stopAllTimers()
  },

  onUnload() {
    this.pageActive = false
    this.stopAllTimers()
  },

  loadMemberInfo() {
    const member = app.globalData.memberInfo || {}
    const levelCode = app.globalData.memberLevel || 'S'
    const themeConfig = (app.memberThemeConfig && app.memberThemeConfig[levelCode]) || {
      primary: '#1A5D3A',
      gradient: 'linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%)',
      name: '会员',
    }
    this.setData({
      member,
      themeColor: themeConfig.primary,
      themeGradient: themeConfig.gradient,
      themeName: themeConfig.name,
    })
  },

  async refreshQrCode() {
    if (!this.pageActive) return
    try {
      this.setData({ errorMsg: '' })
      const res = await api.getMemberQrToken()
      const token = res && res.data && res.data.token
      if (!token) {
        this.setData({ errorMsg: '获取二维码失败' })
        return
      }
      this.qrGeneratedAt = Date.now()
      this.setData({
        countdownPercent: 100,
        countdownText: QR_LIFETIME_S + '秒',
      })
      this.drawQR('MEMBER:' + token)
    } catch (err) {
      console.error('刷新二维码失败:', err)
      // 401 已由 app.request 统一处理（清除 token 并提示）
      this.setData({ errorMsg: '刷新二维码失败，请检查网络或重新登录' })
    }
  },

  drawQR(content) {
    const query = this.createSelectorQuery()
    query.select('#qrCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0] || !res[0].node) {
          console.error('Canvas node not found')
          return
        }
        const canvas = res[0].node
        const canvasWidth = res[0].width || 240
        try {
          drawQRCode(canvas, content, canvasWidth, {
            foreground: this.data.themeColor || '#1A5D3A',
            background: '#FFFFFF',
            margin: 8,
          })
          this.setData({ qrReady: true })
        } catch (err) {
          console.error('QR code generation failed:', err)
          this.setData({ errorMsg: '二维码生成失败' })
        }
      })
  },

  startTimers() {
    this.stopAllTimers()
    this.refreshTimer = setInterval(() => {
      this.refreshQrCode()
    }, REFRESH_INTERVAL_MS)
    this.countdownTimer = setInterval(() => {
      const elapsed = (Date.now() - this.qrGeneratedAt) / 1000
      const remain = Math.max(0, QR_LIFETIME_S - elapsed)
      this.setData({
        countdownPercent: Math.round((remain / QR_LIFETIME_S) * 100),
        countdownText: Math.ceil(remain) + '秒',
      })
    }, 200)
  },

  stopAllTimers() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
      this.refreshTimer = null
    }
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer)
      this.countdownTimer = null
    }
  },
})
