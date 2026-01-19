const app = getApp()

Page({
  data: {
    coachTypes: [
      { id: '', name: '全部' },
      { id: 'technical', name: '技术教练' },
      { id: 'entertainment', name: '娱乐教练' }
    ],
    currentType: '',
    coaches: [],
    loading: true,
    page: 1,
    hasMore: true
  },

  onLoad() {
    this.loadCoaches()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, hasMore: true })
    this.loadCoaches().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // 切换类型
  switchType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({
      currentType: type,
      page: 1,
      hasMore: true,
      coaches: []
    })
    this.loadCoaches()
  },

  // 加载教练列表
  async loadCoaches() {
    this.setData({ loading: true })

    try {
      let url = `/member/coaches?page=${this.data.page}&limit=10`
      if (this.data.currentType) {
        url += `&type=${this.data.currentType}`
      }

      const res = await app.coachRequest({ url })
      const coaches = res.data || []

      this.setData({
        coaches: this.data.page === 1 ? coaches : [...this.data.coaches, ...coaches],
        hasMore: coaches.length >= 10,
        loading: false
      })
    } catch (err) {
      console.error('加载教练失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载更多
  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadCoaches()
  },

  // 跳转详情
  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/coach-detail/coach-detail?id=${id}`
    })
  }
})
