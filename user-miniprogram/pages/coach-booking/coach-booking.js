const app = getApp()
const util = require('../../utils/util.js')

Page({
  data: {
    coachId: null,
    coach: {},
    venues: [],
    selectedVenue: null,
    dates: [],
    selectedDate: '',
    timeSlots: [],
    selectedSlots: [],
    loading: true,
    submitting: false
  },

  onLoad(options) {
    this.setData({ coachId: options.id })
    this.initDates()
    this.loadData()
  },

  // 初始化日期列表
  initDates() {
    const dates = util.getDateList(7)
    this.setData({
      dates,
      selectedDate: dates[0].date
    })
  },

  // 加载数据
  async loadData() {
    try {
      const [coachRes, venuesRes] = await Promise.all([
        app.request({ url: `/member/coaches/${this.data.coachId}` }),
        app.request({ url: '/member/venues?limit=100' })
      ])

      this.setData({
        coach: coachRes.data || {},
        venues: venuesRes.data || [],
        selectedVenue: venuesRes.data?.[0]?.id || null,
        loading: false
      })

      this.loadTimeSlots()
    } catch (err) {
      console.error('加载数据失败:', err)
      this.setData({ loading: false })
    }
  },

  // 选择场馆
  selectVenue(e) {
    const venueId = e.currentTarget.dataset.id
    this.setData({
      selectedVenue: venueId,
      selectedSlots: []
    })
    this.loadTimeSlots()
  },

  // 选择日期
  selectDate(e) {
    const date = e.currentTarget.dataset.date
    this.setData({
      selectedDate: date,
      selectedSlots: []
    })
    this.loadTimeSlots()
  },

  // 加载时间段
  async loadTimeSlots() {
    try {
      const res = await app.request({
        url: `/member/coaches/${this.data.coachId}/schedule?date=${this.data.selectedDate}`
      })

      const slots = (res.data || []).map(slot => ({
        ...slot,
        statusText: this.getSlotStatusText(slot.status)
      }))

      this.setData({ timeSlots: slots })
    } catch (err) {
      console.error('加载时间段失败:', err)
      // 使用默认时间段
      const defaultSlots = util.getTimeSlots(8, 22).map(slot => ({
        time: slot.time,
        label: slot.label,
        status: 'available',
        statusText: '可预约'
      }))
      this.setData({ timeSlots: defaultSlots })
    }
  },

  // 获取时间段状态文字
  getSlotStatusText(status) {
    const map = {
      'available': '可预约',
      'reserved': '已预约',
      'unavailable': '休息'
    }
    return map[status] || '可预约'
  },

  // 选择时间段
  selectSlot(e) {
    const time = e.currentTarget.dataset.time
    const slot = this.data.timeSlots.find(s => s.time === time)

    if (slot.status !== 'available') {
      wx.showToast({
        title: '该时间段不可预约',
        icon: 'none'
      })
      return
    }

    let selectedSlots = [...this.data.selectedSlots]
    const index = selectedSlots.indexOf(time)

    if (index > -1) {
      selectedSlots.splice(index, 1)
    } else {
      selectedSlots.push(time)
    }

    selectedSlots.sort()
    this.setData({ selectedSlots })
  },

  // 计算总价
  getTotalPrice() {
    const price = Number(this.data.coach.price) || 0
    return (price * this.data.selectedSlots.length).toFixed(0)
  },

  // 计算时长
  getDuration() {
    return this.data.selectedSlots.length
  },

  // 获取时间范围
  getTimeRange() {
    const slots = this.data.selectedSlots
    if (slots.length === 0) return ''

    const startTime = slots[0]
    const endHour = parseInt(slots[slots.length - 1].split(':')[0]) + 1
    const endTime = `${String(endHour).padStart(2, '0')}:00`

    return `${startTime} - ${endTime}`
  },

  // 提交预约
  async submitBooking() {
    if (!this.data.selectedVenue) {
      wx.showToast({ title: '请选择场馆', icon: 'none' })
      return
    }

    if (this.data.selectedSlots.length === 0) {
      wx.showToast({ title: '请选择时间段', icon: 'none' })
      return
    }

    this.setData({ submitting: true })

    try {
      const slots = this.data.selectedSlots
      const startTime = slots[0]
      const endHour = parseInt(slots[slots.length - 1].split(':')[0]) + 1
      const endTime = `${String(endHour).padStart(2, '0')}:00`

      const res = await app.request({
        url: '/member/reservations',
        method: 'POST',
        data: {
          coach_id: this.data.coachId,
          venue_id: this.data.selectedVenue,
          reservation_date: this.data.selectedDate,
          start_time: startTime,
          end_time: endTime,
          duration: this.getDuration() * 60
        }
      })

      wx.showToast({
        title: '预约成功',
        icon: 'success'
      })

      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (err) {
      console.error('预约失败:', err)
    } finally {
      this.setData({ submitting: false })
    }
  }
})
