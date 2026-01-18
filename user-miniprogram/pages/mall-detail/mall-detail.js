const app = getApp()
Page({
  data: { id: null, goods: {} },
  onLoad(options) { this.setData({ id: options.id }); this.loadDetail() },
  async loadDetail() {
    try {
      const res = await app.request({ url: `/member/mall/goods/${this.data.id}` })
      this.setData({ goods: res.data || {} })
    } catch (err) { console.error(err) }
  },
  async exchange() {
    if (!app.checkLogin()) return
    try {
      await app.request({ url: `/member/mall/goods/${this.data.id}/exchange`, method: 'POST' })
      wx.showToast({ title: '兑换成功', icon: 'success' })
    } catch (err) { console.error(err) }
  }
})
