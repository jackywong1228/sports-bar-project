const app = getApp()

// 订阅消息模板ID列表
const TEMPLATE_IDS = [
  '7hfiuhhgsLvrJB1iUDYvjNNgcs_a6CetffrnAEYpOAM'  // 优惠券到账通知
  // 后续可以添加更多模板ID
]

Page({
  data: {},

  // 订阅消息通知
  subscribeMessages() {
    wx.requestSubscribeMessage({
      tmplIds: TEMPLATE_IDS,
      success: (res) => {
        console.log('订阅结果:', res)
        // 检查订阅结果
        let successCount = 0
        let rejectCount = 0

        TEMPLATE_IDS.forEach(id => {
          if (res[id] === 'accept') {
            successCount++
          } else if (res[id] === 'reject') {
            rejectCount++
          }
        })

        if (successCount > 0) {
          wx.showToast({
            title: '订阅成功',
            icon: 'success'
          })
        } else if (rejectCount > 0) {
          wx.showModal({
            title: '订阅提示',
            content: '您已拒绝接收消息通知，如需接收优惠券等通知，请在小程序设置中开启',
            showCancel: false
          })
        }
      },
      fail: (err) => {
        console.error('订阅失败:', err)
        if (err.errCode === 20004) {
          wx.showModal({
            title: '提示',
            content: '订阅消息功能被关闭，请在小程序设置中开启',
            showCancel: false
          })
        } else {
          wx.showToast({
            title: '订阅失败',
            icon: 'none'
          })
        }
      }
    })
  },

  // 清除缓存
  clearCache() {
    wx.showModal({
      title: '清除缓存',
      content: '确定要清除缓存吗？',
      success: (res) => {
        if (res.confirm) {
          wx.clearStorageSync()
          wx.showToast({ title: '已清除', icon: 'success' })
        }
      }
    })
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.logout()
        }
      }
    })
  }
})
