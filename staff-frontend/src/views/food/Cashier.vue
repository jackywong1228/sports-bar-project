<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import {
  getFoodMenu,
  createWalkInOrder,
  getFoodOrderPayStatus,
  cancelFoodOrderPay,
  type MenuCategory,
  type MenuItem
} from '@/api/food'
import PayCodeScanner from '@/components/PayCodeScanner.vue'

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
const payMethod = ref<'cash' | 'wechat_code'>('cash')
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
  payMethod.value = 'cash'
  checkoutVisible.value = true
}

function buildOrderPayload(payType: 'cash' | 'wechat_code', authCode?: string) {
  return {
    items: cart.value.map((l) => ({
      item_id: l.item.id,
      quantity: l.quantity,
      ...(Object.keys(l.specs).length > 0 ? { specs: l.specs } : {})
    })),
    pay_type: payType,
    ...(payType === 'wechat_code' && authCode ? { auth_code: authCode } : {}),
    order_type: orderType.value,
    ...(orderType.value === 'dine_in'
      ? { table_no: tableNo.value.trim() }
      : { pickup_time: fmtPickupTime(new Date()) }),
    ...(remark.value.trim() ? { remark: remark.value.trim() } : {})
  }
}

function validateCheckoutForm(): boolean {
  if (orderType.value === 'dine_in' && !tableNo.value.trim()) {
    showToast('堂食订单请填写桌号')
    return false
  }
  return true
}

/** 收款成功后的公共收尾（现金 / 微信共用）：清空购物车、重置表单、刷新菜单库存 */
function afterPaySuccess() {
  checkoutVisible.value = false
  wxPayVisible.value = false
  clearCart()
  tableNo.value = ''
  remark.value = ''
  // 刷新菜单（库存/售罄状态可能变化）
  loadMenu()
}

const submitOrder = async () => {
  if (checkoutLoading.value) return
  if (!validateCheckoutForm()) return
  if (payMethod.value === 'wechat_code') {
    // 微信收款：进入金额确认 → 扫码收款流程
    wxStartFlow()
    return
  }
  checkoutLoading.value = true
  try {
    const res = await createWalkInOrder(buildOrderPayload('cash'))
    showToast({ message: `收款成功 ${fmtAmount(res.data.pay_amount)}`, type: 'success' })
    afterPaySuccess()
  } catch (_e) {
    // 拦截器已 toast
  } finally {
    checkoutLoading.value = false
  }
}

// ── 微信付款码收款流程 ──
type WxStep = 'confirm' | 'scan' | 'submitting' | 'paying' | 'success'

const wxPayVisible = ref(false)
const wxStep = ref<WxStep>('confirm')
const wxScanRound = ref(0) // 每次进入扫码页递增，强制重挂载扫码组件
const wxOrderId = ref<number | null>(null)
const wxPayAmount = ref(0)
const wxCountdown = ref(60)
const wxCancelling = ref(false)
const WX_PAY_TIMEOUT = 60 // 轮询上限（秒）

let wxPollTimer: ReturnType<typeof setTimeout> | null = null
let wxTickTimer: ReturnType<typeof setInterval> | null = null
let wxSuccessTimer: ReturnType<typeof setTimeout> | null = null
let wxPollDeadline = 0
let wxPolling = false

const wxStartFlow = () => {
  wxStep.value = 'confirm'
  wxOrderId.value = null
  wxPayAmount.value = cartTotal.value
  wxPayVisible.value = true
}

const wxGoScan = () => {
  wxScanRound.value += 1
  wxStep.value = 'scan'
}

/** 拿到付款码 → 提交扣款 */
const wxSubmit = async (authCode: string) => {
  if (wxStep.value !== 'scan') return // 防重复提交
  wxStep.value = 'submitting'
  try {
    const res = await createWalkInOrder(buildOrderPayload('wechat_code', authCode))
    wxOrderId.value = res.data.order_id
    wxPayAmount.value = res.data.pay_amount
    if (res.data.status === 'paid') {
      wxShowSuccess()
    } else {
      // paying：等待顾客在手机上确认/输入密码，开始轮询
      wxStartPolling()
    }
  } catch (_e) {
    // HTTP 400 等失败：拦截器已 toast 中文原因，返回扫码页可重扫
    wxGoScan()
  }
}

const wxShowSuccess = () => {
  wxStopPolling()
  wxStep.value = 'success'
  wxSuccessTimer = setTimeout(() => {
    wxSuccessTimer = null
    wxStep.value = 'confirm'
    afterPaySuccess()
  }, 2500)
}

const wxStopPolling = () => {
  wxPolling = false
  if (wxPollTimer) { clearTimeout(wxPollTimer); wxPollTimer = null }
  if (wxTickTimer) { clearInterval(wxTickTimer); wxTickTimer = null }
}

const wxStartPolling = () => {
  wxStep.value = 'paying'
  wxPollDeadline = Date.now() + WX_PAY_TIMEOUT * 1000
  wxCountdown.value = WX_PAY_TIMEOUT
  wxPolling = true
  wxTickTimer = setInterval(() => {
    wxCountdown.value = Math.max(0, Math.ceil((wxPollDeadline - Date.now()) / 1000))
  }, 500)
  wxPollOnce()
}

const wxPollOnce = async () => {
  if (!wxPolling || wxOrderId.value == null) return
  if (Date.now() >= wxPollDeadline) {
    // 60s 超时：自动撤销并关单
    await wxCancelPay(true)
    return
  }
  try {
    const res = await getFoodOrderPayStatus(wxOrderId.value)
    const status = res.data.status
    if (status === 'paid') {
      wxShowSuccess()
      return
    }
    if (status === 'cancelled' || status === 'closed' || status === 'refunded') {
      wxStopPolling()
      showToast('支付已取消')
      wxGoScan()
      return
    }
  } catch (_e) {
    // 单次轮询失败（网络抖动）：继续，直到超时
  }
  wxPollTimer = setTimeout(wxPollOnce, 2000)
}

/** 取消收款（员工主动 / 超时自动） */
const wxCancelPay = async (auto = false) => {
  const orderId = wxOrderId.value
  if (orderId == null || wxCancelling.value) return
  if (!auto) {
    try {
      await showConfirmDialog({
        title: '取消收款',
        message: '确认取消这笔微信收款吗？订单将关闭。'
      })
    } catch (_e) {
      return // 员工点了「取消」
    }
  }
  wxCancelling.value = true
  wxStopPolling()
  try {
    await cancelFoodOrderPay(orderId)
  } catch (_e) {
    // 尽力撤销，失败也放行返回
  } finally {
    wxCancelling.value = false
  }
  wxOrderId.value = null
  if (auto) {
    showToast('收款超时已取消')
  }
  wxGoScan()
}

/** 关闭微信收款弹窗（paying 状态下需先取消收款） */
const wxClosePopup = () => {
  if (wxStep.value === 'submitting') return // 提交中禁止关闭
  if (wxStep.value === 'paying') {
    wxCancelPay()
    return
  }
  if (wxStep.value === 'success') return // 成功页自动关闭
  if (wxSuccessTimer) { clearTimeout(wxSuccessTimer); wxSuccessTimer = null }
  wxStopPolling()
  wxPayVisible.value = false
}

// 页面关闭/刷新时若仍在等待顾客输密码：浏览器提示 + 尽力撤销
const onBeforeUnload = (e: BeforeUnloadEvent) => {
  if (wxStep.value === 'paying' || wxStep.value === 'submitting') {
    e.preventDefault()
    e.returnValue = ''
    if (wxStep.value === 'paying' && wxOrderId.value != null) {
      wxFireAndForgetCancel(wxOrderId.value)
    }
  }
}

/** 尽力撤销（路由跳走/页面卸载场景，不等响应） */
function wxFireAndForgetCancel(orderId: number) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  const token = localStorage.getItem('staff_token')
  try {
    fetch(`${baseURL}/staff/food/orders/${orderId}/cancel-pay`, {
      method: 'POST',
      keepalive: true,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      }
    }).catch(() => { /* 尽力而为 */ })
  } catch (_e) { /* 忽略 */ }
}

onBeforeRouteLeave(() => {
  if (wxStep.value === 'paying' && wxOrderId.value != null) {
    wxFireAndForgetCancel(wxOrderId.value)
  }
  wxStopPolling()
})

function fmtAmount(n: number): string {
  return `¥${(n || 0).toFixed(2)}`
}

onMounted(() => {
  loadMenu()
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
  wxStopPolling()
  if (wxSuccessTimer) { clearTimeout(wxSuccessTimer); wxSuccessTimer = null }
  if (wxStep.value === 'paying' && wxOrderId.value != null) {
    wxFireAndForgetCancel(wxOrderId.value)
  }
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
              <van-radio-group v-model="payMethod" direction="horizontal">
                <van-radio name="cash">现金</van-radio>
                <van-radio name="wechat_code">微信收款</van-radio>
              </van-radio-group>
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
        >{{ payMethod === 'cash' ? `现金收款 ${fmtAmount(cartTotal)}` : `微信收款 ${fmtAmount(cartTotal)}` }}</van-button>
      </div>
    </van-popup>

    <!-- 微信付款码收款流程弹窗 -->
    <van-popup
      v-model:show="wxPayVisible"
      round
      position="bottom"
      :style="{ maxHeight: '88%' }"
      :close-on-click-overlay="false"
      @close="wxClosePopup"
      @closed="wxStep = 'confirm'"
    >
      <div class="wx-popup">
        <!-- 金额确认页 -->
        <template v-if="wxStep === 'confirm'">
          <div class="wx-title">微信收款</div>
          <div class="wx-confirm-amount">{{ fmtAmount(wxPayAmount) }}</div>
          <div class="wx-confirm-hint">请与顾客核对金额，确认无误后扫码收款</div>
          <van-button type="primary" block round size="large" @click="wxGoScan">扫码收款</van-button>
          <van-button block round size="large" class="wx-back-btn" @click="wxPayVisible = false">返回修改</van-button>
        </template>

        <!-- 扫码页 -->
        <template v-else-if="wxStep === 'scan'">
          <div class="wx-title">扫顾客付款码 · {{ fmtAmount(wxPayAmount) }}</div>
          <PayCodeScanner :key="wxScanRound" @scan="wxSubmit" />
          <van-button block round size="large" class="wx-back-btn" @click="wxStep = 'confirm'">返回</van-button>
        </template>

        <!-- 提交中 -->
        <template v-else-if="wxStep === 'submitting'">
          <div class="wx-state">
            <van-loading size="40" color="#1989fa" />
            <div class="wx-state-title">收款中，请勿关闭</div>
            <div class="wx-state-amount">{{ fmtAmount(wxPayAmount) }}</div>
          </div>
        </template>

        <!-- 等待顾客输入密码 -->
        <template v-else-if="wxStep === 'paying'">
          <div class="wx-state">
            <van-loading size="40" color="#ff976a" />
            <div class="wx-state-title">等待顾客输入密码…</div>
            <div class="wx-state-amount">{{ fmtAmount(wxPayAmount) }}</div>
            <div class="wx-countdown">{{ wxCountdown }}s 后自动取消</div>
            <van-button
              type="danger"
              plain
              round
              size="large"
              block
              :loading="wxCancelling"
              @click="wxCancelPay()"
            >取消收款</van-button>
          </div>
        </template>

        <!-- 收款成功 -->
        <template v-else-if="wxStep === 'success'">
          <div class="wx-state">
            <div class="wx-success-check">
              <van-icon name="checked" size="56" color="#07c160" />
            </div>
            <div class="wx-state-title success">收款成功</div>
            <div class="wx-state-amount">{{ fmtAmount(wxPayAmount) }}</div>
            <div class="wx-success-hint">小票打印中，即将返回收银台…</div>
          </div>
        </template>
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

/* ── 微信收款流程弹窗 ── */
.wx-popup {
  padding: 20px 16px calc(20px + env(safe-area-inset-bottom));
}

.wx-title {
  text-align: center;
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 8px;
}

.wx-confirm-amount {
  text-align: center;
  font-size: 42px;
  font-weight: 700;
  color: #ee6723;
  margin: 18px 0 6px;
}

.wx-confirm-hint {
  text-align: center;
  font-size: 13px;
  color: #888;
  margin-bottom: 22px;
}

.wx-back-btn {
  margin-top: 10px;
  background: #f2f3f5;
  color: #666;
  border: none;
}

.wx-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 28px 8px 8px;
}

.wx-state-title {
  font-size: 17px;
  font-weight: 600;
  color: #333;
}

.wx-state-title.success {
  color: #07c160;
}

.wx-state-amount {
  font-size: 30px;
  font-weight: 700;
  color: #ee6723;
}

.wx-countdown {
  font-size: 13px;
  color: #999;
}

.wx-success-check {
  animation: wx-pop 0.35s ease-out;
}

.wx-success-hint {
  font-size: 13px;
  color: #888;
}

@keyframes wx-pop {
  0% { transform: scale(0.3); opacity: 0; }
  70% { transform: scale(1.15); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
