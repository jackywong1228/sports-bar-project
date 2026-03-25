const app = getApp()

Page({
  data: {
    tabs: [
      { key: 'all', name: '全部' },
      { key: 'created', name: '我创建的' },
      { key: 'joined', name: '我参加的' }
    ],
    currentTab: 'all',
    teams: [],
    loading: false,
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: true
  },

  onLoad() {
    this.loadTeams()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, teams: [], hasMore: true })
    this.loadTeams().then(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadTeams()
    }
  },

  switchTab(e) {
    const key = e.currentTarget.dataset.key
    if (key === this.data.currentTab) return
    this.setData({
      currentTab: key,
      page: 1,
      teams: [],
      hasMore: true
    })
    this.loadTeams()
  },

  async loadTeams() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const res = await app.request({
        url: '/member/my-teams',
        data: {
          role: this.data.currentTab,
          page: this.data.page,
          page_size: this.data.pageSize
        },
        showError: false
      })

      if (res.code === 200) {
        const newTeams = res.data.list || []
        const allTeams = this.data.page === 1 ? newTeams : [...this.data.teams, ...newTeams]
        this.setData({
          teams: allTeams,
          total: res.data.total,
          hasMore: allTeams.length < res.data.total,
          page: this.data.page + 1
        })
      }
    } catch (err) {
      console.error('加载我的组队失败:', err)
    } finally {
      this.setData({ loading: false })
    }
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/team-detail/team-detail?id=${id}` })
  },

  goToTeamSquare() {
    wx.navigateTo({ url: '/pages/team/team' })
  }
})
