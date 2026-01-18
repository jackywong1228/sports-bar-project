import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getUserInfo as getUserInfoApi, logout as logoutApi, type UserInfo, type LoginParams } from '@/api/auth'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const permissions = computed(() => userInfo.value?.permissions || [])

  async function login(params: LoginParams) {
    const res = await loginApi(params)
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    const res = await getUserInfoApi()
    userInfo.value = res.data
  }

  async function logout() {
    try {
      await logoutApi()
    } catch (e) {
      // 忽略登出错误
    }
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
    router.push('/login')
  }

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    permissions,
    login,
    fetchUserInfo,
    logout,
    hasPermission
  }
})
