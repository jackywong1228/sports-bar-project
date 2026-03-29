import axios, { type AxiosInstance, type AxiosResponse } from 'axios'
import { showToast } from 'vant'
import router from '@/router'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('staff_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 标记是否正在处理401
let isHandling401 = false

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    if (res.code !== 200) {
      showToast(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        if (!isHandling401) {
          isHandling401 = true
          showToast('登录已过期，请重新登录')
          localStorage.removeItem('staff_token')
          router.push('/login')
          setTimeout(() => {
            isHandling401 = false
          }, 1000)
        }
      } else if (status === 403) {
        showToast('没有权限访问')
      } else {
        showToast(data?.detail || data?.message || '请求失败')
      }
    } else {
      showToast('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default service
