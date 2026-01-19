const app = getApp()
const api = require('../../utils/api')
const wxApi = require('../../utils/wx-api')

Page({
  data: {
    phone: '',
    isLoading: false,
    needBindPhone: false  // 是否需要绑定手机号
  },

  onLoad(options) {
    // 检查是否已登录
    if (app.globalData.token) {
      wx.navigateBack()
    }
  },

  // 输入手机号
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
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
      wxApi.showToast(err.message || '登录失败')
    } finally {
      this.setData({ isLoading: false })
    }
  },

  // 获取手机号（新用户绑定手机号使用）
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
        app.globalData.memberInfo.phone = res.data.phone

        wxApi.showToast('绑定成功', 'success')
        setTimeout(() => {
          wx.navigateBack()
        }, 1000)
      } catch (err) {
        wxApi.showToast(err.message || '绑定失败')
      } finally {
        this.setData({ isLoading: false })
      }
    } else {
      // 先微信登录再绑定手机号
      this.wxLoginThenBindPhone(e.detail.code)
    }
  },

  // 微信登录后绑定手机号
  async wxLoginThenBindPhone(phoneCode) {
    this.setData({ isLoading: true })

    try {
      // 先微信登录
      const loginRes = await wxApi.login()

      if (!loginRes.code) {
        wxApi.showToast('微信登录失败')
        return
      }

      const res = await api.wxLogin(loginRes.code)
      this.handleLoginSuccess(res.data, false)  // 不跳转

      // 再绑定手机号
      const phoneRes = await api.getPhoneNumber(phoneCode)
      app.globalData.memberInfo.phone = phoneRes.data.phone

      wxApi.showToast('登录成功', 'success')
      setTimeout(() => {
        wx.navigateBack()
      }, 1000)

    } catch (err) {
      console.error('登录失败:', err)
      wxApi.showToast(err.message || '登录失败')
    } finally {
      this.setData({ isLoading: false })
    }
  },

  // 处理登录成功
  handleLoginSuccess(data, navigate = true) {
    wx.setStorageSync('token', data.access_token)
    app.globalData.token = data.access_token
    app.globalData.memberInfo = data.member_info

    // 新用户可能需要绑定手机号
    if (data.is_new_user && !data.member_info.phone) {
      this.setData({ needBindPhone: true })
      return
    }

    if (navigate) {
      wxApi.showToast('登录成功', 'success')
      setTimeout(() => {
        wx.navigateBack()
      }, 1000)
    }
  },

  // 跳过绑定手机号
  skipBindPhone() {
    wxApi.showToast('登录成功', 'success')
    setTimeout(() => {
      wx.navigateBack()
    }, 1000)
  }
})
