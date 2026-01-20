// UI页面配置
export interface UIPageConfig {
  id: number
  page_code: string
  page_name: string
  page_type: 'tabbar' | 'normal'
  blocks_config: BlockConfigItem[]
  style_config: PageStyleConfig
  version: number
  status: 'draft' | 'published'
  published_at?: string
  is_active: boolean
}

export interface BlockConfigItem {
  block_code: string
  visible: boolean
  sort_order: number
}

export interface PageStyleConfig {
  backgroundColor?: string
  navigationBarColor?: string
  navigationBarTextStyle?: 'white' | 'black'
}

// UI区块配置
export interface UIBlockConfig {
  id: number
  block_code: string
  block_name: string
  page_code: string
  block_type: 'banner' | 'quick_entry' | 'list' | 'scroll' | 'custom'
  config: BlockTypeConfig
  style_config: BlockStyleConfig
  data_source?: DataSourceConfig
  sort_order: number
  is_active: boolean
}

export interface BlockTypeConfig {
  // Banner配置
  height?: number
  autoplay?: boolean
  interval?: number
  // 快捷入口配置
  columns?: number
  showText?: boolean
  iconSize?: number
  // 列表配置
  limit?: number
  showMore?: boolean
  cardStyle?: 'horizontal' | 'vertical' | 'grid'
}

export interface BlockStyleConfig {
  marginTop?: number
  marginBottom?: number
  paddingHorizontal?: number
  backgroundColor?: string
  borderRadius?: number
}

export interface DataSourceConfig {
  type: 'api' | 'static'
  api?: string
  params?: Record<string, any>
  staticData?: any[]
}

// UI菜单项配置
export interface UIMenuItem {
  id: number
  menu_code: string
  menu_type: 'quick_entry' | 'tabbar' | 'profile_menu' | 'more_menu'
  block_id?: number
  title: string
  subtitle?: string
  icon?: string
  icon_active?: string
  link_type: 'page' | 'tab' | 'webview' | 'miniprogram' | 'none'
  link_value?: string
  link_params?: Record<string, any>
  show_condition?: ShowCondition
  badge_type?: 'none' | 'dot' | 'number' | 'text'
  badge_value?: string
  sort_order: number
  is_visible: boolean
  is_active: boolean
}

export interface ShowCondition {
  loginRequired?: boolean
  memberLevelMin?: number
  startTime?: string
  endTime?: string
}

// UI配置版本
export interface UIConfigVersion {
  id: number
  version: number
  version_name?: string
  config_snapshot: ConfigSnapshot
  published_by?: number
  publish_note?: string
  is_current: boolean
  created_at: string
}

export interface ConfigSnapshot {
  pages: UIPageConfig[]
  blocks: UIBlockConfig[]
  menuItems: UIMenuItem[]
  tabBar: UIMenuItem[]
  publishedAt: string
}

// 表单数据类型
export interface MenuItemForm {
  menu_code: string
  menu_type: string
  block_id?: number
  title: string
  subtitle?: string
  icon?: string
  icon_active?: string
  link_type: string
  link_value?: string
  link_params?: Record<string, any>
  show_condition?: ShowCondition
  badge_type?: string
  badge_value?: string
  sort_order: number
  is_visible: boolean
}

export interface BlockForm {
  block_code: string
  block_name: string
  page_code: string
  block_type: string
  config: BlockTypeConfig
  style_config: BlockStyleConfig
  data_source?: DataSourceConfig
  sort_order: number
  is_active: boolean
}

// 预览数据
export interface PreviewData {
  banner: Array<{ image: string; title: string }>
  quickEntries: UIMenuItem[]
  hotVenues: Array<{ id: number; name: string; image: string; price: number }>
  hotActivities: Array<{ id: number; title: string; image: string }>
  hotCoaches: Array<{ id: number; name: string; avatar: string; price: number }>
  tabBar: UIMenuItem[]
}
