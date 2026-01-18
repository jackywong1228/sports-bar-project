const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    tabs: [
      { id: 'all', name: '全部' },
      { id: 'upcoming', name: '即将开始' },
      { id: 'ongoing', name: '进行中' },
      { id: 'ended', name: '已结束' }
    ],
    currentTab: 'all',
    activities: [],
    loading: true,
    page: 1,
    hasMore: true
  },

  onLoad() {
    this.loadActivities()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, hasMore: true })
    this.loadActivities().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadMore()
    }
  },

  // 切换标签
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({
      currentTab: tab,
      page: 1,
      hasMore: true,
      activities: []
    })
    this.loadActivities()
  },

  // 加载活动列表
  async loadActivities() {
    this.setData({ loading: true })

    try {
      let url = `/member/activities?page=${this.data.page}&limit=10`
      if (this.data.currentTab !== 'all') {
        url += `&status=${this.data.currentTab}`
      }

      const res = await app.request({ url })
      const activities = (res.data || []).map(item => ({
        ...item,
        statusInfo: this.getActivityStatus(item)
      }))

      this.setData({
        activities: this.data.page === 1 ? activities : [...this.data.activities, ...activities],
        hasMore: activities.length >= 10,
        loading: false
      })
    } catch (err) {
      console.error('加载活动失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载更多
  loadMore() {
    this.setData({ page: this.data.page + 1 })
    this.loadActivities()
  },

  // 获取活动状态
  getActivityStatus(activity) {
    const now = new Date()
    const startDate = new Date(`${activity.start_date} ${activity.start_time || '00:00'}`)
    const endDate = new Date(`${activity.end_date || activity.start_date} ${activity.end_time || '23:59'}`)

    if (now < startDate) {
      return { text: '即将开始', class: 'upcoming' }
    } else if (now > endDate) {
      return { text: '已结束', class: 'ended' }
    } else {
      return { text: '进行中', class: 'ongoing' }
    }
  },

  // 跳转详情
  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/activity-detail/activity-detail?id=${id}`
    })
  }
})
