import request from '@/utils/request'

// ============ 类型定义 ============

export interface Course {
  id: number
  coach_id: number
  coach_name: string | null
  category: string
  category_text: string
  title: string
  subtitle: string | null
  cover_image: string | null
  description: string | null
  duration_minutes: number
  price: number
  status: string
  status_text: string
  session_count: number
  upcoming_session_count: number
  created_at: string | null
}

export interface CourseDetail extends Course {
  coach: {
    id: number
    name: string
    phone: string
    avatar: string | null
  } | null
  upcoming_sessions: CourseSession[]
}

export interface CourseSession {
  id: number
  course_id: number
  coach_id: number
  session_date: string
  start_time: string | null
  end_time: string | null
  capacity: number
  booked_count: number
  status: string
  status_text: string
  remark: string | null
  created_at: string | null
}

export interface CourseBooking {
  id: number
  booking_no: string
  member_id: number
  member_name: string | null
  member_phone: string | null
  price: number
  pay_type: string
  status: string
  status_text: string
  is_verified: boolean
  verified_at: string | null
  cancel_reason: string | null
  remark: string | null
  created_at: string | null
}

export interface CourseFormData {
  coach_id: number
  category: string
  title: string
  subtitle?: string | null
  cover_image?: string | null
  description?: string | null
  duration_minutes: number
  price: number
}

export interface SessionItemInput {
  session_date: string
  start_time: string
  end_time: string
  capacity: number
  remark?: string | null
}

// ============ 课程管理 ============

// 课程列表
export function getCourseList(params?: {
  page?: number
  page_size?: number
  category?: string | null
  status?: string | null
  coach_id?: number | null
}) {
  return request.get('/courses', { params })
}

// 课程详情
export function getCourseDetail(id: number) {
  return request.get(`/courses/${id}`)
}

// 创建课程
export function createCourse(data: CourseFormData) {
  return request.post('/courses', data)
}

// 编辑课程
export function updateCourse(id: number, data: Partial<CourseFormData>) {
  return request.put(`/courses/${id}`, data)
}

// 上架/下架
export function updateCourseStatus(id: number, status: 'on' | 'off') {
  return request.put(`/courses/${id}/status`, { status })
}

// 删除课程
export function deleteCourse(id: number) {
  return request.delete(`/courses/${id}`)
}

// ============ 课次管理 ============

// 课次列表
export function getCourseSessions(courseId: number, params?: { start_date?: string; end_date?: string }) {
  return request.get(`/courses/${courseId}/sessions`, { params })
}

// 批量创建课次（单条传 items 长度 1 即可）
export function createCourseSessions(courseId: number, items: SessionItemInput[]) {
  return request.post(`/courses/${courseId}/sessions`, { items })
}

// 修改课次（有报名时后端只允许改备注）
export function updateCourseSession(
  courseId: number,
  sessionId: number,
  data: Partial<SessionItemInput>
) {
  return request.put(`/courses/${courseId}/sessions/${sessionId}`, data)
}

// 取消课次（金币报名自动退款，响应含 refunded_bookings）
export function cancelCourseSession(courseId: number, sessionId: number, reason?: string) {
  return request.put(`/courses/${courseId}/sessions/${sessionId}/cancel`, { reason })
}

// 课次报名名单
export function getSessionBookings(courseId: number, sessionId: number) {
  return request.get(`/courses/${courseId}/sessions/${sessionId}/bookings`)
}
