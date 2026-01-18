const app = getApp()

Page({
  data: {
    venueId: null,
    venue: {},
    loading: true
  },

  onLoad(options) {
    this.setData({ venueId: options.id })
    this.loadVenueDetail()
  },

  // 加载场馆详情
  async loadVenueDetail() {
    try {
      const res = await app.request({
        url: `/member/venues/${this.data.venueId}`
      })
      this.setData({
        venue: res.data || {},
        loading: false
      })
    } catch (err) {
      console.error('加载场馆详情失败:', err)
      this.setData({ loading: false })
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      })
    }
  },

  // 预览图片
  previewImage(e) {
    const current = e.currentTarget.dataset.src
    const photos = this.data.venue.photos || []
    wx.previewImage({
      current,
      urls: photos
    })
  },

  // 拨打电话
  callPhone() {
    const phone = this.data.venue.phone
    if (phone) {
      wx.makePhoneCall({ phoneNumber: phone })
    } else {
      wx.showToast({
        title: '暂无联系电话',
        icon: 'none'
      })
    }
  },

  // 导航到场馆
  navigateTo() {
    const { latitude, longitude, name, address } = this.data.venue
    if (latitude && longitude) {
      wx.openLocation({
        latitude: Number(latitude),
        longitude: Number(longitude),
        name: name,
        address: address
      })
    } else {
      wx.showToast({
        title: '暂无位置信息',
        icon: 'none'
      })
    }
  },

  // 立即预约
  goToBooking() {
    if (!app.checkLogin()) return
    wx.navigateTo({
      url: `/pages/venue-booking/venue-booking?id=${this.data.venueId}`
    })
  },

  // 分享
  onShareAppMessage() {
    return {
      title: this.data.venue.name || '场馆预约',
      path: `/pages/venue-detail/venue-detail?id=${this.data.venueId}`
    }
  }
})
