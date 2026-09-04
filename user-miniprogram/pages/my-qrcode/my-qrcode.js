const app = getApp()
const api = require('../../utils/api')
const { drawQRCode } = require('../../utils/qrcode')

const REFRESH_INTERVAL_MS = 100000  // 100s 提前刷新（后端短码寿命 120s）
const QR_LIFETIME_S = 120

Page({
  data: {
    member: {},
    avatarLetter: '会',
    themeColor: '#1A5D3A',
    themeGradient: 'linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%)',
    themeName: '会员',
    qrReady: false,
    countdownPercent: 100,
    countdownText: '120秒',
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
      wx.showModal({
        title: '提示',
        content: '查看会员码需要登录，是否前往登录？',
        confirmText: '去登录',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' })
          } else {
            wx.navigateBack()
          }
        }
      })
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
    const nick = (member.nickname || '').trim()
    const avatarLetter = nick ? nick.charAt(0) : '会'
    this.setData({
      member,
      avatarLetter,
      themeColor: themeConfig.primary,
      themeGradient: themeConfig.gradient,
      themeName: themeConfig.name,
    })
  },

  reportError(key) {
    // 线上错误上报：优先 reportMonitor（需在微信后台配置），失败则静默
    try {
      if (wx.reportMonitor) wx.reportMonitor(key, 1)
    } catch (_) { /* 静默 */ }
  },

  async refreshQrCode() {
    if (!this.pageActive) return
    try {
      this.setData({ errorMsg: '' })
      const res = await api.getMemberQrToken()
      // 新版后端返回 8 位短码 code；|| token 兜底兼容旧版 JWT 响应
      const code = res && res.data && (res.data.code || res.data.token)
      if (!code) {
        this.setData({ errorMsg: '获取二维码失败' })
        return
      }
      this.qrGeneratedAt = Date.now()
      this.setData({
        countdownPercent: 100,
        countdownText: QR_LIFETIME_S + '秒',
      })
      this.drawQR('MEMBER:' + code)
    } catch (_err) {
      // 401 已由 app.request 统一处理（清除 token 并提示）
      this.reportError('qrcode_refresh_fail')
      this.setData({ errorMsg: '刷新二维码失败，请检查网络或重新登录' })
    }
  },

  drawQR(content) {
    const query = this.createSelectorQuery()
    query.select('#qrCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res || !res[0] || !res[0].node) {
          this.reportError('qrcode_canvas_missing')
          return
        }
        const canvas = res[0].node
        const canvasWidth = res[0].width || 300
        try {
          // 码本身强制纯黑保证对比度（会员等级主题色只用于卡片装饰），
          // margin 32 ≈ 4 个模块宽度的安全留白
          drawQRCode(canvas, content, canvasWidth, {
            foreground: '#000000',
            background: '#FFFFFF',
            margin: 32,
          })
          this.setData({ qrReady: true })
        } catch (_err) {
          this.reportError('qrcode_generate_fail')
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
