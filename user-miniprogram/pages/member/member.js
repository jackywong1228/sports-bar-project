const app = getApp()
Page({
  data: { memberInfo: {}, cards: [] },
  onLoad() { this.loadData() },
  async loadData() {
    try {
      const [memberRes, cardsRes] = await Promise.all([
        app.request({ url: '/member/profile' }),
        app.request({ url: '/member/cards' })
      ])
      this.setData({ memberInfo: memberRes.data || {}, cards: cardsRes.data || [] })
    } catch (err) { console.error(err) }
  },
  buyCard(e) {
    wx.showToast({ title: '功能开发中', icon: 'none' })
  }
})
