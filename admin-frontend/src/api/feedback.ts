import request from '@/utils/request'

export function getFeedbackList(params: any) {
  return request({ url: '/feedback', method: 'get', params })
}

export function getFeedbackDetail(id: number) {
  return request({ url: `/feedback/${id}`, method: 'get' })
}

export function replyFeedback(id: number, data: { reply: string }) {
  return request({ url: `/feedback/${id}/reply`, method: 'put', data })
}

export function updateFeedbackStatus(id: number, data: { status: string }) {
  return request({ url: `/feedback/${id}/status`, method: 'put', data })
}

export function deleteFeedback(id: number) {
  return request({ url: `/feedback/${id}`, method: 'delete' })
}
