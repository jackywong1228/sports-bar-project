const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    periodType: 'daily',  // daily, weekly, monthly
    periodOptions: [
      { value: 'daily', label: '日榜' },
      { value: 'weekly', label: '周榜' },
      { value: 'monthly', label: '月榜' }
    ],
    venueTypeId: null,  // null 表示综合排行
    venueTypes: [],
    leaderboard: [],
    myRank: null,
    loading: false
  },

  onLoad() {
    this.loadVenueTypes()
    this.loadLeaderboard()
    this.loadMyRank()
  },

  // 加载场馆类型
  async loadVenueTypes() {
    try {
      const res = await api.getVenueTypes()
      if (res.code === 200) {
        const types = [{ id: null, name: '综合' }, ...res.data]
        this.setData({ venueTypes: types })
      }
    } catch (err) {
      console.error('加载场馆类型失败:', err)
    }
  },

  // 加载排行榜
  async loadLeaderboard() {
    const { periodType, venueTypeId } = this.data
    this.setData({ loading: true })

    try {
      const res = await api.getLeaderboard({
        period: periodType,
        venue_type_id: venueTypeId
      })
      if (res.code === 200) {
        this.setData({ leaderboard: res.data || [] })
      }
    } catch (err) {
      console.error('加载排行榜失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      this.setData({ loading: false })
    }
  },

  // 加载我的排名
  async loadMyRank() {
    const { periodType, venueTypeId } = this.data

    try {
      const res = await api.getMyRank({
        period: periodType,
        venue_type_id: venueTypeId
      })
      if (res.code === 200) {
        this.setData({ myRank: res.data })
      }
    } catch (err) {
      console.error('加载我的排名失败:', err)
    }
  },

  // 切换周期
  onPeriodChange(e) {
    const periodType = e.currentTarget.dataset.period
    if (periodType === this.data.periodType) return

    this.setData({ periodType })
    this.loadLeaderboard()
    this.loadMyRank()
  },

  // 切换场馆类型
  onVenueTypeChange(e) {
    const index = e.detail.value
    const venueTypeId = this.data.venueTypes[index]?.id || null

    this.setData({ venueTypeId })
    this.loadLeaderboard()
    this.loadMyRank()
  },

  // 格式化时长显示
  formatDuration(minutes) {
    if (!minutes) return '0分钟'
    if (minutes < 60) return `${minutes}分钟`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}小时${mins}分钟` : `${hours}小时`
  },

  // 获取排名样式
  getRankClass(rank) {
    if (rank === 1) return 'gold'
    if (rank === 2) return 'silver'
    if (rank === 3) return 'bronze'
    return ''
  }
})
