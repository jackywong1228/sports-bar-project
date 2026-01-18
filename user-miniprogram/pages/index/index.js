const app = getApp()

Page({
  data: {
    banners: [],
    quickEntries: [
      { icon: '/assets/icons/venue-entry.png', text: '场馆预约', url: '/pages/venue/venue' },
      { icon: '/assets/icons/coach-entry.png', text: '教练预约', url: '/pages/coach-list/coach-list' },
      { icon: '/assets/icons/food-entry.png', text: '在线点餐', url: '/pages/food/food' },
      { icon: '/assets/icons/activity-entry.png', text: '活动报名', url: '/pages/activity/activity' },
      { icon: '/assets/icons/team-entry.png', text: '组队广场', url: '/pages/team/team' },
      { icon: '/assets/icons/mall-entry.png', text: '积分商城', url: '/pages/mall/mall' },
      { icon: '/assets/icons/member-entry.png', text: '会员中心', url: '/pages/member/member' },
      { icon: '/assets/icons/coupon-entry.png', text: '我的券包', url: '/pages/coupons/coupons' }
    ],
    hotVenues: [],
    hotActivities: [],
    hotCoaches: [],
    loading: true
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    // 更新会员信息
    if (app.globalData.token) {
      app.getMemberInfo()
    }
  },

  onPullDownRefresh() {
    this.loadData().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载数据
  async loadData() {
    this.setData({ loading: true })

    try {
      // 并行加载多个数据
      const [bannersRes, venuesRes, activitiesRes, coachesRes] = await Promise.all([
        this.loadBanners(),
        this.loadHotVenues(),
        this.loadHotActivities(),
        this.loadHotCoaches()
      ])

      this.setData({
        banners: bannersRes || [],
        hotVenues: venuesRes || [],
        hotActivities: activitiesRes || [],
        hotCoaches: coachesRes || [],
        loading: false
      })
    } catch (err) {
      console.error('加载数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载轮播图
  async loadBanners() {
    try {
      const res = await app.request({ url: '/member/banners' })
      return res.data || []
    } catch (err) {
      // 使用默认数据
      return [
        { id: 1, image: '/assets/images/banner1.jpg', url: '' },
        { id: 2, image: '/assets/images/banner2.jpg', url: '' }
      ]
    }
  },

  // 加载热门场馆
  async loadHotVenues() {
    try {
      const res = await app.request({ url: '/member/venues?limit=4' })
      return res.data || []
    } catch (err) {
      return []
    }
  },

  // 加载热门活动
  async loadHotActivities() {
    try {
      const res = await app.request({ url: '/member/activities?limit=3' })
      return res.data || []
    } catch (err) {
      return []
    }
  },

  // 加载热门教练
  async loadHotCoaches() {
    try {
      const res = await app.request({ url: '/member/coaches?limit=4' })
      return res.data || []
    } catch (err) {
      return []
    }
  },

  // 轮播图点击
  onBannerTap(e) {
    const url = e.currentTarget.dataset.url
    if (url) {
      wx.navigateTo({ url })
    }
  },

  // 快捷入口点击
  onEntryTap(e) {
    const url = e.currentTarget.dataset.url
    if (url.includes('/pages/profile/') || url.includes('/pages/member/') || url.includes('/pages/coupons/')) {
      if (!app.checkLogin()) return
    }
    if (url.startsWith('/pages/venue/') || url.startsWith('/pages/activity/')) {
      wx.switchTab({ url })
    } else {
      wx.navigateTo({ url })
    }
  },

  // 查看更多场馆
  viewMoreVenues() {
    wx.switchTab({
      url: '/pages/venue/venue'
    })
  },

  // 查看更多活动
  viewMoreActivities() {
    wx.switchTab({
      url: '/pages/activity/activity'
    })
  },

  // 查看更多教练
  viewMoreCoaches() {
    wx.navigateTo({
      url: '/pages/coach-list/coach-list'
    })
  },

  // 场馆详情
  goToVenueDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/venue-detail/venue-detail?id=${id}`
    })
  },

  // 活动详情
  goToActivityDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/activity-detail/activity-detail?id=${id}`
    })
  },

  // 教练详情
  goToCoachDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/coach-detail/coach-detail?id=${id}`
    })
  }
})
