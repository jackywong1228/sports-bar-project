const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    weekDates: [],
    selectedDate: '',
    currentMonth: '',
    currentFilter: 'all',
    reservations: [],
    reservationCounts: {},
    loading: false
  },

  onLoad() {
    if (!app.checkCoachLogin()) return
    this.initDates()
    this.loadReservations()
  },

  onShow() {
    if (!app.globalData.coachToken) return
    // 确保日期已初始化
    if (!this.data.selectedDate) {
      this.initDates()
    }
    this.loadReservations()
  },

  onPullDownRefresh() {
    this.loadReservations().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 初始化日期
  initDates() {
    const today = new Date()
    const weekDates = util.getWeekDates(today)
    const selectedDate = util.formatDate(today, 'YYYY-MM-DD')
    const currentMonth = util.formatDate(today, 'YYYY年MM月')

    this.setData({
      weekDates,
      selectedDate,
      currentMonth
    })
  },

  // 上一周
  prevWeek() {
    const firstDate = new Date(this.data.weekDates[0].date)
    firstDate.setDate(firstDate.getDate() - 7)
    const weekDates = util.getWeekDates(firstDate)
    const currentMonth = util.formatDate(firstDate, 'YYYY年MM月')

    this.setData({
      weekDates,
      currentMonth,
      selectedDate: weekDates[0].date
    })
    this.loadReservations()
  },

  // 下一周
  nextWeek() {
    const firstDate = new Date(this.data.weekDates[0].date)
    firstDate.setDate(firstDate.getDate() + 7)
    const weekDates = util.getWeekDates(firstDate)
    const currentMonth = util.formatDate(firstDate, 'YYYY年MM月')

    this.setData({
      weekDates,
      currentMonth,
      selectedDate: weekDates[0].date
    })
    this.loadReservations()
  },

  // 选择日期
  selectDate(e) {
    const date = e.currentTarget.dataset.date
    this.setData({ selectedDate: date })
    this.loadReservations()
  },

  // 设置筛选
  setFilter(e) {
    const filter = e.currentTarget.dataset.filter
    this.setData({ currentFilter: filter })
    this.loadReservations()
  },

  // 加载预约列表
  async loadReservations() {
    this.setData({ loading: true })

    try {
      const { selectedDate, currentFilter } = this.data
      let url = `/coach/reservations?date=${selectedDate}`
      if (currentFilter !== 'all') {
        url += `&status=${currentFilter}`
      }

      const res = await app.coachRequest({ url })

      // 处理预约状态显示
      const reservations = (res.data || []).map(item => {
        const status = util.getReservationStatus(item.status)
        return {
          ...item,
          statusText: status.text,
          statusClass: status.class,
          start_time: util.formatTime(item.start_time),
          end_time: util.formatTime(item.end_time)
        }
      })

      // 更新预约数量统计
      const counts = {}
      this.data.weekDates.forEach(d => {
        counts[d.date] = 0
      })

      this.setData({
        reservations,
        reservationCounts: counts,
        loading: false
      })

      // 加载整周的预约数量
      this.loadWeekCounts()
    } catch (err) {
      console.error('加载预约失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载整周的预约数量
  async loadWeekCounts() {
    try {
      const startDate = this.data.weekDates[0].date
      const endDate = this.data.weekDates[6].date
      const res = await app.coachRequest({
        url: `/coach/reservations/counts?start_date=${startDate}&end_date=${endDate}`
      })

      if (res.data) {
        this.setData({ reservationCounts: res.data })
      }
    } catch (err) {
      console.error('加载预约数量失败:', err)
    }
  },

  // 跳转预约详情
  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/coach-reservation-detail/coach-reservation-detail?id=${id}`
    })
  }
})
