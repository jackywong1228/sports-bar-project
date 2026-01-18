const app = getApp()

Page({
  data: {
    // 分类数据
    categories: [
      { key: '', name: '全部' },
      { key: 'golf', name: '高尔夫' },
      { key: 'pickleball', name: '匹克球' },
      { key: 'tennis', name: '网球' },
      { key: 'squash', name: '壁球' }
    ],
    currentCategory: '',

    // 组队列表
    teams: [],
    loading: true,

    // 发起组队弹窗
    showCreateModal: false,
    formData: {
      title: '',
      sport_type: 'golf',
      description: '',
      activity_date: '',
      activity_time: '',
      location: '',
      max_members: 4,
      fee_type: 'AA',
      fee_amount: 0
    },

    // 选择器数据
    sportTypeOptions: [
      { key: 'golf', name: '高尔夫' },
      { key: 'pickleball', name: '匹克球' },
      { key: 'tennis', name: '网球' },
      { key: 'squash', name: '壁球' }
    ],
    sportTypeIndex: 0,
    feeTypeOptions: [
      { key: 'free', name: '免费' },
      { key: 'AA', name: 'AA均摊' },
      { key: 'fixed', name: '固定费用' }
    ],
    feeTypeIndex: 1,
    maxMembersOptions: ['2', '3', '4', '5', '6', '8', '10'],
    maxMembersIndex: 2,

    // 日期时间
    minDate: '',
    submitting: false
  },

  onLoad() {
    this.initDateRange()
    this.loadTeams()
  },

  onShow() {
    this.loadTeams()
  },

  onPullDownRefresh() {
    this.loadTeams().then(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 初始化日期范围
  initDateRange() {
    const today = new Date()
    const minDate = this.formatDate(today)
    this.setData({ minDate })
  },

  formatDate(date) {
    const y = date.getFullYear()
    const m = String(date.getMonth() + 1).padStart(2, '0')
    const d = String(date.getDate()).padStart(2, '0')
    return `${y}-${m}-${d}`
  },

  // 切换分类
  switchCategory(e) {
    const key = e.currentTarget.dataset.key
    this.setData({ currentCategory: key })
    this.loadTeams()
  },

  // 加载组队列表
  async loadTeams() {
    this.setData({ loading: true })
    try {
      const params = {}
      if (this.data.currentCategory) {
        params.sport_type = this.data.currentCategory
      }
      const res = await app.request({
        url: '/member/teams',
        data: params
      })
      this.setData({ teams: res.data || [], loading: false })
    } catch (err) {
      console.error('加载组队列表失败', err)
      this.setData({ loading: false })
    }
  },

  // 跳转详情
  goToDetail(e) {
    wx.navigateTo({
      url: `/pages/team-detail/team-detail?id=${e.currentTarget.dataset.id}`
    })
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

  // 显示发起组队弹窗
  createTeam() {
    if (!app.checkLogin()) return

    // 重置表单
    this.setData({
      showCreateModal: true,
      formData: {
        title: '',
        sport_type: 'golf',
        description: '',
        activity_date: '',
        activity_time: '',
        location: '',
        max_members: 4,
        fee_type: 'AA',
        fee_amount: 0
      },
      sportTypeIndex: 0,
      feeTypeIndex: 1,
      maxMembersIndex: 2
    })
  },

  // 关闭弹窗
  closeModal() {
    this.setData({ showCreateModal: false })
  },

  // 阻止冒泡
  stopPropagation() {},

  // 输入标题
  onTitleInput(e) {
    this.setData({ 'formData.title': e.detail.value })
  },

  // 输入描述
  onDescInput(e) {
    this.setData({ 'formData.description': e.detail.value })
  },

  // 输入地点
  onLocationInput(e) {
    this.setData({ 'formData.location': e.detail.value })
  },

  // 输入费用
  onFeeInput(e) {
    this.setData({ 'formData.fee_amount': parseInt(e.detail.value) || 0 })
  },

  // 选择运动类型
  onSportTypeChange(e) {
    const index = e.detail.value
    const sportType = this.data.sportTypeOptions[index].key
    this.setData({
      sportTypeIndex: index,
      'formData.sport_type': sportType
    })
  },

  // 选择日期
  onDateChange(e) {
    this.setData({ 'formData.activity_date': e.detail.value })
  },

  // 选择时间
  onTimeChange(e) {
    this.setData({ 'formData.activity_time': e.detail.value })
  },

  // 选择人数
  onMaxMembersChange(e) {
    const index = e.detail.value
    const maxMembers = parseInt(this.data.maxMembersOptions[index])
    this.setData({
      maxMembersIndex: index,
      'formData.max_members': maxMembers
    })
  },

  // 选择费用类型
  onFeeTypeChange(e) {
    const index = e.detail.value
    const feeType = this.data.feeTypeOptions[index].key
    this.setData({
      feeTypeIndex: index,
      'formData.fee_type': feeType
    })
  },

  // 提交发起组队
  async submitCreate() {
    const { formData } = this.data

    // 验证
    if (!formData.title.trim()) {
      return wx.showToast({ title: '请输入组队标题', icon: 'none' })
    }
    if (!formData.activity_date) {
      return wx.showToast({ title: '请选择活动日期', icon: 'none' })
    }
    if (!formData.activity_time) {
      return wx.showToast({ title: '请选择活动时间', icon: 'none' })
    }

    this.setData({ submitting: true })

    try {
      await app.request({
        url: '/member/teams',
        method: 'POST',
        data: formData
      })

      wx.showToast({ title: '发起成功', icon: 'success' })
      this.setData({ showCreateModal: false })
      this.loadTeams()
    } catch (err) {
      console.error('发起组队失败', err)
      wx.showToast({ title: err.message || '发起失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  }
})
