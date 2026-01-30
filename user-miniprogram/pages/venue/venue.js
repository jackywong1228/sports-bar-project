const app = getApp()

Page({
  data: {
    venueTypes: [],
    currentType: 0,
    venues: [],
    loading: true,
    page: 1,
    hasMore: true
  },

  onLoad() {
    this.loadVenueTypes()
    this.loadVenues()
  },

  onShow() {
    // 刷新数据
  },

  onPullDownRefresh() {
    this.setData({ page: 1, hasMore: true })
    this.loadVenues().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // 加载场馆类型
  async loadVenueTypes() {
    console.log('[DEBUG] loadVenueTypes 开始')
    console.log('[DEBUG] baseUrl:', app.globalData.baseUrl)
    console.log('[DEBUG] 完整请求URL:', app.globalData.baseUrl + '/member/venue-types')

    try {
      const res = await app.request({ url: '/member/venue-types' })
      console.log('[DEBUG] loadVenueTypes 成功:', res)
      const types = [{ id: 0, name: '全部' }, ...(res.data || [])]
      this.setData({ venueTypes: types })
    } catch (err) {
      console.error('[DEBUG] loadVenueTypes 失败:', err)
      console.error('[DEBUG] 错误详情:', JSON.stringify(err))
      this.setData({
        venueTypes: [
          { id: 0, name: '全部' },
          { id: 1, name: '羽毛球' },
          { id: 2, name: '乒乓球' },
          { id: 3, name: '篮球' },
          { id: 4, name: '网球' }
        ]
      })
    }
  },

  // 切换类型
  switchType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      currentType: type,
      page: 1,
      hasMore: true,
      venues: []
    })
    this.loadVenues()
  },

  // 加载场馆列表
  async loadVenues() {
    this.setData({ loading: true })

    try {
      let url = `/member/venues?page=${this.data.page}&limit=10`
      if (this.data.currentType > 0) {
        url += `&type_id=${this.data.currentType}`
      }

      const res = await app.request({ url })
      const venues = res.data || []

      this.setData({
        venues: this.data.page === 1 ? venues : [...this.data.venues, ...venues],
        hasMore: venues.length >= 10,
        loading: false
      })
    } catch (err) {
      console.error('加载场馆失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载更多
  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadVenues()
  },

  // 跳转详情
  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/venue-detail/venue-detail?id=${id}`
    })
  },

  // 立即预约
  goToBooking(e) {
    const id = e.currentTarget.dataset.id
    if (!app.checkLogin()) return
    wx.navigateTo({
      url: `/pages/venue-booking/venue-booking?id=${id}`
    })
  }
})
