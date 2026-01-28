const app = getApp()
const uiConfig = require('../../utils/ui-config')

Page({
  data: {
    // Hero区域数据
    heroImage: '/assets/images/banner1.jpg', // 默认背景图（使用banner1作为备用）
    showScrollHint: true,

    // 公告数据
    announcements: [],

    // 原有数据
    banners: [],
    quickEntries: [],
    hotVenues: [],
    hotActivities: [],
    hotCoaches: [],
    loading: true,

    // UI配置相关
    visibleBlocks: ['banner', 'quick_entry', 'hot_venues', 'hot_activities', 'hot_coaches'],
    uiConfigLoaded: false
  },

  onLoad() {
    this.loadUIConfig()
  },

  onShow() {
    // 更新会员信息
    if (app.globalData.token) {
      app.getMemberInfo()
    }
  },

  onPullDownRefresh() {
    this.loadData(true).then(() => {
      wx.stopPullDownRefresh()
    })
  },

  onPageScroll(e) {
    // 滚动时隐藏下滑提示
    if (e.scrollTop > 50 && this.data.showScrollHint) {
      this.setData({ showScrollHint: false })
    }
  },

  // 加载UI配置
  async loadUIConfig() {
    try {
      const [blocksConfig, quickEntriesConfig] = await Promise.all([
        uiConfig.getVisibleBlocks('home'),
        uiConfig.getQuickEntries()
      ])

      // 转换快捷入口格式
      const quickEntries = quickEntriesConfig.map(item => ({
        icon: item.icon || '/assets/icons/default.png',
        text: item.title,
        url: item.link_value || '',
        linkType: item.link_type
      }))

      this.setData({
        visibleBlocks: blocksConfig.length > 0 ? blocksConfig : this.data.visibleBlocks,
        quickEntries: quickEntries.length > 0 ? quickEntries : this.getDefaultQuickEntries(),
        uiConfigLoaded: true
      })

      // 加载业务数据
      await this.loadData()
    } catch (err) {
      console.error('加载UI配置失败:', err)
      // 使用默认快捷入口
      this.setData({
        quickEntries: this.getDefaultQuickEntries(),
        uiConfigLoaded: true
      })
      await this.loadData()
    }
  },

  // 获取默认快捷入口
  getDefaultQuickEntries() {
    return [
      { icon: '/assets/icons/venue-entry.png', text: '场馆预约', url: '/pages/venue/venue', linkType: 'tab' },
      { icon: '/assets/icons/coach-entry.png', text: '教练预约', url: '/pages/coach-list/coach-list', linkType: 'page' },
      { icon: '/assets/icons/food-entry.png', text: '在线点餐', url: '/pages/food/food', linkType: 'page' },
      { icon: '/assets/icons/activity-entry.png', text: '活动报名', url: '/pages/activity/activity', linkType: 'tab' },
      { icon: '/assets/icons/team-entry.png', text: '组队广场', url: '/pages/team/team', linkType: 'page' },
      { icon: '/assets/icons/mall-entry.png', text: '积分商城', url: '/pages/mall/mall', linkType: 'page' },
      { icon: '/assets/icons/member-entry.png', text: '会员中心', url: '/pages/member/member', linkType: 'page' },
      { icon: '/assets/icons/coupon-entry.png', text: '我的券包', url: '/pages/coupons/coupons', linkType: 'page' }
    ]
  },

  // 处理快捷入口跳转
  handleQuickEntryNav(url, linkType) {
    if (!url) return

    // 根据链接类型跳转
    if (linkType === 'tab') {
      wx.switchTab({ url })
    } else if (linkType === 'webview') {
      wx.navigateTo({ url: `/pages/webview/webview?url=${encodeURIComponent(url)}` })
    } else {
      wx.navigateTo({ url })
    }
  },

  // 检查区块是否可见
  isBlockVisible(blockCode) {
    return this.data.visibleBlocks.includes(blockCode)
  },

  // 加载数据
  async loadData(forceRefresh = false) {
    this.setData({ loading: true })

    try {
      const promises = []

      // 加载公告
      promises.push(this.loadAnnouncements())

      // 加载Hero背景图
      promises.push(this.loadHeroImage())

      // 根据可见区块加载对应数据
      if (this.isBlockVisible('banner')) {
        promises.push(this.loadBanners())
      }
      if (this.isBlockVisible('hot_venues') || this.isBlockVisible('list')) {
        promises.push(this.loadHotVenues())
      }
      if (this.isBlockVisible('hot_activities') || this.isBlockVisible('scroll')) {
        promises.push(this.loadHotActivities())
      }
      if (this.isBlockVisible('hot_coaches')) {
        promises.push(this.loadHotCoaches())
      }

      const results = await Promise.all(promises)

      let resultIndex = 0
      const updateData = { loading: false }

      // 公告
      updateData.announcements = results[resultIndex++] || []

      // Hero背景图
      const heroImage = results[resultIndex++]
      if (heroImage) {
        updateData.heroImage = heroImage
      }

      if (this.isBlockVisible('banner')) {
        updateData.banners = results[resultIndex++] || []
      }
      if (this.isBlockVisible('hot_venues') || this.isBlockVisible('list')) {
        updateData.hotVenues = results[resultIndex++] || []
      }
      if (this.isBlockVisible('hot_activities') || this.isBlockVisible('scroll')) {
        updateData.hotActivities = results[resultIndex++] || []
      }
      if (this.isBlockVisible('hot_coaches')) {
        updateData.hotCoaches = results[resultIndex++] || []
      }

      this.setData(updateData)
    } catch (err) {
      console.error('加载数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载公告
  async loadAnnouncements() {
    try {
      const res = await app.request({ url: '/member/announcements?limit=5' })
      return res.data || []
    } catch (err) {
      console.log('加载公告失败:', err)
      return []
    }
  },

  // 加载Hero背景图
  async loadHeroImage() {
    try {
      // 尝试从轮播图配置中获取第一张作为Hero背景
      const res = await app.request({ url: '/member/banners?position=hero' })
      if (res.data && res.data.length > 0) {
        return res.data[0].image
      }
      return null
    } catch (err) {
      return null
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

  // 公告点击
  onAnnouncementTap(e) {
    const item = e.currentTarget.dataset.item
    if (item && item.url) {
      wx.navigateTo({ url: item.url })
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
    const { url, linktype } = e.currentTarget.dataset
    if (!url) return

    // 需要登录的页面
    const loginRequiredPages = ['/pages/profile/', '/pages/member/', '/pages/coupons/', '/pages/wallet/', '/pages/orders/']
    if (loginRequiredPages.some(page => url.includes(page))) {
      if (!app.checkLogin()) return
    }

    // 根据链接类型跳转
    this.handleQuickEntryNav(url, linktype)
  },

  // 跳转到场馆预约（主CTA按钮）
  goToVenue() {
    wx.switchTab({
      url: '/pages/venue/venue'
    })
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
