const app = getApp()
const util = require('../../utils/util.js')
const api = require('../../utils/api.js')

Page({
  data: {
    venueTypes: [],
    currentTypeId: null,
    dates: [],
    selectedDate: '',
    calendarData: {
      venues: [],
      time_slots: []
    },
    selectedVenueId: null,
    selectedVenueName: '',
    selectedVenuePrice: 0,
    selectedSlots: [], // [{hour: 6}, {hour: 7}, ...]
    loading: true,
    submitting: false,
    calendarHeight: 800,
    scrollLeft: 0,
    // 会员权限相关
    canBook: true,
    memberLevel: 'TRIAL',
    bookingQuota: 0,
    usedQuota: 0,
    remainingQuota: 0,
    permissionReason: ''
  },

  onLoad(options) {
    // 计算日历高度（18个时间段 * 80rpx）
    const systemInfo = wx.getSystemInfoSync()
    const calendarHeight = systemInfo.windowHeight - 280 // 减去顶部高度
    this.setData({ calendarHeight })

    this.initDates()
    // 先加载场馆类型，完成后再检查权限
    this.loadVenueTypes(options.type_id).then(() => {
      this.checkMemberPermission()
    })
  },

  onShow() {
    if (this.data.currentTypeId) {
      this.loadCalendarData()
    }
    this.checkMemberPermission()
  },

  // 检查会员预约权限
  async checkMemberPermission() {
    try {
      const res = await api.checkBookingPermission({
        venue_type_id: this.data.currentTypeId || 1,
        booking_date: this.data.selectedDate
      })
      if (res.code === 200) {
        const data = res.data || {}
        this.setData({
          canBook: data.can_book !== false,
          memberLevel: data.member_level || app.globalData.memberLevel,
          bookingQuota: data.daily_quota || 0,
          usedQuota: data.used_quota || 0,
          remainingQuota: data.remaining_quota || 0,
          permissionReason: data.reason || ''
        })

        // 如果是TRIAL会员，显示提示
        if (data.member_level === 'TRIAL' || !data.can_book) {
          this.showTrialTip()
        }
      }
    } catch (err) {
      console.error('检查预约权限失败:', err)
      // 从app获取默认值
      this.setData({
        canBook: app.checkCanBook(),
        memberLevel: app.globalData.memberLevel,
        bookingQuota: app.globalData.bookingQuota,
        usedQuota: app.globalData.usedQuota,
        remainingQuota: app.getRemainingQuota()
      })
      if (app.globalData.memberLevel === 'TRIAL') {
        this.showTrialTip()
      }
    }
  },

  // 显示体验会员提示
  showTrialTip() {
    wx.showModal({
      title: '预约提示',
      content: '体验会员暂无法自行预约场馆，请联系前台或升级会员',
      confirmText: '升级会员',
      cancelText: '知道了',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: '/pages/member/member'
          })
        }
      }
    })
  },

  // 初始化日期列表（7天）
  initDates() {
    const dates = []
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const today = new Date()

    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      dates.push({
        date: util.formatDate(date, 'YYYY-MM-DD'),
        day: date.getDate(),
        weekDay: i === 0 ? '今天' : weekDays[date.getDay()]
      })
    }

    this.setData({
      dates,
      selectedDate: dates[0].date
    })
  },

  // 加载场馆类型
  async loadVenueTypes(defaultTypeId) {
    try {
      const res = await app.request({
        url: '/member/venue-types'
      })

      const types = res.data || []
      if (types.length > 0) {
        const typeId = defaultTypeId ? parseInt(defaultTypeId) : types[0].id
        this.setData({
          venueTypes: types,
          currentTypeId: typeId
        })
        this.loadCalendarData()
      } else {
        this.setData({
          venueTypes: [],
          loading: false
        })
      }
    } catch (err) {
      console.error('加载场馆类型失败:', err)
      this.setData({ loading: false })
    }
  },

  // 加载日历数据
  async loadCalendarData() {
    this.setData({ loading: true })

    try {
      const res = await app.request({
        url: `/member/venue-calendar?type_id=${this.data.currentTypeId}&date=${this.data.selectedDate}`
      })

      this.setData({
        calendarData: res.data || { venues: [], time_slots: [] },
        loading: false
      })
    } catch (err) {
      console.error('加载日历数据失败:', err)
      this.setData({
        calendarData: { venues: [], time_slots: [] },
        loading: false
      })
    }
  },

  // 选择场馆类型
  selectType(e) {
    const typeId = e.currentTarget.dataset.id
    if (typeId === this.data.currentTypeId) return

    this.setData({
      currentTypeId: typeId,
      selectedSlots: [],
      selectedVenueId: null,
      selectedVenueName: '',
      selectedVenuePrice: 0
    })
    this.loadCalendarData()
  },

  // 选择日期
  selectDate(e) {
    const date = e.currentTarget.dataset.date
    if (date === this.data.selectedDate) return

    this.setData({
      selectedDate: date,
      selectedSlots: [],
      selectedVenueId: null,
      selectedVenueName: '',
      selectedVenuePrice: 0
    })
    this.loadCalendarData()
  },

  // 选择时间段
  selectSlot(e) {
    const { venueId, venueName, venuePrice, hour } = e.currentTarget.dataset

    // 找到对应场馆和时段的状态
    const venue = this.data.calendarData.venues.find(v => v.id === venueId)
    if (!venue) return

    const slot = venue.slots.find(s => s.hour === hour)
    if (slot.status === 'reserved') {
      wx.showToast({
        title: '该时段已被预约',
        icon: 'none'
      })
      return
    }

    let { selectedSlots, selectedVenueId } = this.data

    // 如果选择了不同的场馆，清空已选时段
    if (selectedVenueId && selectedVenueId !== venueId) {
      selectedSlots = []
    }

    // 检查是否已选中
    const index = selectedSlots.findIndex(s => s.hour === hour)

    if (index > -1) {
      // 取消选中
      selectedSlots.splice(index, 1)
    } else {
      // 选中 - 检查是否连续
      if (selectedSlots.length > 0) {
        const hours = selectedSlots.map(s => s.hour).sort((a, b) => a - b)
        const minHour = hours[0]
        const maxHour = hours[hours.length - 1]

        // 只允许选择连续的时段
        if (hour !== minHour - 1 && hour !== maxHour + 1) {
          wx.showToast({
            title: '请选择连续的时段',
            icon: 'none'
          })
          return
        }
      }
      selectedSlots.push({ hour })
    }

    // 按时间排序
    selectedSlots.sort((a, b) => a.hour - b.hour)

    this.setData({
      selectedSlots,
      selectedVenueId: selectedSlots.length > 0 ? venueId : null,
      selectedVenueName: selectedSlots.length > 0 ? venueName : '',
      selectedVenuePrice: selectedSlots.length > 0 ? venuePrice : 0
    })
  },

  // 同步滚动
  onCalendarScroll(e) {
    this.setData({
      scrollLeft: e.detail.scrollLeft
    })
  },

  // 跳转会员中心
  goToMember() {
    wx.navigateTo({
      url: '/pages/member/member'
    })
  },

  // 提交预约
  async submitBooking() {
    if (this.data.selectedSlots.length === 0) {
      wx.showToast({
        title: '请选择时间段',
        icon: 'none'
      })
      return
    }

    // 检查预约权限
    if (!this.data.canBook) {
      this.showTrialTip()
      return
    }

    // 检查额度
    const duration = this.data.selectedSlots.length
    if (duration > this.data.remainingQuota) {
      wx.showModal({
        title: '额度不足',
        content: `您今日剩余预约额度为${this.data.remainingQuota}小时，已选${duration}小时`,
        confirmText: '升级会员',
        cancelText: '调整时段',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({
              url: '/pages/member/member'
            })
          }
        }
      })
      return
    }

    this.setData({ submitting: true })

    try {
      const slots = this.data.selectedSlots
      const startHour = slots[0].hour
      const endHour = slots[slots.length - 1].hour + 1

      await app.request({
        url: '/member/reservations',
        method: 'POST',
        data: {
          venue_id: this.data.selectedVenueId,
          reservation_date: this.data.selectedDate,
          start_time: `${String(startHour).padStart(2, '0')}:00`,
          end_time: `${String(endHour).padStart(2, '0')}:00`,
          duration: this.data.selectedSlots.length * 60
        }
      })

      wx.showToast({
        title: '预约成功',
        icon: 'success'
      })

      // 清空选择并刷新数据
      this.setData({
        selectedSlots: [],
        selectedVenueId: null,
        selectedVenueName: '',
        selectedVenuePrice: 0
      })

      setTimeout(() => {
        this.loadCalendarData()
      }, 1000)

    } catch (err) {
      console.error('预约失败:', err)
      wx.showToast({
        title: err.message || '预约失败',
        icon: 'none'
      })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
