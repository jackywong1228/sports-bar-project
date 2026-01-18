/**
 * 微信小程序API封装
 * 基于微信官方API，Promise化处理
 */

// ==================== 登录相关 ====================

/**
 * 微信登录，获取code
 * @returns {Promise<{code: string}>}
 */
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

/**
 * 检查登录态是否过期
 * @returns {Promise<void>}
 */
const checkSession = () => {
  return new Promise((resolve, reject) => {
    wx.checkSession({
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 获取用户信息（需要button授权）
 * @returns {Promise<Object>}
 */
const getUserProfile = () => {
  return new Promise((resolve, reject) => {
    wx.getUserProfile({
      desc: '用于完善用户资料',
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 位置相关 ====================

/**
 * 获取当前位置
 * @param {string} type 坐标类型 wgs84|gcj02
 * @returns {Promise<{latitude: number, longitude: number}>}
 */
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

/**
 * 选择位置
 * @returns {Promise<{name: string, address: string, latitude: number, longitude: number}>}
 */
const chooseLocation = () => {
  return new Promise((resolve, reject) => {
    wx.chooseLocation({
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 打开地图查看位置
 * @param {number} latitude 纬度
 * @param {number} longitude 经度
 * @param {string} name 位置名称
 * @param {string} address 详细地址
 */
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

// ==================== 支付相关 ====================

/**
 * 发起微信支付
 * @param {Object} payParams 支付参数（后端返回）
 * @returns {Promise<void>}
 */
const requestPayment = (payParams) => {
  return new Promise((resolve, reject) => {
    wx.requestPayment({
      timeStamp: payParams.timeStamp,
      nonceStr: payParams.nonceStr,
      package: payParams.package,
      signType: payParams.signType || 'MD5',
      paySign: payParams.paySign,
      success: resolve,
      fail: (err) => {
        if (err.errMsg && err.errMsg.includes('cancel')) {
          reject({ errMsg: '取消支付', cancelled: true })
        } else {
          reject(err)
        }
      }
    })
  })
}

// ==================== 扫码相关 ====================

/**
 * 扫描二维码/条形码
 * @param {boolean} onlyFromCamera 是否只能从相机扫码
 * @param {Array} scanType 扫码类型 barCode|qrCode
 * @returns {Promise<{result: string, scanType: string}>}
 */
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

/**
 * 选择图片
 * @param {number} count 最多选择图片数量
 * @param {Array} sizeType 图片尺寸 original|compressed
 * @param {Array} sourceType 来源 album|camera
 * @returns {Promise<{tempFilePaths: string[], tempFiles: Object[]}>}
 */
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

/**
 * 选择媒体（图片/视频）
 * @param {Object} options 配置参数
 * @returns {Promise<{tempFiles: Object[], type: string}>}
 */
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

/**
 * 预览图片
 * @param {string} current 当前显示图片的链接
 * @param {Array} urls 需要预览的图片链接列表
 */
const previewImage = (current, urls) => {
  wx.previewImage({
    current,
    urls
  })
}

/**
 * 保存图片到相册
 * @param {string} filePath 图片文件路径
 * @returns {Promise<void>}
 */
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

/**
 * 获取系统信息
 * @returns {Object}
 */
const getSystemInfoSync = () => {
  return wx.getSystemInfoSync()
}

/**
 * 获取系统信息（异步）
 * @returns {Promise<Object>}
 */
const getSystemInfo = () => {
  return new Promise((resolve, reject) => {
    wx.getSystemInfo({
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 获取设备信息
 * @returns {Promise<Object>}
 */
const getDeviceInfo = () => {
  return new Promise((resolve, reject) => {
    wx.getDeviceInfo({
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 缓存相关 ====================

/**
 * 设置缓存
 * @param {string} key 键
 * @param {any} data 值
 */
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

/**
 * 获取缓存
 * @param {string} key 键
 * @returns {Promise<any>}
 */
const getStorage = (key) => {
  return new Promise((resolve, reject) => {
    wx.getStorage({
      key,
      success: (res) => resolve(res.data),
      fail: reject
    })
  })
}

/**
 * 移除缓存
 * @param {string} key 键
 */
const removeStorage = (key) => {
  return new Promise((resolve, reject) => {
    wx.removeStorage({
      key,
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 清空缓存
 */
const clearStorage = () => {
  return new Promise((resolve, reject) => {
    wx.clearStorage({
      success: resolve,
      fail: reject
    })
  })
}

// 同步版本
const setStorageSync = (key, data) => wx.setStorageSync(key, data)
const getStorageSync = (key) => wx.getStorageSync(key)
const removeStorageSync = (key) => wx.removeStorageSync(key)
const clearStorageSync = () => wx.clearStorageSync()

// ==================== 交互反馈 ====================

/**
 * 显示消息提示框
 * @param {string} title 提示内容
 * @param {string} icon 图标类型 success|loading|none
 * @param {number} duration 持续时间
 */
const showToast = (title, icon = 'none', duration = 2000) => {
  wx.showToast({ title, icon, duration })
}

/**
 * 显示加载提示框
 * @param {string} title 提示内容
 * @param {boolean} mask 是否显示透明蒙层
 */
const showLoading = (title = '加载中...', mask = true) => {
  wx.showLoading({ title, mask })
}

/**
 * 隐藏加载提示框
 */
const hideLoading = () => {
  wx.hideLoading()
}

/**
 * 显示模态对话框
 * @param {Object} options 配置
 * @returns {Promise<{confirm: boolean, cancel: boolean}>}
 */
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

/**
 * 显示操作菜单
 * @param {Array} itemList 菜单项
 * @returns {Promise<{tapIndex: number}>}
 */
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

/**
 * 保留当前页面，跳转到应用内的某个页面
 * @param {string} url 页面路径
 */
const navigateTo = (url) => {
  return new Promise((resolve, reject) => {
    wx.navigateTo({ url, success: resolve, fail: reject })
  })
}

/**
 * 关闭当前页面，跳转到应用内的某个页面
 * @param {string} url 页面路径
 */
const redirectTo = (url) => {
  return new Promise((resolve, reject) => {
    wx.redirectTo({ url, success: resolve, fail: reject })
  })
}

/**
 * 跳转到tabBar页面
 * @param {string} url 页面路径
 */
const switchTab = (url) => {
  return new Promise((resolve, reject) => {
    wx.switchTab({ url, success: resolve, fail: reject })
  })
}

/**
 * 关闭所有页面，打开应用内的某个页面
 * @param {string} url 页面路径
 */
const reLaunch = (url) => {
  return new Promise((resolve, reject) => {
    wx.reLaunch({ url, success: resolve, fail: reject })
  })
}

/**
 * 返回上一页面
 * @param {number} delta 返回的页面数
 */
const navigateBack = (delta = 1) => {
  return new Promise((resolve, reject) => {
    wx.navigateBack({ delta, success: resolve, fail: reject })
  })
}

// ==================== 授权相关 ====================

/**
 * 获取授权设置
 * @returns {Promise<{authSetting: Object}>}
 */
const getSetting = () => {
  return new Promise((resolve, reject) => {
    wx.getSetting({
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 打开设置页面
 * @returns {Promise<{authSetting: Object}>}
 */
const openSetting = () => {
  return new Promise((resolve, reject) => {
    wx.openSetting({
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 提前向用户发起授权请求
 * @param {string} scope 需要获取权限的scope
 * @returns {Promise<void>}
 */
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

/**
 * 调起客户端小程序订阅消息界面
 * @param {Array} tmplIds 模板ID数组
 * @returns {Promise<Object>}
 */
const requestSubscribeMessage = (tmplIds) => {
  return new Promise((resolve, reject) => {
    wx.requestSubscribeMessage({
      tmplIds,
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 分享相关 ====================

/**
 * 显示分享菜单
 * @param {Array} menus 分享按钮 shareAppMessage|shareTimeline
 */
const showShareMenu = (menus = ['shareAppMessage', 'shareTimeline']) => {
  return new Promise((resolve, reject) => {
    wx.showShareMenu({
      menus,
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 隐藏分享菜单
 */
const hideShareMenu = () => {
  return new Promise((resolve, reject) => {
    wx.hideShareMenu({
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 剪贴板 ====================

/**
 * 设置剪贴板内容
 * @param {string} data 内容
 */
const setClipboardData = (data) => {
  return new Promise((resolve, reject) => {
    wx.setClipboardData({
      data,
      success: resolve,
      fail: reject
    })
  })
}

/**
 * 获取剪贴板内容
 * @returns {Promise<{data: string}>}
 */
const getClipboardData = () => {
  return new Promise((resolve, reject) => {
    wx.getClipboardData({
      success: resolve,
      fail: reject
    })
  })
}

// ==================== 拨打电话 ====================

/**
 * 拨打电话
 * @param {string} phoneNumber 电话号码
 */
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

/**
 * 使手机发生短振动
 * @param {string} type heavy|medium|light
 */
const vibrateShort = (type = 'medium') => {
  wx.vibrateShort({ type })
}

/**
 * 使手机发生长振动
 */
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
  chooseLocation,
  openLocation,

  // 支付
  requestPayment,

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
  getDeviceInfo,

  // 缓存
  setStorage,
  getStorage,
  removeStorage,
  clearStorage,
  setStorageSync,
  getStorageSync,
  removeStorageSync,
  clearStorageSync,

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

  // 分享
  showShareMenu,
  hideShareMenu,

  // 剪贴板
  setClipboardData,
  getClipboardData,

  // 电话
  makePhoneCall,

  // 振动
  vibrateShort,
  vibrateLong
}
