const app = getApp()

Page({
  data: {
    id: null,
    team: {},
    loading: true,
    isCreator: false,
    hasJoined: false,
    submitting: false
  },

  onLoad(options) {
    this.setData({ id: options.id })
    this.loadDetail()
  },

  onShow() {
    if (this.data.id) {
      this.loadDetail()
    }
  },

  async loadDetail() {
    this.setData({ loading: true })
    try {
      const res = await app.request({ url: `/member/teams/${this.data.id}` })
      const team = res.data || {}

      // 获取当前用户ID
      const userInfo = app.globalData.userInfo
      const memberId = userInfo ? userInfo.id : null

      // 判断是否是创建者
      const isCreator = team.creator_id === memberId

      // 判断是否已加入
      let hasJoined = false
      if (team.members && memberId) {
        hasJoined = team.members.some(m => m.member_id === memberId && m.status === 'joined')
      }

      this.setData({
        team,
        isCreator,
        hasJoined,
        loading: false
      })
    } catch (err) {
      console.error('加载组队详情失败', err)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  // 获取运动类型中文名
  getSportTypeName(key) {
    const map = {
      golf: '高尔夫',
      pickleball: '匹克球',
      tennis: '网球',
      squash: '壁球'
    }
    return map[key] || key
  },

  // 加入队伍
  async joinTeam() {
    if (!app.checkLogin()) return

    const { team } = this.data
    if (team.status !== 'recruiting') {
      return wx.showToast({ title: '该组队已停止招募', icon: 'none' })
    }

    if (team.current_members >= team.max_members) {
      return wx.showToast({ title: '队伍已满员', icon: 'none' })
    }

    this.setData({ submitting: true })
    try {
      await app.request({
        url: `/member/teams/${this.data.id}/join`,
        method: 'POST'
      })
      wx.showToast({ title: '加入成功', icon: 'success' })
      this.loadDetail()
    } catch (err) {
      console.error('加入失败', err)
      wx.showToast({ title: err.message || '加入失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 退出队伍
  async quitTeam() {
    const res = await wx.showModal({
      title: '确认退出',
      content: '确定要退出这个组队吗？'
    })

    if (!res.confirm) return

    this.setData({ submitting: true })
    try {
      await app.request({
        url: `/member/teams/${this.data.id}/quit`,
        method: 'POST'
      })
      wx.showToast({ title: '已退出', icon: 'success' })
      this.loadDetail()
    } catch (err) {
      console.error('退出失败', err)
      wx.showToast({ title: err.message || '退出失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 联系队长
  contactCreator() {
    const { team } = this.data
    if (team.creator && team.creator.phone) {
      wx.makePhoneCall({
        phoneNumber: team.creator.phone,
        fail: () => {
          wx.showToast({ title: '无法拨打电话', icon: 'none' })
        }
      })
    } else {
      wx.showToast({ title: '暂无联系方式', icon: 'none' })
    }
  },

  // 分享
  onShareAppMessage() {
    const { team } = this.data
    return {
      title: team.title || '一起来组队',
      path: `/pages/team-detail/team-detail?id=${this.data.id}`
    }
  }
})
