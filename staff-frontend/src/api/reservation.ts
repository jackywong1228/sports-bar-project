import request from '@/utils/request'

export function getReservationList(params?: Record<string, unknown>) {
  return request.get('/reservations', { params })
}

export function getReservationDetail(id: number) {
  return request.get(`/reservations/${id}`)
}

export function updateReservationStatus(id: number, data: { status: string; remark?: string }) {
  return request.put(`/reservations/${id}/status`, data)
}

export function confirmReservation(id: number) {
  return request.post(`/reservations/${id}/confirm`)
}

export function completeReservation(id: number) {
  return request.post(`/reservations/${id}/complete`)
}

export function verifyReservationByNo(reservationNo: string) {
  return request.post('/reservations/verify-by-no', { reservation_no: reservationNo })
}
