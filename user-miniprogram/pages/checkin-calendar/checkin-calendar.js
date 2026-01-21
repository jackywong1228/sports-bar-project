const app = getApp()
const api = require('../../utils/api')

Page({
  data: {
    currentYear: 2026,
    currentMonth: 1,
    calendarData: [],
    checkinDays: [],
    selectedDate: null,
    dayDetail: null,
    monthStats: {
      checkin_days: 0,
      total_duration: 0,
      total_points: 0
    },
    weekDays: ['日', '一', '二', '三', '四', '五', '六']
  },

  onLoad() {
    const now = new Date()
    this.setData({
      currentYear: now.getFullYear(),
      currentMonth: now.getMonth() + 1
    })
    this.loadCalendarData()
  },

  // 加载日历数据
  async loadCalendarData() {
    const { currentYear, currentMonth } = this.data
    wx.showLoading({ title: '加载中' })

    try {
      const res = await api.getCheckinCalendar(currentYear, currentMonth)
      if (res.code === 200) {
        this.setData({
          checkinDays: res.data.checkin_days || [],
          monthStats: res.data.stats || {}
        })
        this.generateCalendar()
      }
    } catch (err) {
      console.error('加载日历失败:', err)
      wx.showToast({ title: '加载失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  // 生成日历
  generateCalendar() {
    const { currentYear, currentMonth, checkinDays } = this.data
    const firstDay = new Date(currentYear, currentMonth - 1, 1)
    const lastDay = new Date(currentYear, currentMonth, 0)
    const startDayOfWeek = firstDay.getDay()
    const daysInMonth = lastDay.getDate()

    const calendar = []
    const today = new Date()
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

    // 上月的天数填充
    const prevMonth = currentMonth === 1 ? 12 : currentMonth - 1
    const prevYear = currentMonth === 1 ? currentYear - 1 : currentYear
    const prevMonthDays = new Date(prevYear, prevMonth, 0).getDate()

    for (let i = startDayOfWeek - 1; i >= 0; i--) {
      const day = prevMonthDays - i
      calendar.push({
        day,
        date: `${prevYear}-${String(prevMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`,
        isCurrentMonth: false,
        hasCheckin: false,
        isToday: false
      })
    }

    // 当月天数
    for (let i = 1; i <= daysInMonth; i++) {
      const dateStr = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(i).padStart(2, '0')}`
      calendar.push({
        day: i,
        date: dateStr,
        isCurrentMonth: true,
        hasCheckin: checkinDays.includes(dateStr),
        isToday: dateStr === todayStr
      })
    }

    // 下月天数填充
    const remaining = 42 - calendar.length
    const nextMonth = currentMonth === 12 ? 1 : currentMonth + 1
    const nextYear = currentMonth === 12 ? currentYear + 1 : currentYear

    for (let i = 1; i <= remaining; i++) {
      calendar.push({
        day: i,
        date: `${nextYear}-${String(nextMonth).padStart(2, '0')}-${String(i).padStart(2, '0')}`,
        isCurrentMonth: false,
        hasCheckin: false,
        isToday: false
      })
    }

    this.setData({ calendarData: calendar })
  },

  // 上一月
  prevMonth() {
    let { currentYear, currentMonth } = this.data
    if (currentMonth === 1) {
      currentMonth = 12
      currentYear--
    } else {
      currentMonth--
    }
    this.setData({ currentYear, currentMonth, selectedDate: null, dayDetail: null })
    this.loadCalendarData()
  },

  // 下一月
  nextMonth() {
    let { currentYear, currentMonth } = this.data
    if (currentMonth === 12) {
      currentMonth = 1
      currentYear++
    } else {
      currentMonth++
    }
    this.setData({ currentYear, currentMonth, selectedDate: null, dayDetail: null })
    this.loadCalendarData()
  },

  // 选择日期
  async selectDate(e) {
    const { date, iscurrentmonth, hascheckin } = e.currentTarget.dataset
    if (!iscurrentmonth) return

    this.setData({ selectedDate: date })

    if (hascheckin) {
      wx.showLoading({ title: '加载中' })
      try {
        const res = await api.getCheckinRecords({ check_date: date })
        if (res.code === 200) {
          this.setData({ dayDetail: res.data.items || [] })
        }
      } catch (err) {
        console.error('加载详情失败:', err)
      } finally {
        wx.hideLoading()
      }
    } else {
      this.setData({ dayDetail: [] })
    }
  },

  // 关闭详情
  closeDetail() {
    this.setData({ selectedDate: null, dayDetail: null })
  }
})
