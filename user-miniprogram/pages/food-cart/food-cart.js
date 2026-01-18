const app = getApp()
Page({
  data: { cart: [], total: 0 },
  onLoad() {
    const cart = wx.getStorageSync('foodCart') || []
    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    this.setData({ cart, total })
  },
  updateQuantity(e) {
    const { id, action } = e.currentTarget.dataset
    let cart = [...this.data.cart]
    const index = cart.findIndex(c => c.id === id)
    if (index > -1) {
      if (action === 'add') cart[index].quantity++
      else if (action === 'minus') {
        cart[index].quantity--
        if (cart[index].quantity <= 0) cart.splice(index, 1)
      }
    }
    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    this.setData({ cart, total })
    wx.setStorageSync('foodCart', cart)
  },
  submitOrder() {
    if (!app.checkLogin()) return
    wx.navigateTo({ url: '/pages/food-order/food-order' })
  }
})
