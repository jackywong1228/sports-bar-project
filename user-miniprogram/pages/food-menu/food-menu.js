const app = getApp()
const api = require('../../utils/api')

// 购物车与点单上下文（堂食/自取、桌号）本地持久化 key
const CART_KEY = 'food_cart'
const CTX_KEY = 'food_ctx'

// 购物车行唯一键：无规格 = i{itemId}；有规格 = i{itemId}_g{组id}o{选项id逗号串}...
function buildLineKey(itemId, specs) {
  if (!specs) return `i${itemId}`
  const parts = Object.keys(specs)
    .sort((a, b) => Number(a) - Number(b))
    .map(gid => `g${gid}o${(specs[gid] || []).slice().sort((x, y) => x - y).join(',')}`)
  return `i${itemId}_${parts.join('_')}`
}

function fen2text(n) {
  return (Math.round(n * 100) / 100).toFixed(2)
}

Page({
  data: {
    loading: true,
    loadFailed: false,
    categories: [],       // [{id, name, items: [{...display fields}]}]
    activeCatIndex: 0,
    // 点单模式：dine_in 堂食 / pickup 自取（预约取餐）
    mode: 'dine_in',
    tableNo: '',
    // 购物车
    cartMap: {},          // lineKey -> line
    itemQtyMap: {},       // item_id -> 总数量（列表角标/步进器用）
    cartList: [],         // 浮层展示用数组
    cartCount: 0,
    cartTotalText: '0.00',
    showCart: false,
    // 规格弹层
    showSpecModal: false,
    specItem: null,
    specSelections: {},   // group_id -> [option_id]
    specQty: 1,
    specPriceText: '0.00',
    specValid: false,
  },

  onLoad(options) {
    if (!app.checkLogin()) {
      // 未登录：仍可先看菜单，但下单会拦；这里直接返回上一页会打断扫码场景，保持页面加载
    }
    // 扫桌码进入：?table=5 自动堂食并带桌号
    const ctx = wx.getStorageSync(CTX_KEY) || {}
    const mode = options && options.table ? 'dine_in' : (ctx.mode || 'dine_in')
    const tableNo = options && options.table ? String(options.table) : (ctx.tableNo || '')
    this.setData({ mode, tableNo })
    this.saveCtx()
    this.restoreCart()
    this.loadMenu()
  },

  // ==================== 菜单加载 ====================

  async loadMenu() {
    this.setData({ loading: true, loadFailed: false })
    try {
      const res = await api.getFoodMenu()
      const categories = (res.data || []).map(cat => ({
        id: cat.id,
        name: cat.name,
        items: (cat.items || []).map(item => ({
          ...item,
          image: app.resolveImageUrl(item.image),
          price_text: fen2text(item.price || 0),
          // 规格最低价提示（含规格加价时起价不变，规格加价在弹层实时算）
          spec_hint: item.has_specs ? '选规格' : '',
        })),
      }))
      this.setData({ categories, activeCatIndex: 0 })
    } catch (err) {
      console.error('加载菜单失败:', err)
      this.setData({ loadFailed: true })
    } finally {
      this.setData({ loading: false })
    }
  },

  onCatTap(e) {
    const index = Number(e.currentTarget.dataset.index)
    this.setData({ activeCatIndex: index })
  },

  // ==================== 加购 ====================

  onAddTap(e) {
    const { catindex, itemindex } = e.currentTarget.dataset
    const item = this.data.categories[catindex].items[itemindex]
    if (item.sold_out) return
    if (item.has_specs && item.spec_groups && item.spec_groups.length > 0) {
      this.openSpecModal(catindex, itemindex)
      return
    }
    this.addLine(item, null, null, 1)
  },

  onMinusTap(e) {
    const { catindex, itemindex } = e.currentTarget.dataset
    const item = this.data.categories[catindex].items[itemindex]
    // 无规格商品直接减该行
    const key = buildLineKey(item.id, null)
    const line = this.data.cartMap[key]
    if (!line) return
    this.setLineQty(key, line.quantity - 1)
  },

  addLine(item, specs, specsText, qty) {
    const key = buildLineKey(item.id, specs)
    const extra = this.specExtraOf(item, specs)
    const unitPrice = Math.round(((item.price || 0) + extra) * 100) / 100
    const cartMap = { ...this.data.cartMap }
    if (cartMap[key]) {
      cartMap[key] = { ...cartMap[key], quantity: cartMap[key].quantity + qty }
    } else {
      cartMap[key] = {
        key,
        item_id: item.id,
        name: item.name,
        image: item.image,
        unit_price: unitPrice,
        unit_price_text: fen2text(unitPrice),
        quantity: qty,
        specs: specs || null,
        specs_text: specsText || '',
        coupon_enabled: !!item.coupon_enabled,
      }
    }
    this.setData({ cartMap })
    this.refreshCart()
  },

  // 规格加价合计
  specExtraOf(item, specs) {
    if (!specs || !item.spec_groups) return 0
    let extra = 0
    for (const group of item.spec_groups) {
      const ids = specs[String(group.id)] || specs[group.id] || []
      for (const opt of group.options || []) {
        if (ids.includes(opt.id)) extra += Number(opt.price_delta || 0)
      }
    }
    return extra
  },

  setLineQty(key, qty) {
    const cartMap = { ...this.data.cartMap }
    if (qty <= 0) {
      delete cartMap[key]
    } else if (cartMap[key]) {
      cartMap[key] = { ...cartMap[key], quantity: qty }
    }
    this.setData({ cartMap })
    this.refreshCart()
  },

  // 重算角标/总价/浮层列表并持久化
  refreshCart() {
    const cartMap = this.data.cartMap
    const cartList = []
    const itemQtyMap = {}
    let count = 0
    let total = 0
    for (const key of Object.keys(cartMap)) {
      const line = cartMap[key]
      count += line.quantity
      total += line.unit_price * line.quantity
      itemQtyMap[line.item_id] = (itemQtyMap[line.item_id] || 0) + line.quantity
      cartList.push({
        ...line,
        subtotal_text: fen2text(line.unit_price * line.quantity),
      })
    }
    this.setData({
      cartList,
      itemQtyMap,
      cartCount: count,
      cartTotalText: fen2text(total),
      showCart: count > 0 ? this.data.showCart : false,
    })
    wx.setStorageSync(CART_KEY, cartMap)
  },

  restoreCart() {
    const cartMap = wx.getStorageSync(CART_KEY) || {}
    this.setData({ cartMap })
    // refreshCart 依赖 setData 完成，直接同步再调一次
    this.refreshCart()
  },

  saveCtx() {
    wx.setStorageSync(CTX_KEY, { mode: this.data.mode, tableNo: this.data.tableNo })
  },

  // ==================== 规格弹层 ====================

  openSpecModal(catIndex, itemIndex) {
    const item = this.data.categories[catIndex].items[itemIndex]
    // 默认选中：必选的下单选组自动选第一个选项
    const selections = {}
    for (const group of item.spec_groups || []) {
      if (group.select_type === 'single' && group.required && group.options && group.options.length > 0) {
        selections[String(group.id)] = [group.options[0].id]
      }
    }
    this.setData({
      showSpecModal: true,
      specItem: item,
      specSelections: selections,
      specQty: 1,
    })
    this.refreshSpecSummary()
  },

  closeSpecModal() {
    this.setData({ showSpecModal: false, specItem: null })
  },

  noop() {},

  toggleSpecOption(e) {
    const { gid, oid, type } = e.currentTarget.dataset
    const gidStr = String(gid)
    const selections = { ...this.data.specSelections }
    const current = (selections[gidStr] || []).slice()
    if (type === 'single') {
      selections[gidStr] = current.includes(oid) && !this.isGroupRequired(gid) ? [] : [oid]
    } else {
      const idx = current.indexOf(oid)
      if (idx >= 0) current.splice(idx, 1)
      else current.push(oid)
      selections[gidStr] = current
    }
    this.setData({ specSelections: selections })
    this.refreshSpecSummary()
  },

  isGroupRequired(gid) {
    const item = this.data.specItem
    if (!item) return false
    const group = (item.spec_groups || []).find(g => g.id === Number(gid))
    return !!(group && group.required)
  },

  specQtyMinus() {
    if (this.data.specQty <= 1) return
    this.setData({ specQty: this.data.specQty - 1 })
    this.refreshSpecSummary()
  },

  specQtyPlus() {
    if (this.data.specQty >= 99) return
    this.setData({ specQty: this.data.specQty + 1 })
    this.refreshSpecSummary()
  },

  // 实时计算规格合计价 + 必选项校验
  refreshSpecSummary() {
    const item = this.data.specItem
    if (!item) return
    const selections = this.data.specSelections
    let extra = 0
    let valid = true
    for (const group of item.spec_groups || []) {
      const ids = selections[String(group.id)] || []
      if (group.required && ids.length === 0) valid = false
      for (const opt of group.options || []) {
        if (ids.includes(opt.id)) extra += Number(opt.price_delta || 0)
      }
    }
    const total = ((item.price || 0) + extra) * this.data.specQty
    this.setData({
      specPriceText: fen2text(total),
      specValid: valid,
    })
  },

  specConfirm() {
    const item = this.data.specItem
    if (!item || !this.data.specValid) return
    // 规格参数键统一用字符串组ID（后端兼容 int/str 键）
    const specs = {}
    const names = []
    for (const group of item.spec_groups || []) {
      const ids = this.data.specSelections[String(group.id)] || []
      if (ids.length > 0) specs[String(group.id)] = ids
      for (const opt of group.options || []) {
        if (ids.includes(opt.id)) names.push(opt.name)
      }
    }
    this.addLine(item, Object.keys(specs).length > 0 ? specs : null, names.join('/'), this.data.specQty)
    this.closeSpecModal()
  },

  // ==================== 购物车浮层 ====================

  toggleCart() {
    if (this.data.cartCount === 0) return
    this.setData({ showCart: !this.data.showCart })
  },

  closeCart() {
    this.setData({ showCart: false })
  },

  cartInc(e) {
    const key = e.currentTarget.dataset.key
    const line = this.data.cartMap[key]
    if (!line) return
    if (line.quantity >= 99) return
    this.setLineQty(key, line.quantity + 1)
  },

  cartDec(e) {
    const key = e.currentTarget.dataset.key
    const line = this.data.cartMap[key]
    if (!line) return
    this.setLineQty(key, line.quantity - 1)
  },

  clearCart() {
    this.setData({ cartMap: {}, showCart: false })
    this.refreshCart()
  },

  // ==================== 模式切换 / 桌号 ====================

  switchMode() {
    wx.showActionSheet({
      itemList: ['堂食', '自取（预约取餐）'],
      success: (res) => {
        const mode = res.tapIndex === 0 ? 'dine_in' : 'pickup'
        if (mode === 'dine_in' && !this.data.tableNo) {
          this.promptTableNo()
          return
        }
        this.setData({ mode })
        this.saveCtx()
      },
    })
  },

  promptTableNo() {
    wx.showModal({
      title: '请输入桌号',
      editable: true,
      placeholderText: '如：5',
      confirmText: '确定',
      success: (res) => {
        if (res.confirm && res.content && res.content.trim()) {
          this.setData({ mode: 'dine_in', tableNo: res.content.trim() })
          this.saveCtx()
        }
      },
    })
  },

  onTableTap() {
    this.promptTableNo()
  },

  // ==================== 去结算 ====================

  goCheckout() {
    if (!app.checkLogin()) return
    if (this.data.cartCount === 0) {
      wx.showToast({ title: '购物车是空的', icon: 'none' })
      return
    }
    if (this.data.mode === 'dine_in' && !this.data.tableNo) {
      this.promptTableNo()
      return
    }
    this.saveCtx()
    wx.navigateTo({ url: '/pages/food-checkout/food-checkout' })
  },

  goOrders() {
    wx.navigateTo({ url: '/pages/food-orders/food-orders' })
  },
})
