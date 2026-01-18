const app = getApp()
Page({
  data: { goods: [], loading: true },
  onLoad() { this.loadGoods() },
  async loadGoods() {
    try {
      const res = await app.request({ url: '/member/mall/goods' })
      this.setData({ goods: res.data || [], loading: false })
    } catch (err) { this.setData({ loading: false }) }
  },
  goToDetail(e) {
    wx.navigateTo({ url: `/pages/mall-detail/mall-detail?id=${e.currentTarget.dataset.id}` })
  }
})
