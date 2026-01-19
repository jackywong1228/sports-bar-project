const app = getApp()

Page({
  data: {
    coachId: null,
    coach: {},
    loading: true
  },

  onLoad(options) {
    this.setData({ coachId: options.id })
    this.loadCoachDetail()
  },

  // 加载教练详情
  async loadCoachDetail() {
    try {
      const res = await app.coachRequest({
        url: `/member/coaches/${this.data.coachId}`
      })
      this.setData({
        coach: res.data || {},
        loading: false
      })
    } catch (err) {
      console.error('加载教练详情失败:', err)
      this.setData({ loading: false })
    }
  },

  // 预览图片
  previewImage(e) {
    const current = e.currentTarget.dataset.src
    const photos = this.data.coach.photos || []
    wx.previewImage({
      current,
      urls: photos
    })
  },

  // 立即预约
  goToBooking() {
    if (!app.checkCoachLogin()) return
    wx.navigateTo({
      url: `/pages/coach-booking/coach-booking?id=${this.data.coachId}`
    })
  },

  // 分享
  onShareAppMessage() {
    return {
      title: `${this.data.coach.name} - 专业教练预约`,
      path: `/pages/coach-detail/coach-detail?id=${this.data.coachId}`
    }
  }
})
