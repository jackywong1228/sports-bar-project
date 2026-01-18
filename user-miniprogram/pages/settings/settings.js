const app = getApp()
Page({
  data: {},
  clearCache() {
    wx.showModal({
      title: '清除缓存', content: '确定要清除缓存吗？',
      success: (res) => { if (res.confirm) { wx.clearStorageSync(); wx.showToast({ title: '已清除', icon: 'success' }) } }
    })
  },
  logout() {
    wx.showModal({
      title: '退出登录', content: '确定要退出登录吗？',
      success: (res) => { if (res.confirm) { app.logout() } }
    })
  }
})
