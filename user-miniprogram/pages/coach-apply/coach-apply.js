const app = getApp()
const api = require('../../utils/api')
const wxApi = require('../../utils/wx-api')

Page({
  data: {
    name: '',
    phone: '',
    type: 'technical',
    introduction: '',
    isLoading: false,
    applyStatus: null,  // none, pending, approved, rejected
    statusMessage: ''
  },

  onLoad() {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.showToast({
        title: '请先登录',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
      return
    }

    // 预填手机号
    if (app.globalData.memberInfo && app.globalData.memberInfo.phone) {
      this.setData({
        phone: app.globalData.memberInfo.phone
      })
    }

    // 检查申请状态
    this.checkApplyStatus()
  },

  // 检查申请状态
  async checkApplyStatus() {
    try {
      const res = await api.getCoachApplyStatus()
      const data = res.data

      if (data.is_coach) {
        // 已是教练，跳转到教练首页
        wx.setStorageSync('coach_token', app.globalData.token)
        app.globalData.coachToken = app.globalData.token
        wx.redirectTo({
          url: '/pages/coach-home/coach-home'
        })
        return
      }

      this.setData({
        applyStatus: data.status,
        statusMessage: data.message
      })
    } catch (err) {
      console.error('检查申请状态失败:', err)
    }
  },

  // 输入姓名
  onNameInput(e) {
    this.setData({ name: e.detail.value })
  },

  // 输入手机号
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  // 输入介绍
  onIntroInput(e) {
    this.setData({ introduction: e.detail.value })
  },

  // 选择类型
  onTypeChange(e) {
    this.setData({ type: e.detail.value })
  },

  // 提交申请
  async submitApply() {
    const { name, phone, type, introduction } = this.data

    if (!name.trim()) {
      wxApi.showToast('请输入姓名')
      return
    }

    if (!phone) {
      wxApi.showToast('请输入手机号')
      return
    }

    if (!/^1[3-9]\d{9}$/.test(phone)) {
      wxApi.showToast('请输入正确的手机号')
      return
    }

    this.setData({ isLoading: true })

    try {
      await api.applyForCoach({
        name: name.trim(),
        phone,
        type,
        introduction: introduction.trim()
      })

      wx.showModal({
        title: '提交成功',
        content: '您的申请已提交，请等待审核通过后即可使用教练功能',
        showCancel: false,
        success: () => {
          this.checkApplyStatus()
        }
      })
    } catch (err) {
      wxApi.showToast(err.message || '提交失败')
    } finally {
      this.setData({ isLoading: false })
    }
  },

  // 返回
  goBack() {
    wx.navigateBack()
  }
})
