const app = getApp()
const util = require('../../utils/util.js')
const api = require('../../utils/api.js')

// 场馆类型图标映射（英文key → 本地图片路径）
const SPORT_ICON_MAP = {
  tennis: '/assets/icons/sports/tennis.svg',
  pickleball: '/assets/icons/sports/pickleball.svg',
  squash: '/assets/icons/sports/squash.svg',
  golf: '/assets/icons/sports/golf.svg',
  'golf-vip': '/assets/icons/sports/golf.svg',
  golf_vip: '/assets/icons/sports/golf.svg',
  basketball: '/assets/icons/sports/basketball.svg',
  badminton: '/assets/icons/sports/badminton.svg',
}

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
    // 会员权限相关（三级会员制）
    canBook: true,
    isMember: false,
    memberLevel: 'S',
    permissionReason: '',
    freeUsageInfo: null  // SSS免费时长信息
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

  // 检查会员预约权限（三级会员制）
  async checkMemberPermission() {
    const legacyMap = { GUEST: 'S', TRIAL: 'S', MEMBER: 'SS' }

    try {
      const res = await api.checkBookingPermission({
        venue_type_id: this.data.currentTypeId || 1,
        booking_date: this.data.selectedDate
      })
      if (res.code === 200) {
        const data = res.data || {}
        const levelCode = data.level_code || app.globalData.memberLevel || 'S'
        const mappedLevel = legacyMap[levelCode] || levelCode
        const isMember = (mappedLevel === 'SS' || mappedLevel === 'SSS')

        this.setData({
          canBook: data.can_book !== false,
          isMember: isMember,
          memberLevel: mappedLevel,
          permissionReason: data.reason || '',
          freeUsageInfo: data.free_usage_info || null
        })

        if (!data.can_book) {
          this.showBookingTip(mappedLevel, data.reason)
        }
      }
    } catch (err) {
      console.error('检查预约权限失败:', err)
      this.setData({
        canBook: app.checkCanBook(),
        isMember: app.globalData.isMember,
        memberLevel: app.globalData.memberLevel
      })
      if (!app.globalData.isMember) {
        this.showBookingTip(app.globalData.memberLevel, '')
      }
    }
  },

  // 显示预约权限提示（根据等级差异化）
  showBookingTip(level, reason) {
    let content = reason || ''
    if (level === 'S') {
      content = '当前为S级会员，无法预约场馆。\n开通SS会员可预约当天场馆，SSS会员可提前3天预约。'
    } else if (level === 'SS' && !content) {
      content = 'SS级会员仅可预约当天场馆。如需提前预约，请升级为SSS会员。'
    }

    wx.showModal({
      title: '预约提示',
      content: content,
      confirmText: '查看会员',
      cancelText: '知道了',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({ url: '/pages/member/member' })
        }
      }
    })
  },

  // 初始化日期列表（根据会员等级限制天数）
  initDates() {
    const dates = []
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const today = new Date()
    const level = app.globalData.memberLevel || 'S'

    // SS仅当天, SSS提前3天, 默认7天
    let maxDays = 7
    if (level === 'SS') maxDays = 1
    else if (level === 'SSS') maxDays = 4  // 今天 + 3天

    for (let i = 0; i < maxDays; i++) {
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

      const types = (res.data || []).map(type => ({
        ...type,
        iconPath: SPORT_ICON_MAP[(type.icon || '').toLowerCase()] || SPORT_ICON_MAP.basketball
      }))
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
      this.showGuestTip()
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
