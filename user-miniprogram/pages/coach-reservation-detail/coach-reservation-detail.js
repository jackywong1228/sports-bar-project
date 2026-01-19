const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    id: null,
    reservation: {}
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ id: options.id })
      this.loadReservation()
    }
  },

  // 加载预约详情
  async loadReservation() {
    try {
      wx.showLoading({ title: '加载中' })
      const res = await app.coachRequest({
        url: `/coach/reservations/${this.data.id}`
      })

      const data = res.data
      const status = util.getReservationStatus(data.status)

      this.setData({
        reservation: {
          ...data,
          statusText: status.text,
          date: util.formatDate(data.reservation_date, 'YYYY年MM月DD日'),
          start_time: util.formatTime(data.start_time),
          end_time: util.formatTime(data.end_time)
        }
      })

      // 生成完课码
      if (data.status === 'confirmed' || data.status === 'in_progress') {
        this.generateQRCode()
      }

      wx.hideLoading()
    } catch (err) {
      wx.hideLoading()
      console.error('加载预约详情失败:', err)
    }
  },

  // 生成完课码
  generateQRCode() {
    // 简单的占位实现，实际需要使用二维码库
    const ctx = wx.createCanvasContext('qrcode')
    ctx.setFillStyle('#f5f5f5')
    ctx.fillRect(0, 0, 200, 200)
    ctx.setFillStyle('#333')
    ctx.setFontSize(14)
    ctx.setTextAlign('center')
    ctx.fillText('完课码', 100, 100)
    ctx.fillText(`ID: ${this.data.id}`, 100, 120)
    ctx.draw()
  },

  // 拨打电话
  callPhone() {
    const phone = this.data.reservation.member_phone
    if (phone) {
      wx.makePhoneCall({
        phoneNumber: phone,
        fail: () => {
          wx.showToast({
            title: '拨打失败',
            icon: 'none'
          })
        }
      })
    }
  },

  // 确认预约
  async confirmReservation() {
    try {
      wx.showModal({
        title: '确认预约',
        content: '确定要接受这个预约吗？',
        success: async (res) => {
          if (res.confirm) {
            wx.showLoading({ title: '处理中' })
            await app.coachRequest({
              url: `/coach/reservations/${this.data.id}/confirm`,
              method: 'POST'
            })
            wx.hideLoading()
            wx.showToast({
              title: '已确认预约',
              icon: 'success'
            })
            this.loadReservation()
          }
        }
      })
    } catch (err) {
      wx.hideLoading()
      console.error('确认预约失败:', err)
    }
  },

  // 拒绝预约
  async rejectReservation() {
    try {
      wx.showModal({
        title: '拒绝预约',
        content: '确定要拒绝这个预约吗？费用将退还给学员。',
        success: async (res) => {
          if (res.confirm) {
            wx.showLoading({ title: '处理中' })
            await app.coachRequest({
              url: `/coach/reservations/${this.data.id}/reject`,
              method: 'POST'
            })
            wx.hideLoading()
            wx.showToast({
              title: '已拒绝预约',
              icon: 'success'
            })
            setTimeout(() => {
              wx.navigateBack()
            }, 1500)
          }
        }
      })
    } catch (err) {
      wx.hideLoading()
      console.error('拒绝预约失败:', err)
    }
  }
})
