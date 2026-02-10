const app = getApp()
const api = require('../../utils/api')
const wxApi = require('../../utils/wx-api')
const { upload } = require('../../utils/request')

Page({
  data: {
    phone: '',
    isLoading: false,
    needBindPhone: false,
    needCompleteProfile: false,
    tempAvatar: '',
    tempNickname: '',
    isSaving: false
  },

  onLoad(options) {
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
      const loginRes = await wxApi.login()

      if (!loginRes.code) {
        wxApi.showToast('微信登录失败')
        return
      }

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
      this.wxLoginThenBindPhone(e.detail.code)
    }
  },

  // 微信登录后绑定手机号
  async wxLoginThenBindPhone(phoneCode) {
    this.setData({ isLoading: true })

    try {
      const loginRes = await wxApi.login()

      if (!loginRes.code) {
        wxApi.showToast('微信登录失败')
        return
      }

      const res = await api.wxLogin(loginRes.code)
      this.handleLoginSuccess(res.data, false)

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
    if (data.openid) {
      app.globalData.openid = data.openid
      wx.setStorageSync('openid', data.openid)
    }

    // 新用户可能需要绑定手机号
    if (data.is_new_user && !data.member_info.phone) {
      this.setData({ needBindPhone: true })
      return
    }

    // 检查是否需要完善资料（昵称为默认值）
    const nickname = data.member_info.nickname || ''
    if (nickname === '微信用户' || nickname.startsWith('用户')) {
      this.setData({ needCompleteProfile: true })
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
  },

  // ==================== 完善资料相关 ====================

  // 选择头像回调
  onChooseAvatar(e) {
    const tempFilePath = e.detail.avatarUrl
    this.setData({ tempAvatar: tempFilePath })
  },

  // 昵称输入回调
  onNicknameChange(e) {
    this.setData({ tempNickname: e.detail.value })
  },

  // 保存资料
  async saveProfile() {
    const { tempAvatar, tempNickname } = this.data

    if (!tempAvatar && !tempNickname) {
      wxApi.showToast('请至少设置头像或昵称')
      return
    }

    this.setData({ isSaving: true })

    try {
      let avatarUrl = ''

      // 上传头像
      if (tempAvatar) {
        const uploadRes = await upload('/upload/member-image', tempAvatar, 'file')
        if (uploadRes.data && uploadRes.data.url) {
          avatarUrl = uploadRes.data.url
        }
      }

      // 更新资料到后端
      const profileData = {}
      if (avatarUrl) {
        profileData.avatar = avatarUrl
      }
      if (tempNickname) {
        profileData.nickname = tempNickname
      }

      if (Object.keys(profileData).length > 0) {
        await api.updateUserProfile(profileData)

        // 更新本地缓存
        if (app.globalData.memberInfo) {
          if (profileData.avatar) {
            app.globalData.memberInfo.avatar = profileData.avatar
          }
          if (profileData.nickname) {
            app.globalData.memberInfo.nickname = profileData.nickname
          }
        }
      }

      wxApi.showToast('保存成功', 'success')
      setTimeout(() => {
        wx.navigateBack()
      }, 1000)

    } catch (err) {
      console.error('保存资料失败:', err)
      wxApi.showToast(err.message || '保存失败')
    } finally {
      this.setData({ isSaving: false })
    }
  },

  // 跳过完善资料
  skipProfile() {
    wxApi.showToast('登录成功', 'success')
    setTimeout(() => {
      wx.navigateBack()
    }, 1000)
  }
})
