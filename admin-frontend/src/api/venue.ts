import request from '@/utils/request'

// 场地类型列表
export function getVenueTypes(params?: any) {
  return request.get('/venue-types', { params })
}

// 创建场地类型
export function createVenueType(data: any) {
  return request.post('/venue-types', data)
}

// 更新场地类型
export function updateVenueType(id: number, data: any) {
  return request.put(`/venue-types/${id}`, data)
}

// 删除场地类型
export function deleteVenueType(id: number) {
  return request.delete(`/venue-types/${id}`)
}

// 场地列表
export function getVenueList(params?: any) {
  return request.get('/venues', { params })
}

// 场地详情
export function getVenueDetail(id: number) {
  return request.get(`/venues/${id}`)
}

// 创建场地
export function createVenue(data: any) {
  return request.post('/venues', data)
}

// 更新场地
export function updateVenue(id: number, data: any) {
  return request.put(`/venues/${id}`, data)
}

// 删除场地
export function deleteVenue(id: number) {
  return request.delete(`/venues/${id}`)
}

// 场地时间段配置
export function getVenueTimeSlots(id: number) {
  return request.get(`/venues/${id}/time-slots`)
}

// 更新场地时间段配置
export function updateVenueTimeSlots(id: number, data: any) {
  return request.put(`/venues/${id}/time-slots`, data)
}
