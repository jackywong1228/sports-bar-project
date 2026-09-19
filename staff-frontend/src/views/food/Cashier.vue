<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import {
  getFoodMenu,
  createWalkInOrder,
  type MenuCategory,
  type MenuItem
} from '@/api/food'

const router = useRouter()

// ── 菜单数据 ──
const menuLoading = ref(true)
const categories = ref<MenuCategory[]>([])
const activeCatIndex = ref(0)

const activeItems = computed<MenuItem[]>(() => {
  return categories.value[activeCatIndex.value]?.items || []
})

const loadMenu = async () => {
  menuLoading.value = true
  try {
    const res = await getFoodMenu()
    categories.value = res.data || []
    activeCatIndex.value = 0
  } finally {
    menuLoading.value = false
  }
}

// ── 购物车 ──
interface CartLine {
  key: string
  item: MenuItem
  specs: Record<string, number[]>
  specsText: string
  unitPrice: number
  quantity: number
}

const cart = ref<CartLine[]>([])

const cartTotal = computed(() =>
  cart.value.reduce((sum, l) => sum + l.unitPrice * l.quantity, 0)
)
const cartCount = computed(() =>
  cart.value.reduce((sum, l) => sum + l.quantity, 0)
)

function buildKey(itemId: number, specs: Record<string, number[]>): string {
  const specPart = Object.keys(specs)
    .sort()
    .map((g) => `${g}:${[...(specs[g] || [])].sort((a, b) => a - b).join(',')}`)
    .join('|')
  return `${itemId}#${specPart}`
}

function addToCart(item: MenuItem, specs: Record<string, number[]>, specsText: string, unitPrice: number, qty: number) {
  const key = buildKey(item.id, specs)
  const existing = cart.value.find((l) => l.key === key)
  if (existing) {
    existing.quantity += qty
  } else {
    cart.value.push({ key, item, specs, specsText, unitPrice, quantity: qty })
  }
}

const onItemClick = (item: MenuItem) => {
  if (item.sold_out) return
  if (item.has_specs && item.spec_groups.length > 0) {
    openSpecPopup(item)
  } else {
    addToCart(item, {}, '', item.price, 1)
  }
}

const changeQty = (line: CartLine, delta: number) => {
  line.quantity += delta
  if (line.quantity <= 0) {
    cart.value = cart.value.filter((l) => l.key !== line.key)
  }
}

const removeLine = (line: CartLine) => {
  cart.value = cart.value.filter((l) => l.key !== line.key)
}

const clearCart = () => {
  cart.value = []
}

// ── 规格选择弹窗 ──
const specVisible = ref(false)
const specItem = ref<MenuItem | null>(null)
const specSelections = ref<Record<number, number[]>>({})
const specQty = ref(1)

function openSpecPopup(item: MenuItem) {
  specItem.value = item
  specQty.value = 1
  const init: Record<number, number[]> = {}
  for (const g of item.spec_groups) {
    // 单选必选组默认选中第一个选项，减少操作步骤
    init[g.id] = g.select_type === 'single' && g.required && g.options.length > 0 ? [g.options[0]!.id] : []
  }
  specSelections.value = init
  specVisible.value = true
}

const toggleOption = (groupId: number, optionId: number, selectType: string) => {
  const current = specSelections.value[groupId] || []
  if (selectType === 'single') {
    specSelections.value[groupId] = [optionId]
  } else {
    specSelections.value[groupId] = current.includes(optionId)
      ? current.filter((id) => id !== optionId)
      : [...current, optionId]
  }
}

const isOptionSelected = (groupId: number, optionId: number) =>
  (specSelections.value[groupId] || []).includes(optionId)

const specUnitPrice = computed(() => {
  if (!specItem.value) return 0
  let price = specItem.value.price
  for (const g of specItem.value.spec_groups) {
    for (const optId of specSelections.value[g.id] || []) {
      const opt = g.options.find((o) => o.id === optId)
      if (opt) price += opt.price_delta
    }
  }
  return price
})

const confirmSpec = () => {
  const item = specItem.value
  if (!item) return
  const specNames: string[] = []
  const specs: Record<string, number[]> = {}
  for (const g of item.spec_groups) {
    const selected = specSelections.value[g.id] || []
    if (g.required && selected.length === 0) {
      showToast(`请选择「${g.name}」`)
      return
    }
    if (selected.length > 0) {
      specs[String(g.id)] = selected
      const names = g.options.filter((o) => selected.includes(o.id)).map((o) => o.name)
      specNames.push(...names)
    }
  }
  addToCart(item, specs, specNames.join('/'), specUnitPrice.value, specQty.value)
  specVisible.value = false
}

// ── 结算 ──
const checkoutVisible = ref(false)
const checkoutLoading = ref(false)
const orderType = ref<'dine_in' | 'pickup'>('dine_in')
const tableNo = ref('')
const remark = ref('')
const cartExpanded = ref(false)

function fmtPickupTime(d: Date): string {
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

const openCheckout = () => {
  if (cart.value.length === 0) {
    showToast('购物车为空')
    return
  }
  checkoutVisible.value = true
}

const submitOrder = async () => {
  if (checkoutLoading.value) return
  if (orderType.value === 'dine_in' && !tableNo.value.trim()) {
    showToast('堂食订单请填写桌号')
    return
  }
  checkoutLoading.value = true
  try {
    const payload = {
      items: cart.value.map((l) => ({
        item_id: l.item.id,
        quantity: l.quantity,
        ...(Object.keys(l.specs).length > 0 ? { specs: l.specs } : {})
      })),
      pay_type: 'cash' as const,
      order_type: orderType.value,
      ...(orderType.value === 'dine_in'
        ? { table_no: tableNo.value.trim() }
        : { pickup_time: fmtPickupTime(new Date()) }),
      ...(remark.value.trim() ? { remark: remark.value.trim() } : {})
    }
    const res = await createWalkInOrder(payload)
    showToast({ message: `收款成功 ${fmtAmount(res.data.pay_amount)}`, type: 'success' })
    checkoutVisible.value = false
    clearCart()
    tableNo.value = ''
    remark.value = ''
    // 刷新菜单（库存/售罄状态可能变化）
    loadMenu()
  } catch (_e) {
    // 拦截器已 toast
  } finally {
    checkoutLoading.value = false
  }
}

function fmtAmount(n: number): string {
  return `¥${(n || 0).toFixed(2)}`
}

onMounted(() => {
  loadMenu()
})
</script>

<template>
  <div class="page-container cashier-page">
    <van-nav-bar title="收银台" left-arrow @click-left="router.back()">
      <template #right>
        <van-icon name="orders-o" size="20" @click="router.push('/food/orders')" />
      </template>
    </van-nav-bar>

    <div v-if="menuLoading" class="loading-wrap">
      <van-loading size="36" />
    </div>

    <div v-else-if="categories.length === 0" class="loading-wrap">
      <van-empty description="暂无在售商品" />
    </div>

    <div v-else class="cashier-body">
      <!-- 商品区 -->
      <div class="menu-area">
        <van-sidebar v-model="activeCatIndex" class="cat-sidebar">
          <van-sidebar-item v-for="cat in categories" :key="cat.id" :title="cat.name" />
        </van-sidebar>

        <div class="item-grid-wrap">
          <div class="item-grid">
            <div
              v-for="item in activeItems"
              :key="item.id"
              class="item-card"
              :class="{ 'sold-out': item.sold_out }"
              @click="onItemClick(item)"
            >
              <div class="item-name">{{ item.name }}</div>
              <div class="item-bottom">
                <span class="item-price">{{ fmtAmount(item.price) }}</span>
                <van-tag v-if="item.has_specs" size="medium" plain type="primary">规格</van-tag>
              </div>
              <div v-if="item.sold_out" class="sold-out-mask">已售罄</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 购物车栏 -->
      <div class="cart-panel" :class="{ expanded: cartExpanded }">
        <div class="cart-header" @click="cartExpanded = !cartExpanded">
          <div class="cart-summary">
            <van-icon name="shopping-cart-o" size="22" />
            <van-badge v-if="cartCount > 0" :content="cartCount" class="cart-badge" />
            <span class="cart-total">{{ fmtAmount(cartTotal) }}</span>
          </div>
          <div class="cart-header-actions" @click.stop>
            <van-button size="mini" plain type="danger" :disabled="cart.length === 0" @click="clearCart">清空</van-button>
            <van-button
              size="small"
              type="primary"
              round
              :disabled="cart.length === 0"
              @click="openCheckout"
            >结算</van-button>
          </div>
        </div>

        <div class="cart-lines">
          <div v-for="line in cart" :key="line.key" class="cart-line">
            <div class="line-info">
              <div class="line-name">{{ line.item.name }}</div>
              <div v-if="line.specsText" class="line-specs">{{ line.specsText }}</div>
              <div class="line-price">{{ fmtAmount(line.unitPrice) }}</div>
            </div>
            <div class="line-actions">
              <van-button size="mini" round icon="minus" @click="changeQty(line, -1)" />
              <span class="line-qty">{{ line.quantity }}</span>
              <van-button size="mini" round icon="plus" type="primary" @click="changeQty(line, 1)" />
              <van-icon name="delete-o" size="18" color="#ee0a24" class="line-del" @click="removeLine(line)" />
            </div>
          </div>
          <van-empty v-if="cart.length === 0" description="点击商品加入购物车" image-size="60" />
        </div>
      </div>
    </div>

    <!-- 规格选择弹窗 -->
    <van-popup v-model:show="specVisible" round position="bottom" :style="{ maxHeight: '75%' }">
      <div v-if="specItem" class="spec-popup">
        <div class="spec-header">
          <div class="spec-title">{{ specItem.name }}</div>
          <div class="spec-price">{{ fmtAmount(specUnitPrice) }}</div>
        </div>

        <div v-for="group in specItem.spec_groups" :key="group.id" class="spec-group">
          <div class="spec-group-name">
            {{ group.name }}
            <span class="spec-group-hint">
              {{ group.select_type === 'single' ? '单选' : '多选' }}<template v-if="group.required"> · 必选</template>
            </span>
          </div>
          <div class="spec-options">
            <div
              v-for="opt in group.options"
              :key="opt.id"
              class="spec-option"
              :class="{ active: isOptionSelected(group.id, opt.id) }"
              @click="toggleOption(group.id, opt.id, group.select_type)"
            >
              {{ opt.name }}
              <span v-if="opt.price_delta > 0" class="spec-delta">+{{ fmtAmount(opt.price_delta) }}</span>
            </div>
          </div>
        </div>

        <div class="spec-footer">
          <van-stepper v-model="specQty" min="1" max="99" />
          <van-button type="primary" round block class="spec-confirm" @click="confirmSpec">
            加入购物车 {{ fmtAmount(specUnitPrice * specQty) }}
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 结算弹窗 -->
    <van-popup v-model:show="checkoutVisible" round position="bottom" :style="{ maxHeight: '80%' }">
      <div class="checkout-popup">
        <div class="checkout-title">结算</div>

        <van-cell-group inset>
          <van-cell title="支付方式">
            <template #value>
              <van-tag type="success" size="large">现金</van-tag>
            </template>
          </van-cell>
          <van-cell title="订单类型">
            <template #value>
              <van-radio-group v-model="orderType" direction="horizontal">
                <van-radio name="dine_in">堂食</van-radio>
                <van-radio name="pickup">自取</van-radio>
              </van-radio-group>
            </template>
          </van-cell>
          <van-field
            v-if="orderType === 'dine_in'"
            v-model="tableNo"
            label="桌号"
            placeholder="必填，如 A12"
            maxlength="20"
          />
          <van-cell v-else title="取餐时间" value="立即（现在）" />
          <van-field v-model="remark" label="备注" placeholder="选填" maxlength="200" />
        </van-cell-group>

        <div class="checkout-total">
          <span>共 {{ cartCount }} 件</span>
          <span class="checkout-amount">{{ fmtAmount(cartTotal) }}</span>
        </div>

        <van-button
          type="primary"
          block
          round
          size="large"
          :loading="checkoutLoading"
          :disabled="cart.length === 0"
          @click="submitOrder"
        >现金收款 {{ fmtAmount(cartTotal) }}</van-button>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.cashier-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.loading-wrap {
  padding: 60px 0;
  text-align: center;
}

.cashier-body {
  flex: 1;
  display: flex;
  min-height: 0;
}

/* ── 商品区 ── */
.menu-area {
  flex: 1;
  display: flex;
  min-height: 0;
  min-width: 0;
}

.cat-sidebar {
  width: 96px;
  flex-shrink: 0;
  overflow-y: auto;
}

.item-grid-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.item-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: 10px;
}

.item-card {
  position: relative;
  background: #fff;
  border-radius: 10px;
  padding: 14px 12px;
  min-height: 72px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  user-select: none;
}

.item-card:active {
  opacity: 0.7;
}

.item-card.sold-out {
  opacity: 0.45;
  cursor: not-allowed;
}

.item-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  line-height: 1.4;
}

.item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.item-price {
  color: #ee6723;
  font-weight: 600;
  font-size: 15px;
}

.sold-out-mask {
  position: absolute;
  top: 6px;
  right: 6px;
  font-size: 11px;
  color: #999;
}

/* ── 购物车 ── */
.cart-panel {
  width: clamp(280px, 32%, 380px);
  flex-shrink: 0;
  background: #fff;
  border-left: 1px solid #eee;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.cart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #f2f2f2;
  cursor: pointer;
}

.cart-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
}

.cart-total {
  font-size: 18px;
  font-weight: 700;
  color: #ee6723;
}

.cart-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cart-lines {
  flex: 1;
  overflow-y: auto;
  padding: 8px 14px;
}

.cart-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
  gap: 8px;
}

.line-info {
  flex: 1;
  min-width: 0;
}

.line-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.line-specs {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.line-price {
  font-size: 13px;
  color: #ee6723;
  margin-top: 2px;
}

.line-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.line-qty {
  min-width: 22px;
  text-align: center;
  font-weight: 600;
}

.line-del {
  margin-left: 4px;
}

/* ── 窄屏：购物车变底部抽屉 ── */
@media (max-width: 700px) {
  .cashier-body {
    flex-direction: column;
    position: relative;
  }

  .cart-panel {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    width: auto;
    max-height: 70%;
    border-left: none;
    border-top: 1px solid #eee;
    box-shadow: 0 -2px 12px rgba(0, 0, 0, 0.1);
    z-index: 10;
  }

  .cart-panel .cart-lines {
    display: none;
  }

  .cart-panel.expanded .cart-lines {
    display: block;
    max-height: 40vh;
  }

  .menu-area {
    padding-bottom: 60px;
  }
}

/* ── 规格弹窗 ── */
.spec-popup {
  padding: 20px 16px calc(16px + env(safe-area-inset-bottom));
}

.spec-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.spec-title {
  font-size: 17px;
  font-weight: 600;
}

.spec-price {
  font-size: 17px;
  font-weight: 700;
  color: #ee6723;
}

.spec-group {
  margin-bottom: 16px;
}

.spec-group-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
}

.spec-group-hint {
  font-size: 12px;
  color: #999;
  font-weight: 400;
  margin-left: 6px;
}

.spec-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.spec-option {
  padding: 7px 14px;
  border-radius: 8px;
  background: #f5f5f5;
  font-size: 13px;
  color: #333;
  cursor: pointer;
  user-select: none;
}

.spec-option.active {
  background: var(--van-primary-color);
  color: #fff;
}

.spec-delta {
  font-size: 12px;
  opacity: 0.85;
}

.spec-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.spec-confirm {
  flex: 1;
}

/* ── 结算弹窗 ── */
.checkout-popup {
  padding: 20px 0 calc(20px + env(safe-area-inset-bottom));
}

.checkout-title {
  text-align: center;
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 12px;
}

.checkout-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  font-size: 14px;
  color: #666;
}

.checkout-amount {
  font-size: 22px;
  font-weight: 700;
  color: #ee6723;
}

.checkout-popup .van-button {
  width: calc(100% - 32px);
  margin: 0 16px;
}
</style>
