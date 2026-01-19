const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    currentTab: 'coin',
    walletData: {},
    recordList: [],
    selectedMonth: '',
    loading: false
  },

  onLoad(options) {
    // 设置默认月份
    const now = new Date()
    this.setData({
      selectedMonth: util.formatDate(now, 'YYYY-MM'),
      currentTab: options.type || 'coin'
    })
    this.loadWalletData()
    this.loadRecordList()
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadWalletData(),
      this.loadRecordList()
    ]).then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 切换标签
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ currentTab: tab })
    this.loadRecordList()
  },

  // 选择月份
  selectMonth(e) {
    this.setData({ selectedMonth: e.detail.value })
    this.loadRecordList()
  },

  // 加载钱包数据
  async loadWalletData() {
    try {
      const res = await app.coachRequest({
        url: '/coach/wallet'
      })
      this.setData({ walletData: res.data || {} })
    } catch (err) {
      console.error('加载钱包数据失败:', err)
    }
  },

  // 加载收支记录
  async loadRecordList() {
    this.setData({ loading: true })

    try {
      const { currentTab, selectedMonth } = this.data
      const res = await app.coachRequest({
        url: `/coach/wallet/records?type=${currentTab}&month=${selectedMonth}`
      })

      const list = (res.data || []).map(item => ({
        ...item,
        created_at: util.formatDate(item.created_at, 'MM-DD HH:mm')
      }))

      this.setData({
        recordList: list,
        loading: false
      })
    } catch (err) {
      console.error('加载收支记录失败:', err)
      this.setData({ loading: false })
    }
  },

  // 跳转充值
  goToRecharge() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  }
})
