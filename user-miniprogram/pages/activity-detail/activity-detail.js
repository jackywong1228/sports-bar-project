const app = getApp()

Page({
  data: {
    activityId: null,
    activity: {},
    isEnrolled: false,
    loading: true,
    submitting: false
  },

  onLoad(options) {
    this.setData({ activityId: options.id })
    this.loadActivityDetail()
  },

  // 加载活动详情
  async loadActivityDetail() {
    try {
      const res = await app.request({
        url: `/member/activities/${this.data.activityId}`
      })

      const activity = res.data || {}
      activity.statusInfo = this.getActivityStatus(activity)

      this.setData({
        activity,
        isEnrolled: activity.is_enrolled || false,
        loading: false
      })
    } catch (err) {
      console.error('加载活动详情失败:', err)
      this.setData({ loading: false })
    }
  },

  // 获取活动状态
  getActivityStatus(activity) {
    const now = new Date()
    const startDate = new Date(`${activity.start_date} ${activity.start_time || '00:00'}`)
    const endDate = new Date(`${activity.end_date || activity.start_date} ${activity.end_time || '23:59'}`)

    if (now < startDate) {
      return { text: '即将开始', class: 'upcoming', canEnroll: true }
    } else if (now > endDate) {
      return { text: '已结束', class: 'ended', canEnroll: false }
    } else {
      return { text: '进行中', class: 'ongoing', canEnroll: true }
    }
  },

  // 报名活动
  async enrollActivity() {
    if (!app.checkLogin()) return

    const { activity, isEnrolled } = this.data

    if (isEnrolled) {
      wx.showToast({ title: '您已报名', icon: 'none' })
      return
    }

    if (!activity.statusInfo.canEnroll) {
      wx.showToast({ title: '活动已结束', icon: 'none' })
      return
    }

    if (activity.max_participants && activity.enrolled >= activity.max_participants) {
      wx.showToast({ title: '报名已满', icon: 'none' })
      return
    }

    this.setData({ submitting: true })

    try {
      await app.request({
        url: `/member/activities/${this.data.activityId}/enroll`,
        method: 'POST'
      })

      wx.showToast({
        title: '报名成功',
        icon: 'success'
      })

      this.setData({
        isEnrolled: true,
        'activity.enrolled': (this.data.activity.enrolled || 0) + 1
      })
    } catch (err) {
      console.error('报名失败:', err)
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 取消报名
  async cancelEnroll() {
    wx.showModal({
      title: '取消报名',
      content: '确定要取消报名吗？',
      success: async (res) => {
        if (res.confirm) {
          this.setData({ submitting: true })

          try {
            await app.request({
              url: `/member/activities/${this.data.activityId}/cancel`,
              method: 'POST'
            })

            wx.showToast({
              title: '已取消报名',
              icon: 'success'
            })

            this.setData({
              isEnrolled: false,
              'activity.enrolled': Math.max(0, (this.data.activity.enrolled || 1) - 1)
            })
          } catch (err) {
            console.error('取消失败:', err)
          } finally {
            this.setData({ submitting: false })
          }
        }
      }
    })
  },

  // 分享
  onShareAppMessage() {
    return {
      title: this.data.activity.title || '活动报名',
      path: `/pages/activity-detail/activity-detail?id=${this.data.activityId}`,
      imageUrl: this.data.activity.image
    }
  }
})
