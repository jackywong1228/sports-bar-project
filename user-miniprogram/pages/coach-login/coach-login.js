const app = getApp()
const api = require('../../utils/api')
const coachApi = require('../../utils/coach-api')
const wxApi = require('../../utils/wx-api')

Page({
  data: {
    phone: '',
    isLoading: false,
    checkingStatus: true  // 是否正在检查教练状态
  },

  onLoad() {
    // 检查是否已登录教练
    const coachToken = wx.getStorageSync('coach_token')
    if (coachToken) {
      wx.redirectTo({
        url: '/pages/coach-home/coach-home'
      })
      return
    }

    // 检查用户是否已登录
    if (!app.globalData.token) {
      wx.showToast({
        title: '请先登录用户账号',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateTo({
          url: '/pages/login/login'
        })
      }, 1500)
      return
    }

    // 检查是否已是教练
    this.checkCoachStatus()
  },

  // 检查教练状态
  async checkCoachStatus() {
    try {
      const res = await api.getCoachApplyStatus()
      const data = res.data

      this.setData({ checkingStatus: false })

      if (data.is_coach) {
        // 已是教练，尝试用微信登录获取教练token
        this.wxLogin()
      } else if (data.status === 'none' || data.status === 'rejected') {
        // 未申请或被拒绝，跳转到申请页面
        wx.redirectTo({
          url: '/pages/coach-apply/coach-apply'
        })
      } else if (data.status === 'pending') {
        // 申请中
        wx.showModal({
          title: '申请审核中',
          content: '您的教练申请正在审核中，请耐心等待',
          showCancel: false,
          success: () => {
            wx.navigateBack()
          }
        })
      }
    } catch (err) {
      console.error('检查教练状态失败:', err)
      this.setData({ checkingStatus: false })
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
      const res = await coachApi.loginByPhone(this.data.phone)
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
      const res = await coachApi.wxLogin(loginRes.code)
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
    if (app.globalData.coachToken) {
      this.setData({ isLoading: true })

      try {
        const res = await coachApi.getPhoneNumber(e.detail.code)
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
    app.globalData.coachToken = data.access_token
    app.globalData.coachInfo = {
      id: data.coach_id,
      name: data.name,
      avatar: data.avatar
    }

    wxApi.showToast('登录成功', 'success')

    setTimeout(() => {
      wx.redirectTo({
        url: '/pages/coach-home/coach-home'
      })
    }, 1000)
  }
})
