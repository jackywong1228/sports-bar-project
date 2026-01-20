/**
 * UI配置工具
 * 用于获取和缓存后台配置的UI布局
 */

const app = getApp()

// 缓存key
const CACHE_KEY = 'ui_config_cache'
const CACHE_EXPIRE_KEY = 'ui_config_expire'

// 缓存有效期（1小时）
const CACHE_DURATION = 60 * 60 * 1000

// 默认配置（当无法获取后台配置时使用）
const DEFAULT_CONFIG = {
  pages: [
    {
      page_code: 'home',
      page_name: '首页',
      page_type: 'tabbar',
      blocks_config: [
        { block_code: 'banner', visible: true, sort_order: 0 },
        { block_code: 'quick_entry', visible: true, sort_order: 1 },
        { block_code: 'hot_venues', visible: true, sort_order: 2 },
        { block_code: 'hot_activities', visible: true, sort_order: 3 },
        { block_code: 'hot_coaches', visible: true, sort_order: 4 }
      ]
    }
  ],
  blocks: [
    { block_code: 'banner', block_name: '轮播图', block_type: 'banner', page_code: 'home', sort_order: 0, is_active: true },
    { block_code: 'quick_entry', block_name: '快捷入口', block_type: 'quick_entry', page_code: 'home', sort_order: 1, is_active: true },
    { block_code: 'hot_venues', block_name: '热门场馆', block_type: 'list', page_code: 'home', sort_order: 2, is_active: true },
    { block_code: 'hot_activities', block_name: '热门活动', block_type: 'scroll', page_code: 'home', sort_order: 3, is_active: true },
    { block_code: 'hot_coaches', block_name: '热门教练', block_type: 'scroll', page_code: 'home', sort_order: 4, is_active: true }
  ],
  menuItems: [
    { menu_code: 'venue', menu_type: 'quick_entry', title: '场馆预约', icon: '/assets/icons/venue-entry.png', link_type: 'tab', link_value: '/pages/venue/venue', sort_order: 0, is_visible: true },
    { menu_code: 'coach', menu_type: 'quick_entry', title: '教练预约', icon: '/assets/icons/coach-entry.png', link_type: 'page', link_value: '/pages/coach-list/coach-list', sort_order: 1, is_visible: true },
    { menu_code: 'activity', menu_type: 'quick_entry', title: '精彩活动', icon: '/assets/icons/activity-entry.png', link_type: 'tab', link_value: '/pages/activity/activity', sort_order: 2, is_visible: true },
    { menu_code: 'food', menu_type: 'quick_entry', title: '点餐', icon: '/assets/icons/food-entry.png', link_type: 'page', link_value: '/pages/food/food', sort_order: 3, is_visible: true },
    { menu_code: 'mall', menu_type: 'quick_entry', title: '积分商城', icon: '/assets/icons/mall-entry.png', link_type: 'page', link_value: '/pages/mall/mall', sort_order: 4, is_visible: true },
    { menu_code: 'team', menu_type: 'quick_entry', title: '组队', icon: '/assets/icons/team-entry.png', link_type: 'page', link_value: '/pages/team/team', sort_order: 5, is_visible: true },
    { menu_code: 'member', menu_type: 'quick_entry', title: '会员中心', icon: '/assets/icons/member-entry.png', link_type: 'page', link_value: '/pages/member/member', sort_order: 6, is_visible: true },
    { menu_code: 'coupon', menu_type: 'quick_entry', title: '我的券包', icon: '/assets/icons/coupon-entry.png', link_type: 'page', link_value: '/pages/coupons/coupons', sort_order: 7, is_visible: true }
  ],
  tabBar: [
    { menu_code: 'tab_home', menu_type: 'tabbar', title: '首页', icon: '/assets/icons/home.png', icon_active: '/assets/icons/home-active.png', link_type: 'tab', link_value: '/pages/index/index', sort_order: 0, is_visible: true },
    { menu_code: 'tab_venue', menu_type: 'tabbar', title: '场馆', icon: '/assets/icons/venue.png', icon_active: '/assets/icons/venue-active.png', link_type: 'tab', link_value: '/pages/venue/venue', sort_order: 1, is_visible: true },
    { menu_code: 'tab_activity', menu_type: 'tabbar', title: '活动', icon: '/assets/icons/activity.png', icon_active: '/assets/icons/activity-active.png', link_type: 'tab', link_value: '/pages/activity/activity', sort_order: 2, is_visible: true },
    { menu_code: 'tab_profile', menu_type: 'tabbar', title: '我的', icon: '/assets/icons/user.png', icon_active: '/assets/icons/user-active.png', link_type: 'tab', link_value: '/pages/profile/profile', sort_order: 3, is_visible: true }
  ],
  version: 0
}

/**
 * 获取UI配置
 * @param {boolean} forceRefresh - 是否强制刷新
 * @returns {Promise<Object>} UI配置对象
 */
const getUIConfig = (forceRefresh = false) => {
  return new Promise((resolve, reject) => {
    // 检查缓存
    if (!forceRefresh) {
      const cached = getCache()
      if (cached) {
        console.log('[UIConfig] 使用缓存配置')
        resolve(cached)
        return
      }
    }

    // 从服务器获取
    console.log('[UIConfig] 从服务器获取配置')
    wx.request({
      url: `${app.globalData.baseUrl}/member/ui-config`,
      method: 'GET',
      success(res) {
        if (res.statusCode === 200 && res.data.code === 200) {
          const config = res.data.data
          setCache(config)
          console.log('[UIConfig] 配置获取成功，版本:', config.version)
          resolve(config)
        } else {
          console.warn('[UIConfig] 获取配置失败，使用默认配置')
          resolve(DEFAULT_CONFIG)
        }
      },
      fail(err) {
        console.error('[UIConfig] 请求失败:', err)
        resolve(DEFAULT_CONFIG)
      }
    })
  })
}

/**
 * 获取页面配置
 * @param {string} pageCode - 页面编码
 * @returns {Promise<Object>} 页面配置
 */
const getPageConfig = async (pageCode) => {
  const config = await getUIConfig()
  return config.pages.find(p => p.page_code === pageCode) || null
}

/**
 * 获取区块配置
 * @param {string} pageCode - 页面编码
 * @returns {Promise<Array>} 区块配置列表
 */
const getBlocksConfig = async (pageCode) => {
  const config = await getUIConfig()
  return config.blocks
    .filter(b => b.page_code === pageCode && b.is_active)
    .sort((a, b) => a.sort_order - b.sort_order)
}

/**
 * 获取可见区块列表
 * @param {string} pageCode - 页面编码
 * @returns {Promise<Array>} 可见区块代码列表
 */
const getVisibleBlocks = async (pageCode) => {
  const blocks = await getBlocksConfig(pageCode)
  return blocks.map(b => b.block_code)
}

/**
 * 获取快捷入口菜单
 * @returns {Promise<Array>} 快捷入口列表
 */
const getQuickEntries = async () => {
  const config = await getUIConfig()
  return (config.menuItems || [])
    .filter(m => m.menu_type === 'quick_entry' && m.is_visible)
    .sort((a, b) => a.sort_order - b.sort_order)
}

/**
 * 获取TabBar配置
 * @returns {Promise<Array>} TabBar列表
 */
const getTabBarConfig = async () => {
  const config = await getUIConfig()
  return (config.tabBar || [])
    .filter(m => m.is_visible)
    .sort((a, b) => a.sort_order - b.sort_order)
}

/**
 * 获取缓存
 */
const getCache = () => {
  try {
    const expire = wx.getStorageSync(CACHE_EXPIRE_KEY)
    if (expire && Date.now() < expire) {
      return wx.getStorageSync(CACHE_KEY)
    }
  } catch (e) {
    console.error('[UIConfig] 读取缓存失败:', e)
  }
  return null
}

/**
 * 设置缓存
 */
const setCache = (config) => {
  try {
    wx.setStorageSync(CACHE_KEY, config)
    wx.setStorageSync(CACHE_EXPIRE_KEY, Date.now() + CACHE_DURATION)
  } catch (e) {
    console.error('[UIConfig] 设置缓存失败:', e)
  }
}

/**
 * 清除缓存
 */
const clearCache = () => {
  try {
    wx.removeStorageSync(CACHE_KEY)
    wx.removeStorageSync(CACHE_EXPIRE_KEY)
  } catch (e) {
    console.error('[UIConfig] 清除缓存失败:', e)
  }
}

module.exports = {
  getUIConfig,
  getPageConfig,
  getBlocksConfig,
  getVisibleBlocks,
  getQuickEntries,
  getTabBarConfig,
  clearCache,
  DEFAULT_CONFIG
}
