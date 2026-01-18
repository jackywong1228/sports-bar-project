import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface UserInfo {
  id: number
  username: string
  name: string
  avatar: string | null
  phone: string | null
  email: string | null
  department_id: number | null
  department_name: string | null
  roles: string[]
  permissions: string[]
}

export function login(data: LoginParams) {
  return request.post('/auth/login', data)
}

export function getUserInfo() {
  return request.get('/auth/userinfo')
}

export function logout() {
  return request.post('/auth/logout')
}
