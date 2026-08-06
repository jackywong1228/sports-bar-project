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
 * 获取轮播图
 */
const getBanners = () => {
  return get('/member/banners')
}

/**
 * 获取公告列表
 */
const getAnnouncements = () => {
  return get('/member/announcements')
}

// ==================== 场馆预约 ====================

/**
 * 获取场馆类型
 */
const getVenueTypes = () => {
  return get('/member/venue-types')
}

/**
 * 获取场馆列表
 */
const getVenueList = (params = {}) => {
  return get('/member/venues', params)
}

/**
 * 获取场馆详情
 */
const getVenueDetail = (id) => {
  return get(`/member/venues/${id}`)
}

/**
 * 获取场馆可预约时段
 * @param {number} venueId 场馆ID
 * @param {string} date 日期 YYYY-MM-DD
 */
const getVenueSchedule = (venueId, date) => {
  return get(`/member/venues/${venueId}/slots`, { date })
}

/**
 * 创建场馆预约
 */
const createVenueReservation = (data) => {
  return post('/member/reservations', data, { showLoading: true })
}

// ==================== 教练预约 ====================

/**
 * 获取教练列表
 */
const getCoachList = (params = {}) => {
  return get('/member/coaches', params)
}

/**
 * 获取教练详情
 */
const getCoachDetail = (id) => {
  return get(`/member/coaches/${id}`)
}

/**
 * 获取教练排期
 */
const getCoachSchedule = (coachId, date) => {
  return get(`/member/coaches/${coachId}/schedule`, { date })
}

/**
 * 创建教练预约
 */
const createCoachReservation = (data) => {
  return post('/member/reservations', data, { showLoading: true })
}

// ==================== 预约记录 ====================

/**
 * 获取预约列表
 */
const getReservationList = (params = {}) => {
  return get('/member/reservations', params)
}


/**
 * 取消预约
 */
const cancelReservation = (id) => {
  return post(`/member/reservations/${id}/cancel`, {}, { showLoading: true })
}

// ==================== 活动 ====================

/**
 * 获取活动列表
 */
const getActivityList = (params = {}) => {
  return get('/member/activities', params)
}

/**
 * 获取活动详情
 */
const getActivityDetail = (id) => {
  return get(`/member/activities/${id}`)
}

/**
 * 报名活动
 */
const joinActivity = (activityId) => {
  return post(`/member/activities/${activityId}/enroll`, {}, { showLoading: true })
}

/**
 * 取消报名
 */
const quitActivity = (activityId) => {
  return post(`/member/activities/${activityId}/cancel`, {}, { showLoading: true })
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
  return get('/member/mall/categories')
}

/**
 * 获取商城商品列表
 */
const getMallProducts = (params = {}) => {
  return get('/member/mall/goods', params)
}

/**
 * 获取商品详情
 */
const getMallProductDetail = (id) => {
  return get(`/member/mall/goods/${id}`)
}

/**
 * 兑换商品
 */
const exchangeProduct = (productId, quantity = 1, addressId = null) => {
  return post(`/member/mall/goods/${productId}/exchange`, { quantity, address_id: addressId }, { showLoading: true })
}


// ==================== 组队广场 ====================

/**
 * 获取组队列表
 */
const getTeamList = (params = {}) => {
  return get('/member/teams', params)
}

/**
 * 获取组队详情
 */
const getTeamDetail = (id) => {
  return get(`/member/teams/${id}`)
}

/**
 * 发起组队
 */
const createTeam = (data) => {
  return post('/member/teams', data, { showLoading: true })
}

/**
 * 加入组队
 */
const joinTeam = (teamId) => {
  return post(`/member/teams/${teamId}/join`, {}, { showLoading: true })
}

/**
 * 退出组队
 */
const quitTeam = (teamId) => {
  return post(`/member/teams/${teamId}/quit`, {}, { showLoading: true })
}

/**
 * 获取我的组队列表
 */
const getMyTeams = (params = {}) => {
  return get('/member/my-teams', params)
}

// ==================== 钱包 ====================


/**
 * 获取金币记录
 */
const getCoinRecords = (params = {}) => {
  return get('/member/coin-records', params)
}

/**
 * 获取积分记录
 */
const getPointRecords = (params = {}) => {
  return get('/member/point-records', params)
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
const getMyCoupons = (status = '', applicableType = '') => {
  const params = {}
  if (status) params.status = status
  if (applicableType) params.applicable_type = applicableType
  return get('/member/coupons', params)
}


// ==================== 订单 ====================

/**
 * 获取所有订单
 */
const getOrders = (params = {}) => {
  return get('/member/orders', params)
}

/**
 * 获取订单详情
 */
const getOrderDetail = (id) => {
  return get(`/member/orders/${id}`)
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



// ==================== 评论 ====================

/**
 * 提交评论
 * @param {Object} data { venue_id?, coach_id?, content, rating, images? }
 */
const submitReview = (data) => {
  return post('/member/reviews', data)
}

/**
 * 获取我的评论列表
 * @param {Object} params { page?, page_size? }
 */
const getMyReviews = (params = {}) => {
  return get('/member/reviews', params)
}

// ==================== 场馆价目表 ====================

/**
 * 获取场馆价目表
 * @param {number} venueId 场馆ID
 * @param {string} date 日期
 */
const getVenuePriceTable = (venueId, date) => {
  return get(`/member/venues/${venueId}/price-table`, { date })
}

// ==================== 充值套餐（会员端） ====================


// ==================== 人脸识别（预留） ====================

/**
 * 注册人脸
 * @param {Object} data { image }
 */
const registerFace = (data) => {
  return post('/member/face/register', data)
}

/**
 * 获取人脸识别状态
 */
const getFaceStatus = () => {
  return get('/member/face/status')
}

// ==================== 邀请功能 ====================

/**
 * 生成邀请码
 */
const generateInviteCode = () => {
  return post('/member/invite/generate')
}

/**
 * 获取本月邀请统计
 */
const getInviteStats = () => {
  return get('/member/invite/stats')
}

/**
 * 获取邀请记录
 */
const getInviteHistory = (page = 1, pageSize = 20) => {
  return get(`/member/invite/history?page=${page}&page_size=${pageSize}`)
}

/**
 * 使用邀请码
 */
const useInviteCode = (code) => {
  return post(`/member/invite/${code}/accept`)
}

// ==================== 意见反馈 ====================

/**
 * 提交意见反馈
 */
const submitFeedback = (data) => {
  return post('/member/feedback', data, { showLoading: true })
}

/**
 * 获取我的反馈列表
 */
const getMyFeedback = (params = {}) => {
  return get('/member/feedback', params)
}

// ==================== 会员动态二维码 ====================

/**
 * 获取我的会员动态二维码 token（30 秒短期 JWT）
 * 配合 my-qrcode 页面使用，前端每 25 秒刷新一次
 */
const getMemberQrToken = () => {
  return get('/member/qrcode/token')
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
  cancelReservation,

  // 活动
  getActivityList,
  getActivityDetail,
  joinActivity,
  quitActivity,

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

  // 组队
  getTeamList,
  getTeamDetail,
  createTeam,
  joinTeam,
  quitTeam,
  getMyTeams,

  // 钱包
  getCoinRecords,
  getPointRecords,

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

  // 订单
  getOrders,
  getOrderDetail,

  // 上传
  uploadImage,

  // 会员权限检查
  checkBookingPermission,

  // 评论
  submitReview,
  getMyReviews,

  // 场馆价目表
  getVenuePriceTable,

  // 充值套餐（会员端）

  // 人脸识别（预留）
  registerFace,
  getFaceStatus,

  // 邀请功能
  generateInviteCode,
  getInviteStats,
  getInviteHistory,
  useInviteCode,

  // 意见反馈
  submitFeedback,
  getMyFeedback,

  // 会员动态二维码
  getMemberQrToken
}
