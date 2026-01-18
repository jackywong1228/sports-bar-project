const app = getApp()

Page({
  data: {
    categories: [],
    currentCategory: 0,
    foods: [],
    cart: [],
    cartTotal: 0,
    loading: true
  },

  onLoad() {
    this.loadCategories()
    this.loadFoods()
  },

  async loadCategories() {
    try {
      const res = await app.request({ url: '/member/food-categories' })
      this.setData({ categories: [{ id: 0, name: '全部' }, ...(res.data || [])] })
    } catch (err) {
      this.setData({ categories: [{ id: 0, name: '全部' }] })
    }
  },

  async loadFoods() {
    this.setData({ loading: true })
    try {
      let url = '/member/foods'
      if (this.data.currentCategory > 0) {
        url += `?category_id=${this.data.currentCategory}`
      }
      const res = await app.request({ url })
      this.setData({ foods: res.data || [], loading: false })
    } catch (err) {
      this.setData({ loading: false })
    }
  },

  switchCategory(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ currentCategory: id })
    this.loadFoods()
  },

  addToCart(e) {
    const id = e.currentTarget.dataset.id
    const food = this.data.foods.find(f => f.id === id)
    if (!food) return

    let cart = [...this.data.cart]
    const index = cart.findIndex(c => c.id === id)
    if (index > -1) {
      cart[index].quantity++
    } else {
      cart.push({ ...food, quantity: 1 })
    }

    const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    this.setData({ cart, cartTotal })
  },

  goToCart() {
    if (this.data.cart.length === 0) {
      wx.showToast({ title: '购物车是空的', icon: 'none' })
      return
    }
    wx.setStorageSync('foodCart', this.data.cart)
    wx.navigateTo({ url: '/pages/food-cart/food-cart' })
  }
})
