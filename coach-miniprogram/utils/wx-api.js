/**
 * 微信小程序API封装（教练端）
 * 基于微信官方API，Promise化处理
 */

// ==================== 登录相关 ====================

const login = () => {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        if (res.code) {
          resolve(res)
        } else {
          reject({ errMsg: res.errMsg || '登录失败' })
        }
      },
      fail: reject
    })
  })
}

const checkSession = () => {
  return new Promise((resolve, reject) => {
    wx.checkSession({
      success: resolve,
      fail: reject
    })
  })
}

const getUserProfile = () => {
  return new Promise((resolve, reject) => {
    wx.getUserProfile({
      desc: '用于完善教练资料',
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 位置相关 ====================

const getLocation = (type = 'gcj02') => {
  return new Promise((resolve, reject) => {
    wx.getLocation({
      type,
      success: resolve,
      fail: (err) => {
        if (err.errMsg && err.errMsg.includes('auth deny')) {
          reject({ errMsg: '请授权位置信息' })
        } else {
          reject(err)
        }
      }
    })
  })
}

const openLocation = (latitude, longitude, name = '', address = '') => {
  return new Promise((resolve, reject) => {
    wx.openLocation({
      latitude,
      longitude,
      name,
      address,
      scale: 18,
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 扫码相关 ====================

const scanCode = (onlyFromCamera = false, scanType = ['qrCode', 'barCode']) => {
  return new Promise((resolve, reject) => {
    wx.scanCode({
      onlyFromCamera,
      scanType,
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 媒体相关 ====================

const chooseImage = (count = 9, sizeType = ['original', 'compressed'], sourceType = ['album', 'camera']) => {
  return new Promise((resolve, reject) => {
    wx.chooseImage({
      count,
      sizeType,
      sourceType,
      success: resolve,
      fail: reject
    })
  })
}

const chooseMedia = (options = {}) => {
  return new Promise((resolve, reject) => {
    wx.chooseMedia({
      count: options.count || 9,
      mediaType: options.mediaType || ['image', 'video'],
      sourceType: options.sourceType || ['album', 'camera'],
      maxDuration: options.maxDuration || 60,
      camera: options.camera || 'back',
      success: resolve,
      fail: reject
    })
  })
}

const previewImage = (current, urls) => {
  wx.previewImage({
    current,
    urls
  })
}

const saveImageToPhotosAlbum = (filePath) => {
  return new Promise((resolve, reject) => {
    wx.saveImageToPhotosAlbum({
      filePath,
      success: resolve,
      fail: (err) => {
        if (err.errMsg && err.errMsg.includes('auth deny')) {
          reject({ errMsg: '请授权保存到相册' })
        } else {
          reject(err)
        }
      }
    })
  })
}

// ==================== 系统信息 ====================

const getSystemInfoSync = () => {
  return wx.getSystemInfoSync()
}

const getSystemInfo = () => {
  return new Promise((resolve, reject) => {
    wx.getSystemInfo({
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 缓存相关 ====================

const setStorage = (key, data) => {
  return new Promise((resolve, reject) => {
    wx.setStorage({
      key,
      data,
      success: resolve,
      fail: reject
    })
  })
}

const getStorage = (key) => {
  return new Promise((resolve, reject) => {
    wx.getStorage({
      key,
      success: (res) => resolve(res.data),
      fail: reject
    })
  })
}

const removeStorage = (key) => {
  return new Promise((resolve, reject) => {
    wx.removeStorage({
      key,
      success: resolve,
      fail: reject
    })
  })
}

const setStorageSync = (key, data) => wx.setStorageSync(key, data)
const getStorageSync = (key) => wx.getStorageSync(key)
const removeStorageSync = (key) => wx.removeStorageSync(key)

// ==================== 交互反馈 ====================

const showToast = (title, icon = 'none', duration = 2000) => {
  wx.showToast({ title, icon, duration })
}

const showLoading = (title = '加载中...', mask = true) => {
  wx.showLoading({ title, mask })
}

const hideLoading = () => {
  wx.hideLoading()
}

const showModal = (options) => {
  return new Promise((resolve, reject) => {
    wx.showModal({
      title: options.title || '提示',
      content: options.content || '',
      showCancel: options.showCancel !== false,
      cancelText: options.cancelText || '取消',
      confirmText: options.confirmText || '确定',
      confirmColor: options.confirmColor || '#07c160',
      success: resolve,
      fail: reject
    })
  })
}

const showActionSheet = (itemList) => {
  return new Promise((resolve, reject) => {
    wx.showActionSheet({
      itemList,
      success: resolve,
      fail: (err) => {
        if (err.errMsg && err.errMsg.includes('cancel')) {
          reject({ cancelled: true })
        } else {
          reject(err)
        }
      }
    })
  })
}

// ==================== 导航相关 ====================

const navigateTo = (url) => {
  return new Promise((resolve, reject) => {
    wx.navigateTo({ url, success: resolve, fail: reject })
  })
}

const redirectTo = (url) => {
  return new Promise((resolve, reject) => {
    wx.redirectTo({ url, success: resolve, fail: reject })
  })
}

const switchTab = (url) => {
  return new Promise((resolve, reject) => {
    wx.switchTab({ url, success: resolve, fail: reject })
  })
}

const reLaunch = (url) => {
  return new Promise((resolve, reject) => {
    wx.reLaunch({ url, success: resolve, fail: reject })
  })
}

const navigateBack = (delta = 1) => {
  return new Promise((resolve, reject) => {
    wx.navigateBack({ delta, success: resolve, fail: reject })
  })
}

// ==================== 授权相关 ====================

const getSetting = () => {
  return new Promise((resolve, reject) => {
    wx.getSetting({
      success: resolve,
      fail: reject
    })
  })
}

const openSetting = () => {
  return new Promise((resolve, reject) => {
    wx.openSetting({
      success: resolve,
      fail: reject
    })
  })
}

const authorize = (scope) => {
  return new Promise((resolve, reject) => {
    wx.authorize({
      scope,
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 订阅消息 ====================

const requestSubscribeMessage = (tmplIds) => {
  return new Promise((resolve, reject) => {
    wx.requestSubscribeMessage({
      tmplIds,
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 剪贴板 ====================

const setClipboardData = (data) => {
  return new Promise((resolve, reject) => {
    wx.setClipboardData({
      data,
      success: resolve,
      fail: reject
    })
  })
}

const getClipboardData = () => {
  return new Promise((resolve, reject) => {
    wx.getClipboardData({
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 电话 ====================

const makePhoneCall = (phoneNumber) => {
  return new Promise((resolve, reject) => {
    wx.makePhoneCall({
      phoneNumber,
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 振动 ====================

const vibrateShort = (type = 'medium') => {
  wx.vibrateShort({ type })
}

const vibrateLong = () => {
  wx.vibrateLong()
}

module.exports = {
  // 登录
  login,
  checkSession,
  getUserProfile,

  // 位置
  getLocation,
  openLocation,

  // 扫码
  scanCode,

  // 媒体
  chooseImage,
  chooseMedia,
  previewImage,
  saveImageToPhotosAlbum,

  // 系统
  getSystemInfoSync,
  getSystemInfo,

  // 缓存
  setStorage,
  getStorage,
  removeStorage,
  setStorageSync,
  getStorageSync,
  removeStorageSync,

  // 交互
  showToast,
  showLoading,
  hideLoading,
  showModal,
  showActionSheet,

  // 导航
  navigateTo,
  redirectTo,
  switchTab,
  reLaunch,
  navigateBack,

  // 授权
  getSetting,
  openSetting,
  authorize,

  // 订阅消息
  requestSubscribeMessage,

  // 剪贴板
  setClipboardData,
  getClipboardData,

  // 电话
  makePhoneCall,

  // 振动
  vibrateShort,
  vibrateLong
}
