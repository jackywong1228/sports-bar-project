const app = getApp()
const api = require('../../utils/api')

// 分类 Tab（对应后端 category 四选一）
const TABS = [
  { key: 'group', label: '团课' },
  { key: 'golf', label: '高尔夫' },
  { key: 'squash', label: '壁球' },
  { key: 'pickleball', label: '匹克球' },
]

const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

// 「2026-01-24 10:00」→「周六 10:00」（今天/明天特殊处理）
function formatSessionTime(timeStr) {
  if (!timeStr) return ''
  const dt = new Date(timeStr.replace(/-/g, '/'))
  if (isNaN(dt.getTime())) return timeStr
  const now = new Date()
  const dayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const targetStart = new Date(dt.getFullYear(), dt.getMonth(), dt.getDate()).getTime()
  const diffDays = Math.round((targetStart - dayStart) / 86400000)
  const hh = String(dt.getHours()).padStart(2, '0')
  const mm = String(dt.getMinutes()).padStart(2, '0')
  let dayLabel
  if (diffDays === 0) dayLabel = '今天'
  else if (diffDays === 1) dayLabel = '明天'
  else dayLabel = WEEKDAYS[dt.getDay()]
  return `${dayLabel} ${hh}:${mm}`
}

Page({
  data: {
    tabs: TABS,
    activeTab: 'group',
    courses: [],
    loading: false,
    loaded: false,
  },

  onLoad(options) {
    // 支持从分享/入口带分类参数进入
    if (options && options.category && TABS.some(t => t.key === options.category)) {
      this.setData({ activeTab: options.category })
    }
    this.loadCourses()
  },

  onPullDownRefresh() {
    this.loadCourses().finally(() => wx.stopPullDownRefresh())
  },

  onTabChange(e) {
    const key = e.currentTarget.dataset.key
    if (key === this.data.activeTab) return
    this.setData({ activeTab: key, courses: [], loaded: false })
    this.loadCourses()
  },

  async loadCourses() {
    if (this.data.loading) return
    this.setData({ loading: true })
    try {
      const res = await api.getCourseList({ category: this.data.activeTab })
      const list = (res.data || []).map(item => ({
        ...item,
        cover_image: app.resolveImageUrl(item.cover_image),
        coach_avatar: app.resolveImageUrl(item.coach_avatar),
        nearest_time_text: item.nearest_session_time
          ? formatSessionTime(item.nearest_session_time)
          : '近期开课',
        coach_initial: (item.coach_name || '教').charAt(0),
      }))
      this.setData({ courses: list, loaded: true })
    } catch (err) {
      console.error('加载课程列表失败:', err)
      this.setData({ courses: [], loaded: true })
    } finally {
      this.setData({ loading: false })
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/course-detail/course-detail?id=${id}` })
  },
})
