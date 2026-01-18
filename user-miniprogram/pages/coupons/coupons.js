const app = getApp()
Page({
  data: { coupons: [], loading: true },
  onLoad() { this.loadCoupons() },
  async loadCoupons() {
    try {
      const res = await app.request({ url: '/member/coupons' })
      this.setData({ coupons: res.data || [], loading: false })
    } catch (err) { this.setData({ loading: false }) }
  }
})
