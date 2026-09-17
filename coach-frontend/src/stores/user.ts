import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getProfile } from '@/api/auth'
import router from '@/router'

export interface CoachInfo {
  id: number
  coach_no: string
  name: string
  avatar: string | null
  phone: string | null
  type: string | null
  type_name: string | null
  rating: number | null
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('coach_token') || '')
  const userInfo = ref<CoachInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(phone: string, password: string) {
    const res = await loginApi({ phone, password })
    token.value = res.data.access_token
    localStorage.setItem('coach_token', token.value)
    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    const res = await getProfile()
    userInfo.value = res.data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('coach_token')
    router.push('/login')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    login,
    fetchUserInfo,
    logout
  }
})
