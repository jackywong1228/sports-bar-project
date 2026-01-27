/**
 * API接口定义
 * 统一管理所有后端接口
 */

const { get, post, put, del, upload } = require('./request')

// ==================== 用户认证 ====================

/**
 * 手机号登录（开发测试用）
 * @param {string} phone 手机号
 */
const loginByPhone = (phone) => {
  return post('/member/auth/login', { phone })
}

/**
 * 微信登录
 * @param {string} code wx.login获取的code
 * @param {Object} userInfo 用户信息
 */
const wxLogin = (code, userInfo = {}) => {
  return post('/member/auth/wx-login', { code, ...userInfo })
}

/**
 * 获取手机号
 * @param {string} code getPhoneNumber事件获取的code
 */
const getPhoneNumber = (code) => {
  return post('/member/auth/phone', { code })
}

/**
 * 获取当前用户信息
 */
const getUserProfile = () => {
  return get('/member/profile')
}

/**
 * 更新用户信息
 */
const updateUserProfile = (data) => {
  return put('/member/profile', data)
}

// ==================== 教练申请 ====================

/**
 * 申请成为教练
 */
const applyForCoach = (data) => {
  return post('/member/coach/apply', data)
}

/**
 * 获取教练申请状态
 */
const getCoachApplyStatus = () => {
  return get('/member/coach/apply/status')
}

// ==================== 首页 ====================

/**
 * 获取首页数据
 */
const getHomeData = () => {
  return get('/home')
}

/**
 * 获取轮播图
 */
const getBanners = () => {
  return get('/banners')
}

/**
 * 获取公告列表
 */
const getAnnouncements = () => {
  return get('/announcements')
}

// ==================== 场馆预约 ====================

/**
 * 获取场馆类型
 */
const getVenueTypes = () => {
  return get('/venues/types')
}

/**
 * 获取场馆列表
 */
const getVenueList = (params = {}) => {
  return get('/venues', params)
}

/**
 * 获取场馆详情
 */
const getVenueDetail = (id) => {
  return get(`/venues/${id}`)
}

/**
 * 获取场馆可预约时段
 * @param {number} venueId 场馆ID
 * @param {string} date 日期 YYYY-MM-DD
 */
const getVenueSchedule = (venueId, date) => {
  return get(`/venues/${venueId}/schedule`, { date })
}

/**
 * 创建场馆预约
 */
const createVenueReservation = (data) => {
  return post('/reservations/venue', data, { showLoading: true })
}

// ==================== 教练预约 ====================

/**
 * 获取教练列表
 */
const getCoachList = (params = {}) => {
  return get('/coaches', params)
}

/**
 * 获取教练详情
 */
const getCoachDetail = (id) => {
  return get(`/coaches/${id}`)
}

/**
 * 获取教练排期
 */
const getCoachSchedule = (coachId, date) => {
  return get(`/coaches/${coachId}/schedule`, { date })
}

/**
 * 创建教练预约
 */
const createCoachReservation = (data) => {
  return post('/reservations/coach', data, { showLoading: true })
}

// ==================== 预约记录 ====================

/**
 * 获取预约列表
 */
const getReservationList = (params = {}) => {
  return get('/reservations', params)
}

/**
 * 获取预约详情
 */
const getReservationDetail = (id) => {
  return get(`/reservations/${id}`)
}

/**
 * 取消预约
 */
const cancelReservation = (id) => {
  return post(`/reservations/${id}/cancel`, {}, { showLoading: true })
}

// ==================== 活动 ====================

/**
 * 获取活动列表
 */
const getActivityList = (params = {}) => {
  return get('/activities', params)
}

/**
 * 获取活动详情
 */
const getActivityDetail = (id) => {
  return get(`/activities/${id}`)
}

/**
 * 报名活动
 */
const joinActivity = (activityId) => {
  return post(`/activities/${activityId}/join`, {}, { showLoading: true })
}

/**
 * 取消报名
 */
const quitActivity = (activityId) => {
  return post(`/activities/${activityId}/quit`, {}, { showLoading: true })
}

// ==================== 点餐 ====================

/**
 * 获取餐饮分类
 */
const getFoodCategories = () => {
  return get('/food/categories')
}

/**
 * 获取餐饮商品列表
 */
const getFoodList = (params = {}) => {
  return get('/food/items', params)
}

/**
 * 获取购物车
 */
const getCart = () => {
  return get('/food/cart')
}

/**
 * 添加到购物车
 */
const addToCart = (itemId, quantity = 1, specs = {}) => {
  return post('/food/cart', { item_id: itemId, quantity, specs })
}

/**
 * 更新购物车数量
 */
const updateCartItem = (cartItemId, quantity) => {
  return put(`/food/cart/${cartItemId}`, { quantity })
}

/**
 * 删除购物车项
 */
const removeCartItem = (cartItemId) => {
  return del(`/food/cart/${cartItemId}`)
}

/**
 * 清空购物车
 */
const clearCart = () => {
  return del('/food/cart')
}

/**
 * 创建餐饮订单
 */
const createFoodOrder = (data) => {
  return post('/food/orders', data, { showLoading: true })
}

/**
 * 获取餐饮订单列表
 */
const getFoodOrders = (params = {}) => {
  return get('/food/orders', params)
}

/**
 * 获取餐饮订单详情
 */
const getFoodOrderDetail = (id) => {
  return get(`/food/orders/${id}`)
}

// ==================== 会员卡 ====================

/**
 * 获取会员等级列表
 */
const getMemberLevels = () => {
  return get('/member-cards/levels')
}

/**
 * 获取会员卡套餐列表
 */
const getMemberCards = (params = {}) => {
  return get('/member/cards', params)
}

/**
 * 获取会员卡套餐详情
 */
const getMemberCardDetail = (id) => {
  return get(`/member/cards/${id}`)
}

/**
 * 购买会员卡（微信支付）
 */
const purchaseMemberCard = (cardId) => {
  return post(`/member/cards/${cardId}/buy`, {}, { showLoading: true })
}

/**
 * 获取我的会员卡订单
 */
const getMemberCardOrders = (params = {}) => {
  return get('/member/card-orders', params)
}

/**
 * 查询会员卡订单状态
 */
const queryMemberCardOrder = (orderNo) => {
  return get(`/member/card-orders/${orderNo}`)
}

// ==================== 积分商城 ====================

/**
 * 获取商城分类
 */
const getMallCategories = () => {
  return get('/mall/categories')
}

/**
 * 获取商城商品列表
 */
const getMallProducts = (params = {}) => {
  return get('/mall/products', params)
}

/**
 * 获取商品详情
 */
const getMallProductDetail = (id) => {
  return get(`/mall/products/${id}`)
}

/**
 * 兑换商品
 */
const exchangeProduct = (productId, quantity = 1, addressId = null) => {
  return post('/mall/exchange', { product_id: productId, quantity, address_id: addressId }, { showLoading: true })
}

/**
 * 获取兑换订单列表
 */
const getMallOrders = (params = {}) => {
  return get('/mall/orders', params)
}

// ==================== 组队广场 ====================

/**
 * 获取组队列表
 */
const getTeamList = (params = {}) => {
  return get('/teams', params)
}

/**
 * 获取组队详情
 */
const getTeamDetail = (id) => {
  return get(`/teams/${id}`)
}

/**
 * 发起组队
 */
const createTeam = (data) => {
  return post('/teams', data, { showLoading: true })
}

/**
 * 加入组队
 */
const joinTeam = (teamId) => {
  return post(`/teams/${teamId}/join`, {}, { showLoading: true })
}

/**
 * 退出组队
 */
const quitTeam = (teamId) => {
  return post(`/teams/${teamId}/quit`, {}, { showLoading: true })
}

// ==================== 钱包 ====================

/**
 * 获取钱包信息
 */
const getWallet = () => {
  return get('/wallet')
}

/**
 * 获取金币记录
 */
const getCoinRecords = (params = {}) => {
  return get('/wallet/coins', params)
}

/**
 * 获取积分记录
 */
const getPointRecords = (params = {}) => {
  return get('/wallet/points', params)
}

/**
 * 获取充值套餐
 */
const getRechargePackages = () => {
  return get('/wallet/recharge-packages')
}

/**
 * 发起充值
 */
const createRecharge = (amount, packageId = null) => {
  return post('/wallet/recharge', { amount, package_id: packageId }, { showLoading: true })
}

// ==================== 打卡与训练 ====================

/**
 * 获取打卡统计（本月数据，用于我的页面）
 */
const getCheckinStats = () => {
  return get('/member/checkin/stats')
}

/**
 * 获取今日打卡状态
 */
const getTodayCheckin = () => {
  return get('/member/checkin/today')
}

/**
 * 获取训练日历数据
 * @param {number} year 年份
 * @param {number} month 月份
 */
const getCheckinCalendar = (year, month) => {
  return get('/member/checkin/calendar', { year, month })
}

/**
 * 获取打卡记录列表
 * @param {Object} params 查询参数
 */
const getCheckinRecords = (params = {}) => {
  return get('/member/checkin/records', params)
}

// ==================== 排行榜 ====================

/**
 * 获取排行榜
 * @param {Object} params { period: 'daily'|'weekly'|'monthly', venue_type_id?: number }
 */
const getLeaderboard = (params = {}) => {
  return get('/member/leaderboard', params)
}

/**
 * 获取我的排名
 * @param {Object} params { period: 'daily'|'weekly'|'monthly', venue_type_id?: number }
 */
const getMyRank = (params = {}) => {
  return get('/member/leaderboard/my-rank', params)
}

// ==================== 优惠券 ====================

/**
 * 获取我的优惠券
 */
const getMyCoupons = (status = '') => {
  return get('/coupons/mine', { status })
}

/**
 * 领取优惠券
 */
const receiveCoupon = (templateId) => {
  return post('/coupons/receive', { template_id: templateId })
}

// ==================== 订单 ====================

/**
 * 获取所有订单
 */
const getOrders = (params = {}) => {
  return get('/orders', params)
}

/**
 * 获取订单详情
 */
const getOrderDetail = (id) => {
  return get(`/orders/${id}`)
}

/**
 * 支付订单
 */
const payOrder = (orderId, payType = 'coin') => {
  return post(`/orders/${orderId}/pay`, { pay_type: payType }, { showLoading: true })
}

/**
 * 取消订单
 */
const cancelOrder = (orderId) => {
  return post(`/orders/${orderId}/cancel`, {}, { showLoading: true })
}

// ==================== 文件上传 ====================

/**
 * 上传图片
 */
const uploadImage = (filePath) => {
  return upload('/upload/image', filePath, 'file')
}

// ==================== 会员权限检查 ====================

/**
 * 检查预约权限
 * @param {Object} params { venue_id?, coach_id?, date?, duration? }
 * @returns {Promise} { can_book, reason?, remaining_quota, daily_quota }
 */
const checkBookingPermission = (params = {}) => {
  return get('/member/booking-permission', params)
}

/**
 * 获取餐饮折扣信息
 * @returns {Promise} { discount, level_name }
 */
const getFoodDiscount = () => {
  return get('/member/food-discount')
}

/**
 * 获取违规记录
 * @param {Object} params { page?, page_size? }
 * @returns {Promise} { total, items: [{ id, type, description, created_at }] }
 */
const getViolations = (params = {}) => {
  return get('/member/violations', params)
}

/**
 * 核销预约（教练/前台使用）
 * @param {Object} data { reservation_id, verify_code? }
 * @returns {Promise} { success, message }
 */
const verifyReservation = (data) => {
  return post('/member/reservations/verify', data, { showLoading: true })
}

module.exports = {
  // 认证
  loginByPhone,
  wxLogin,
  getPhoneNumber,
  getUserProfile,
  updateUserProfile,

  // 教练申请
  applyForCoach,
  getCoachApplyStatus,

  // 首页
  getHomeData,
  getBanners,
  getAnnouncements,

  // 场馆
  getVenueTypes,
  getVenueList,
  getVenueDetail,
  getVenueSchedule,
  createVenueReservation,

  // 教练
  getCoachList,
  getCoachDetail,
  getCoachSchedule,
  createCoachReservation,

  // 预约
  getReservationList,
  getReservationDetail,
  cancelReservation,

  // 活动
  getActivityList,
  getActivityDetail,
  joinActivity,
  quitActivity,

  // 点餐
  getFoodCategories,
  getFoodList,
  getCart,
  addToCart,
  updateCartItem,
  removeCartItem,
  clearCart,
  createFoodOrder,
  getFoodOrders,
  getFoodOrderDetail,

  // 会员卡
  getMemberLevels,
  getMemberCards,
  getMemberCardDetail,
  purchaseMemberCard,
  getMemberCardOrders,
  queryMemberCardOrder,

  // 商城
  getMallCategories,
  getMallProducts,
  getMallProductDetail,
  exchangeProduct,
  getMallOrders,

  // 组队
  getTeamList,
  getTeamDetail,
  createTeam,
  joinTeam,
  quitTeam,

  // 钱包
  getWallet,
  getCoinRecords,
  getPointRecords,
  getRechargePackages,
  createRecharge,

  // 打卡与训练
  getCheckinStats,
  getTodayCheckin,
  getCheckinCalendar,
  getCheckinRecords,

  // 排行榜
  getLeaderboard,
  getMyRank,

  // 优惠券
  getMyCoupons,
  receiveCoupon,

  // 订单
  getOrders,
  getOrderDetail,
  payOrder,
  cancelOrder,

  // 上传
  uploadImage,

  // 会员权限检查
  checkBookingPermission,
  getFoodDiscount,
  getViolations,
  verifyReservation
}
