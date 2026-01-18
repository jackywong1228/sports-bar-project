const app = getApp()
const api = require('../../utils/api')
const wxApi = require('../../utils/wx-api')

Page({
  data: {
    phone: '',
    isLoading: false
  },

  onLoad() {
    // 检查是否已登录
    const token = wx.getStorageSync('coach_token')
    if (token) {
      wx.switchTab({
        url: '/pages/index/index'
      })
    }
  },

  // 输入手机号
  onPhoneInput(e) {
    this.setData({
      phone: e.detail.value
    })
  },

  // 手机号登录（开发测试用）
  async loginByPhone() {
    if (!this.data.phone) {
      wxApi.showToast('请输入手机号')
      return
    }

    if (!/^1[3-9]\d{9}$/.test(this.data.phone)) {
      wxApi.showToast('请输入正确的手机号')
      return
    }

    this.setData({ isLoading: true })

    try {
      // 直接用手机号登录（后端会查找对应的教练）
      const res = await api.loginByPhone(this.data.phone)
      this.handleLoginSuccess(res.data)
    } catch (err) {
      wxApi.showToast(err.message || '登录失败')
    } finally {
      this.setData({ isLoading: false })
    }
  },

  // 微信一键登录
  async wxLogin() {
    this.setData({ isLoading: true })

    try {
      // 获取微信登录code
      const loginRes = await wxApi.login()

      if (!loginRes.code) {
        wxApi.showToast('微信登录失败')
        return
      }

      // 调用后端接口
      const res = await api.wxLogin(loginRes.code)
      this.handleLoginSuccess(res.data)

    } catch (err) {
      console.error('微信登录失败:', err)

      // 特殊处理：如果是未注册会员或未成为教练的提示
      if (err.message && (err.message.includes('会员') || err.message.includes('教练'))) {
        wx.showModal({
          title: '提示',
          content: err.message,
          showCancel: false
        })
      } else {
        wxApi.showToast(err.message || '登录失败')
      }
    } finally {
      this.setData({ isLoading: false })
    }
  },

  // 获取手机号（绑定手机号使用）
  async getPhoneNumber(e) {
    if (!e.detail.code) {
      wxApi.showToast('获取手机号失败')
      return
    }

    // 如果已经登录，直接绑定手机号
    if (app.globalData.token) {
      this.setData({ isLoading: true })

      try {
        const res = await api.getPhoneNumber(e.detail.code)
        app.globalData.coachInfo.phone = res.data.phone

        wxApi.showToast('绑定成功', 'success')
      } catch (err) {
        wxApi.showToast(err.message || '绑定失败')
      } finally {
        this.setData({ isLoading: false })
      }
    }
  },

  // 处理登录成功
  handleLoginSuccess(data) {
    wx.setStorageSync('coach_token', data.access_token)
    app.globalData.token = data.access_token
    app.globalData.coachInfo = {
      id: data.coach_id,
      name: data.name,
      avatar: data.avatar
    }

    wxApi.showToast('登录成功', 'success')

    setTimeout(() => {
      wx.switchTab({
        url: '/pages/index/index'
      })
    }, 1000)
  }
})
