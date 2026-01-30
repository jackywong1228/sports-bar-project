/**
 * 网络请求封装
 * 基于微信小程序 wx.request API
 */

const app = getApp()

// 请求队列（用于请求去重）
const pendingRequests = new Map()

// 生成请求key
const generateRequestKey = (config) => {
  return `${config.method || 'GET'}_${config.url}_${JSON.stringify(config.data || {})}`
}

// 请求拦截器
const requestInterceptor = (config) => {
  // 添加token
  const token = app.globalData.token || wx.getStorageSync('token')
  if (token) {
    config.header = {
      ...config.header,
      'Authorization': `Bearer ${token}`
    }
  }

  // 默认Content-Type
  config.header = {
    'Content-Type': 'application/json',
    ...config.header
  }

  return config
}

// 响应拦截器
const responseInterceptor = (response, config) => {
  const { statusCode, data } = response

  // 401 未授权
  if (statusCode === 401) {
    wx.removeStorageSync('token')
    app.globalData.token = ''
    app.globalData.memberInfo = null

    // 跳转登录页
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    if (currentPage && currentPage.route !== 'pages/login/login') {
      wx.navigateTo({ url: '/pages/login/login' })
    }

    return Promise.reject({ code: 401, message: '登录已过期，请重新登录' })
  }

  // 403 禁止访问
  if (statusCode === 403) {
    return Promise.reject({ code: 403, message: '没有访问权限' })
  }

  // 404 资源不存在
  if (statusCode === 404) {
    return Promise.reject({ code: 404, message: '请求的资源不存在' })
  }

  // 500 服务器错误
  if (statusCode >= 500) {
    return Promise.reject({ code: statusCode, message: '服务器繁忙，请稍后重试' })
  }

  // 业务响应处理
  if (statusCode === 200) {
    // 后端返回的统一格式
    if (data.code === 200 || data.code === 0) {
      return Promise.resolve(data)
    }
    return Promise.reject(data)
  }

  return Promise.reject({ code: statusCode, message: '请求失败' })
}

/**
 * 发起网络请求
 * @param {Object} options 请求配置
 * @param {string} options.url 请求地址
 * @param {string} options.method 请求方法 GET|POST|PUT|DELETE
 * @param {Object} options.data 请求数据
 * @param {Object} options.header 请求头
 * @param {boolean} options.showLoading 是否显示加载提示
 * @param {string} options.loadingText 加载提示文字
 * @param {boolean} options.showError 是否显示错误提示
 * @param {boolean} options.dedupe 是否去重（相同请求只发一次）
 * @param {number} options.timeout 超时时间（毫秒）
 */
const request = (options) => {
  return new Promise((resolve, reject) => {
    // 拦截处理
    const config = requestInterceptor({
      url: `${app.globalData.baseUrl}${options.url}`,
      method: options.method || 'GET',
      data: options.data || {},
      header: options.header || {},
      timeout: options.timeout || 30000
    })

    // 请求去重
    const requestKey = generateRequestKey(config)
    if (options.dedupe && pendingRequests.has(requestKey)) {
      const pending = pendingRequests.get(requestKey)
      pending.then(resolve).catch(reject)
      return
    }

    // 显示加载提示
    if (options.showLoading) {
      wx.showLoading({
        title: options.loadingText || '加载中...',
        mask: true
      })
    }

    const requestTask = wx.request({
      ...config,
      success: (res) => {
        responseInterceptor(res, config)
          .then(resolve)
          .catch((err) => {
            if (options.showError !== false) {
              wx.showToast({
                title: err.message || '请求失败',
                icon: 'none',
                duration: 2000
              })
            }
            reject(err)
          })
      },
      fail: (err) => {
        // 详细记录网络错误
        console.error('[REQUEST FAIL] URL:', config.url)
        console.error('[REQUEST FAIL] Error:', JSON.stringify(err))
        console.error('[REQUEST FAIL] errMsg:', err.errMsg)
        console.error('[REQUEST FAIL] errno:', err.errno)

        let message = '网络错误'
        if (err.errMsg) {
          if (err.errMsg.includes('timeout')) {
            message = '请求超时'
          } else if (err.errMsg.includes('fail')) {
            message = '网络连接失败: ' + err.errMsg
          }
        }

        if (options.showError !== false) {
          wx.showToast({
            title: message,
            icon: 'none',
            duration: 2000
          })
        }
        reject({ code: -1, message, errMsg: err.errMsg, errno: err.errno })
      },
      complete: () => {
        // 隐藏加载提示
        if (options.showLoading) {
          wx.hideLoading()
        }
        // 移除请求队列
        pendingRequests.delete(requestKey)
      }
    })

    // 存入请求队列
    if (options.dedupe) {
      const promise = new Promise((res, rej) => {
        requestTask._resolve = res
        requestTask._reject = rej
      })
      pendingRequests.set(requestKey, promise)
    }
  })
}

// GET请求
const get = (url, data = {}, options = {}) => {
  return request({ ...options, url, method: 'GET', data })
}

// POST请求
const post = (url, data = {}, options = {}) => {
  return request({ ...options, url, method: 'POST', data })
}

// PUT请求
const put = (url, data = {}, options = {}) => {
  return request({ ...options, url, method: 'PUT', data })
}

// DELETE请求
const del = (url, data = {}, options = {}) => {
  return request({ ...options, url, method: 'DELETE', data })
}

/**
 * 上传文件
 * @param {string} url 上传地址
 * @param {string} filePath 文件路径
 * @param {string} name 文件对应的key
 * @param {Object} formData 额外的表单数据
 */
const upload = (url, filePath, name = 'file', formData = {}) => {
  return new Promise((resolve, reject) => {
    const token = app.globalData.token || wx.getStorageSync('token')

    wx.uploadFile({
      url: `${app.globalData.baseUrl}${url}`,
      filePath,
      name,
      formData,
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        if (res.statusCode === 200) {
          try {
            const data = JSON.parse(res.data)
            if (data.code === 200 || data.code === 0) {
              resolve(data)
            } else {
              reject(data)
            }
          } catch (e) {
            reject({ code: -1, message: '解析响应失败' })
          }
        } else {
          reject({ code: res.statusCode, message: '上传失败' })
        }
      },
      fail: (err) => {
        reject({ code: -1, message: err.errMsg || '上传失败' })
      }
    })
  })
}

/**
 * 下载文件
 * @param {string} url 下载地址
 */
const download = (url) => {
  return new Promise((resolve, reject) => {
    wx.downloadFile({
      url,
      success: (res) => {
        if (res.statusCode === 200) {
          resolve(res.tempFilePath)
        } else {
          reject({ code: res.statusCode, message: '下载失败' })
        }
      },
      fail: (err) => {
        reject({ code: -1, message: err.errMsg || '下载失败' })
      }
    })
  })
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  upload,
  download
}
