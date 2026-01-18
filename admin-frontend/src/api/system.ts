import request from '@/utils/request'

// ==================== 用户管理 ====================

// 用户列表
export function getUserList(params?: any) {
  return request.get('/users', { params })
}

// 用户详情
export function getUserDetail(id: number) {
  return request.get(`/users/${id}`)
}

// 创建用户
export function createUser(data: any) {
  return request.post('/users', data)
}

// 更新用户
export function updateUser(id: number, data: any) {
  return request.put(`/users/${id}`, data)
}

// 删除用户
export function deleteUser(id: number) {
  return request.delete(`/users/${id}`)
}

// 重置密码
export function resetPassword(id: number, data: { password: string }) {
  return request.post(`/users/${id}/reset-password`, data)
}

// 更新用户状态
export function updateUserStatus(id: number, data: { status: boolean }) {
  return request.put(`/users/${id}/status`, data)
}

// ==================== 角色管理 ====================

// 角色列表
export function getRoleList(params?: any) {
  return request.get('/roles', { params })
}

// 创建角色
export function createRole(data: any) {
  return request.post('/roles', data)
}

// 更新角色
export function updateRole(id: number, data: any) {
  return request.put(`/roles/${id}`, data)
}

// 删除角色
export function deleteRole(id: number) {
  return request.delete(`/roles/${id}`)
}

// 获取角色权限
export function getRolePermissions(id: number) {
  return request.get(`/roles/${id}/permissions`)
}

// 更新角色权限
export function updateRolePermissions(id: number, data: { permission_ids: number[] }) {
  return request.put(`/roles/${id}/permissions`, data)
}

// ==================== 部门管理 ====================

// 部门树
export function getDepartmentTree() {
  return request.get('/departments/tree')
}

// 部门列表
export function getDepartmentList(params?: any) {
  return request.get('/departments', { params })
}

// 创建部门
export function createDepartment(data: any) {
  return request.post('/departments', data)
}

// 更新部门
export function updateDepartment(id: number, data: any) {
  return request.put(`/departments/${id}`, data)
}

// 删除部门
export function deleteDepartment(id: number) {
  return request.delete(`/departments/${id}`)
}

// ==================== 权限管理 ====================

// 权限列表
export function getPermissionList() {
  return request.get('/permissions')
}

// 权限树
export function getPermissionTree() {
  return request.get('/permissions/tree')
}
