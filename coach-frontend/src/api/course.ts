import request from '@/utils/request'

// ============ 类型定义 ============

export interface CoachCourse {
  id: number
  category: string
  category_text: string
  title: string
  subtitle: string | null
  cover_image: string | null
  duration_minutes: number
  price: number
  status: string
  status_text: string
  upcoming_session_count: number
}

export interface CourseSession {
  id: number
  course_id: number
  course_title: string | null
  category: string | null
  category_text: string | null
  session_date: string
  start_time: string | null
  end_time: string | null
  capacity: number
  booked_count: number
  status: string
  status_text: string
  remark: string | null
}

export interface SessionBooking {
  id: number
  booking_no: string
  member_name: string
  member_phone: string
  price: number
  pay_type: string
  status: string
  status_text: string
  is_verified: boolean
  created_at: string | null
}

// ============ 约课新链路（只读） ============

// 我的课程列表
export function getMyCourses() {
  return request.get('/coach/courses')
}

// 我的排课（start_date/end_date 缺省后端给今天起 7 天）
export function getMySessions(params?: { start_date?: string; end_date?: string }) {
  return request.get('/coach/sessions', { params })
}

// 某课次的报名名单
export function getSessionBookings(sessionId: number) {
  return request.get(`/coach/sessions/${sessionId}/bookings`)
}
