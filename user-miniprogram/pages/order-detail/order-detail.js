const app = getApp()
Page({
  data: { id: null, order: {} },
  onLoad(options) { this.setData({ id: options.id }); this.loadDetail() },
  async loadDetail() {
    try {
      const res = await app.request({ url: `/member/orders/${this.data.id}` })
      this.setData({ order: res.data || {} })
    } catch (err) { console.error(err) }
  }
})
