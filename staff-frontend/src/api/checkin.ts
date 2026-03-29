import request from '@/utils/request'

export function getCheckinRecords(params?: Record<string, unknown>) {
  return request.get('/checkin/records', { params })
}
