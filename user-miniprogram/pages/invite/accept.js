const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    code: '',
    // 状态: loading / success / error
    status: 'loading',
    inviterName: '',
    message: '',
    errorMsg: ''
  },

  // 防止重复调用
  _accepted: false,

  onLoad(options) {
    const code = options.code || ''
    if (!code) {
      this.setData({ status: 'error', errorMsg: '邀请码无效' })
      return
    }
    this.setData({ code })

    if (app.globalData.token) {
      this.acceptInvite(code)
    } else {
      // 审核要求：带显式取消选项
      wx.showModal({
        title: '提示',
        content: '接受好友邀请需要登录，是否前往登录？',
        confirmText: '去登录',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({ url: '/pages/login/login' })
          } else {
            this.setData({
              status: 'error',
              errorMsg: '已取消登录，邀请未接受'
            })
          }
        }
      })
    }
  },

  onShow() {
    // 登录页返回后，检测是否已登录，自动使用邀请码
    if (app.globalData.token && !this._accepted && this.data.code) {
      this.acceptInvite(this.data.code)
    }
  },

  async acceptInvite(code) {
    if (this._accepted) return
    this._accepted = true
    this.setData({ status: 'loading' })

    try {
      const res = await api.useInviteCode(code)
      this.setData({
        status: 'success',
        inviterName: (res.data && res.data.inviter_name) || '',
        message: (res.data && res.data.message) || '邀请成功'
      })
    } catch (err) {
      this._accepted = false // 允许重试
      this.setData({
        status: 'error',
        errorMsg: (err && err.message) || '网络错误，请稍后重试'
      })
    }
  },

  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  goMember() {
    wx.navigateTo({ url: '/pages/member/member' })
  }
})
