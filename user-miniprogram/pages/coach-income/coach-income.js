const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    incomeData: {},
    incomeList: [],
    currentFilter: 'all',
    loading: false
  },

  onLoad() {
    this.loadIncomeData()
    this.loadIncomeList()
  },

  onPullDownRefresh() {
    Promise.all([
      this.loadIncomeData(),
      this.loadIncomeList()
    ]).then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 加载收入概览
  async loadIncomeData() {
    try {
      const res = await app.coachRequest({
        url: '/coach/income/overview'
      })
      this.setData({ incomeData: res.data || {} })
    } catch (err) {
      console.error('加载收入概览失败:', err)
    }
  },

  // 加载收入列表
  async loadIncomeList() {
    this.setData({ loading: true })

    try {
      const { currentFilter } = this.data
      let url = '/coach/income/list'
      if (currentFilter !== 'all') {
        url += `?status=${currentFilter}`
      }

      const res = await app.coachRequest({ url })

      const list = (res.data || []).map(item => ({
        ...item,
        course_date: util.formatDate(item.course_date, 'YYYY-MM-DD'),
        start_time: util.formatTime(item.start_time),
        end_time: util.formatTime(item.end_time)
      }))

      this.setData({
        incomeList: list,
        loading: false
      })
    } catch (err) {
      console.error('加载收入列表失败:', err)
      this.setData({ loading: false })
    }
  },

  // 设置筛选
  setFilter(e) {
    const filter = e.currentTarget.dataset.filter
    this.setData({ currentFilter: filter })
    this.loadIncomeList()
  }
})
