const app = getApp()

Page({
  data: {
    currentTab: 'coin',
    memberInfo: {},
    records: [],
    loading: true,
    page: 1,
    hasMore: true
  },

  onLoad(options) {
    if (options.type) {
      this.setData({ currentTab: options.type })
    }
    this.loadMemberInfo()
    this.loadRecords()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, hasMore: true })
    this.loadRecords().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // 加载会员信息
  async loadMemberInfo() {
    try {
      const res = await app.request({ url: '/member/profile' })
      this.setData({ memberInfo: res.data || {} })
    } catch (err) {
      console.error('加载会员信息失败:', err)
    }
  },

  // 切换标签
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({
      currentTab: tab,
      page: 1,
      hasMore: true,
      records: []
    })
    this.loadRecords()
  },

  // 加载记录
  async loadRecords() {
    this.setData({ loading: true })

    try {
      const { currentTab, page } = this.data
      const url = `/member/${currentTab}-records?page=${page}&limit=20`
      const res = await app.request({ url })
      const records = res.data || []

      this.setData({
        records: page === 1 ? records : [...this.data.records, ...records],
        hasMore: records.length >= 20,
        loading: false
      })
    } catch (err) {
      console.error('加载记录失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载更多
  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadRecords()
  },

  // 去充值
  goToRecharge() {
    wx.navigateTo({
      url: '/pages/recharge/recharge'
    })
  }
})
