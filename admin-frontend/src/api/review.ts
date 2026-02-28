import request from '@/utils/request'

export function getReviews(params: any) {
  return request({ url: '/reviews', method: 'get', params })
}
export function replyReview(id: number, data: { reply: string }) {
  return request({ url: `/reviews/${id}/reply`, method: 'put', data })
}
export function toggleReviewVisible(id: number, data: { is_visible: boolean }) {
  return request({ url: `/reviews/${id}/visible`, method: 'put', data })
}
export function getReviewPointConfig() {
  return request({ url: '/reviews/point-config', method: 'get' })
}
export function updateReviewPointConfig(data: any) {
  return request({ url: '/reviews/point-config', method: 'put', data })
}
