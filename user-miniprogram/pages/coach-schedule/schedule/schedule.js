const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    weekDates: [],
    weekTitle: '',
    timeSlots: [],
    scheduleData: {}, // { 'YYYY-MM-DD': { '09:00': 'available' | 'reserved' | 'unavailable' } }
    startDateStr: '' // 存储为字符串格式 YYYY-MM-DD
  },

  onLoad() {
    this.initTimeSlots()
    this.initWeek()
  },

  onShow() {
    this.loadSchedule()
  },

  onPullDownRefresh() {
    this.loadSchedule().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 初始化时间段
  initTimeSlots() {
    const slots = util.generateTimeSlots(8, 22)
    this.setData({ timeSlots: slots })
  },

  // 初始化本周
  initWeek() {
    const today = new Date()
    // 获取本周一
    const day = today.getDay()
    const monday = new Date(today)
    monday.setDate(today.getDate() - (day === 0 ? 6 : day - 1))

    this.setData({ startDateStr: util.formatDate(monday, 'YYYY-MM-DD') })
    this.updateWeekDates()
  },

  // 更新周日期
  updateWeekDates() {
    const { startDateStr } = this.data
    if (!startDateStr) return

    const startDate = new Date(startDateStr)
    const weekDates = []

    for (let i = 0; i < 7; i++) {
      const date = new Date(startDate)
      date.setDate(startDate.getDate() + i)
      weekDates.push({
        date: util.formatDate(date, 'YYYY-MM-DD'),
        day: date.getDate(),
        month: date.getMonth() + 1,
        weekDay: util.getWeekDay(date),
        isToday: util.formatDate(new Date(), 'YYYY-MM-DD') === util.formatDate(date, 'YYYY-MM-DD')
      })
    }

    const endDate = new Date(startDate)
    endDate.setDate(startDate.getDate() + 6)
    const weekTitle = `${util.formatDate(startDate, 'MM月DD日')} - ${util.formatDate(endDate, 'MM月DD日')}`

    this.setData({ weekDates, weekTitle })
    this.loadSchedule()
  },

  // 上一周
  prevWeek() {
    const { startDateStr } = this.data
    const startDate = new Date(startDateStr)
    startDate.setDate(startDate.getDate() - 7)
    this.setData({ startDateStr: util.formatDate(startDate, 'YYYY-MM-DD') })
    this.updateWeekDates()
  },

  // 下一周
  nextWeek() {
    const { startDateStr } = this.data
    const startDate = new Date(startDateStr)
    startDate.setDate(startDate.getDate() + 7)
    this.setData({ startDateStr: util.formatDate(startDate, 'YYYY-MM-DD') })
    this.updateWeekDates()
  },

  // 加载排期数据
  async loadSchedule() {
    try {
      const { weekDates } = this.data
      if (weekDates.length === 0) return

      const startDate = weekDates[0].date
      const endDate = weekDates[6].date

      const res = await app.request({
        url: `/coach/schedule?start_date=${startDate}&end_date=${endDate}`
      })

      this.setData({ scheduleData: res.data || {} })
    } catch (err) {
      console.error('加载排期失败:', err)
    }
  },

  // 获取时间段样式类
  getSlotClass(time, date) {
    const { scheduleData } = this.data
    const dayData = scheduleData[date] || {}
    const status = dayData[time]

    if (status === 'reserved') return 'reserved'
    if (status === 'available') return 'available'
    return 'unavailable'
  },

  // 是否已预约
  isReserved(time, date) {
    const { scheduleData } = this.data
    const dayData = scheduleData[date] || {}
    return dayData[time] === 'reserved'
  },

  // 是否可用
  isAvailable(time, date) {
    const { scheduleData } = this.data
    const dayData = scheduleData[date] || {}
    return dayData[time] === 'available'
  },

  // 切换时间段状态
  async toggleSlot(e) {
    const { time, date } = e.currentTarget.dataset
    const { scheduleData } = this.data

    // 已预约的不能修改
    if (this.isReserved(time, date)) {
      wx.showToast({
        title: '已被预约，无法修改',
        icon: 'none'
      })
      return
    }

    // 切换状态
    const newStatus = this.isAvailable(time, date) ? 'unavailable' : 'available'

    try {
      await app.request({
        url: '/coach/schedule',
        method: 'POST',
        data: {
          date,
          time,
          status: newStatus
        }
      })

      // 更新本地数据
      const newScheduleData = { ...scheduleData }
      if (!newScheduleData[date]) {
        newScheduleData[date] = {}
      }
      newScheduleData[date][time] = newStatus

      this.setData({ scheduleData: newScheduleData })
    } catch (err) {
      console.error('更新排期失败:', err)
    }
  },

  // 全部设为可用
  async setAllAvailable() {
    wx.showModal({
      title: '确认操作',
      content: '将本周所有未预约时段设为可用？',
      success: async (res) => {
        if (res.confirm) {
          await this.batchUpdateSchedule('available')
        }
      }
    })
  },

  // 全部设为不可用
  async setAllUnavailable() {
    wx.showModal({
      title: '确认操作',
      content: '将本周所有未预约时段设为不可用？',
      success: async (res) => {
        if (res.confirm) {
          await this.batchUpdateSchedule('unavailable')
        }
      }
    })
  },

  // 批量更新排期
  async batchUpdateSchedule(status) {
    try {
      wx.showLoading({ title: '处理中' })
      const { weekDates } = this.data

      await app.request({
        url: '/coach/schedule/batch',
        method: 'POST',
        data: {
          start_date: weekDates[0].date,
          end_date: weekDates[6].date,
          status
        }
      })

      wx.hideLoading()
      wx.showToast({
        title: '设置成功',
        icon: 'success'
      })

      this.loadSchedule()
    } catch (err) {
      wx.hideLoading()
      console.error('批量更新失败:', err)
    }
  },

  // 复制上周排期
  async copyLastWeek() {
    wx.showModal({
      title: '确认操作',
      content: '将上周的排期复制到本周？',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '处理中' })
            const { weekDates } = this.data

            await app.request({
              url: '/coach/schedule/copy',
              method: 'POST',
              data: {
                target_start_date: weekDates[0].date
              }
            })

            wx.hideLoading()
            wx.showToast({
              title: '复制成功',
              icon: 'success'
            })

            this.loadSchedule()
          } catch (err) {
            wx.hideLoading()
            console.error('复制排期失败:', err)
          }
        }
      }
    })
  }
})
