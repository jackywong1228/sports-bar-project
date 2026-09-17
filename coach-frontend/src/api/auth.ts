import request from '@/utils/request'

// 教练登录（手机号 + 密码），返回 data: { access_token, token_type, coach_id, name }
export function login(data: { phone: string; password: string }) {
  return request.post('/coach/auth/login', data)
}

// 教练个人信息
export function getProfile() {
  return request.get('/coach/profile')
}
