Page({
  data: {
    url: ''
  },

  onLoad(options) {
    if (options.url) {
      const url = decodeURIComponent(options.url)
      this.setData({ url })
    } else {
      wx.showToast({ title: '链接无效', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
    }
  },

  // web-view 加载失败（如域名未配置业务域名）时给出提示
  onError(e) {
    console.error('[WEBVIEW] 加载失败:', e.detail)
    wx.showModal({
      title: '提示',
      content: '页面加载失败，请确认该链接已在小程序后台配置为业务域名',
      showCancel: false
    })
  }
})
