const app = getApp()
const { upload } = require('../../utils/request')

Page({
  data: {
    categories: [
      { key: 'suggestion', name: '建议' },
      { key: 'bug', name: 'Bug' },
      { key: 'complaint', name: '投诉' },
      { key: 'other', name: '其他' }
    ],
    selectedCategory: 'suggestion',
    content: '',
    contentLength: 0,
    images: [],
    contact: '',
    submitting: false,
    // 反馈历史
    feedbackList: [],
    expandedId: null
  },

  onLoad() {
    this.loadMyFeedback()
  },

  // 选择反馈类型
  selectCategory(e) {
    this.setData({ selectedCategory: e.currentTarget.dataset.key })
  },

  // 内容输入
  onContentInput(e) {
    this.setData({
      content: e.detail.value,
      contentLength: e.detail.value.length
    })
  },

  // 联系方式输入
  onContactInput(e) {
    this.setData({ contact: e.detail.value })
  },

  // 选择图片
  chooseImage() {
    const remaining = 3 - this.data.images.length
    if (remaining <= 0) {
      wx.showToast({ title: '最多上传3张图片', icon: 'none' })
      return
    }
    wx.chooseMedia({
      count: remaining,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const files = res.tempFiles
        files.forEach(file => this.uploadImage(file.tempFilePath))
      }
    })
  },

  // 上传图片
  async uploadImage(filePath) {
    try {
      wx.showLoading({ title: '上传中...' })
      const res = await upload('/upload/image?folder=feedback', filePath, 'file')
      if (res.data && res.data.url) {
        const images = [...this.data.images, res.data.url]
        this.setData({ images })
      }
    } catch (err) {
      console.error('上传图片失败:', err)
      wx.showToast({ title: '上传失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  // 删除图片
  removeImage(e) {
    const index = e.currentTarget.dataset.index
    const images = [...this.data.images]
    images.splice(index, 1)
    this.setData({ images })
  },

  // 预览图片
  previewImage(e) {
    const url = e.currentTarget.dataset.url
    const urls = this.data.images.map(img => app.resolveImageUrl(img))
    wx.previewImage({
      current: app.resolveImageUrl(url),
      urls: urls
    })
  },

  // 提交反馈
  async submitFeedback() {
    const { selectedCategory, content, images, contact } = this.data

    if (!content || content.trim().length < 10) {
      wx.showToast({ title: '反馈内容至少10个字', icon: 'none' })
      return
    }

    this.setData({ submitting: true })

    try {
      const res = await app.request({
        url: '/member/feedback',
        method: 'POST',
        data: {
          category: selectedCategory,
          content: content.trim(),
          images: images.length > 0 ? JSON.stringify(images) : null,
          contact: contact || null
        }
      })

      if (res.code === 200) {
        wx.showToast({ title: '提交成功', icon: 'success' })
        this.setData({
          content: '',
          contentLength: 0,
          images: [],
          contact: '',
          selectedCategory: 'suggestion'
        })
        this.loadMyFeedback()
      }
    } catch (err) {
      console.error('提交反馈失败:', err)
      wx.showToast({ title: '提交失败', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // 加载反馈历史
  async loadMyFeedback() {
    try {
      const res = await app.request({
        url: '/member/feedback',
        data: { page: 1, page_size: 50 },
        showError: false
      })
      if (res.code === 200) {
        this.setData({ feedbackList: res.data.list || [] })
      }
    } catch (err) {
      console.error('加载反馈历史失败:', err)
    }
  },

  // 展开/收起反馈详情
  toggleExpand(e) {
    const id = e.currentTarget.dataset.id
    this.setData({
      expandedId: this.data.expandedId === id ? null : id
    })
  }
})
