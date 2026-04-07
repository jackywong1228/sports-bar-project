<template>
  <div class="page-container">
    <el-card class="search-card">
      <template #header>
        <span>扫码核销（会员 / 优惠券 / 预约）</span>
      </template>

      <!-- 当前服务场馆下拉（散客到店登记必须） -->
      <el-form :inline="true" style="margin-bottom: 8px;">
        <el-form-item label="当前服务场馆">
          <el-select
            v-model="currentVenueId"
            placeholder="选择当前服务台"
            style="width: 220px"
            @change="onVenueChange"
          >
            <el-option
              v-for="v in venueOptions"
              :key="v.id"
              :label="v.name"
              :value="v.id"
            />
          </el-select>
        </el-form-item>
      </el-form>

      <el-form :inline="true" @submit.prevent="handleVerify">
        <el-form-item label="编号">
          <el-input
            ref="inputRef"
            v-model="couponInput"
            placeholder="扫码或输入券号/预约号"
            clearable
            style="width: 400px; max-width: 90vw;"
            @keyup.enter="handleVerify"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleVerify">核销</el-button>
          <el-button
            :type="scanning ? 'danger' : 'success'"
            @click="scanning ? stopScan() : startScan('main')"
          >
            {{ scanning ? '停止扫码' : '扫一扫' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div style="color: #909399; font-size: 13px; margin-top: 8px;">
        支持会员动态码 (MEMBER:xxx)、优惠券 (COUPON_VERIFY:xx) 和预约 (VERIFY:xxx)，也可手动输入券号或预约编号
      </div>

      <div v-show="scanning" class="qr-reader-wrapper">
        <div id="qr-reader"></div>
        <div v-if="scanDebug" style="margin-top: 8px; color: #67C23A; font-size: 13px; text-align: center;">
          {{ scanDebug }}
        </div>
      </div>
    </el-card>

    <!-- 优惠券核销结果（旧） -->
    <el-card v-if="result?.kind === 'coupon'" class="result-card" style="margin-top: 16px;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px;">
          <el-icon color="#67C23A" :size="20"><CircleCheckFilled /></el-icon>
          <span>优惠券核销成功</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="券ID">{{ result.data.coupon_id }}</el-descriptions-item>
        <el-descriptions-item label="券名称">{{ result.data.coupon_name }}</el-descriptions-item>
        <el-descriptions-item label="券类型">
          <el-tag>{{ typeMap[result.data.coupon_type] || result.data.coupon_type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会员昵称">{{ result.data.member_nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="会员手机">{{ result.data.member_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="核销时间">{{ result.data.verified_at }}</el-descriptions-item>
        <el-descriptions-item label="核销人">{{ result.data.verified_by }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 预约核销结果（旧） -->
    <el-card v-if="result?.kind === 'reservation'" class="result-card" style="margin-top: 16px;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px;">
          <el-icon color="#67C23A" :size="20"><CircleCheckFilled /></el-icon>
          <span>预约核销成功</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="预约编号">{{ result.data.reservation_no }}</el-descriptions-item>
        <el-descriptions-item label="会员">
          {{ result.data.member_nickname || result.data.member_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="场馆">{{ result.data.venue_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="日期">{{ result.data.booking_date || '-' }}</el-descriptions-item>
        <el-descriptions-item label="时段">
          {{ result.data.start_time || '-' }} ~ {{ result.data.end_time || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="当前状态">
          <el-tag type="warning">{{ reservationStatusText(result.data.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="核销时间" :span="2">{{ result.data.verified_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 会员扫码结果（新） -->
    <el-card v-if="memberResult" class="result-card" style="margin-top: 16px;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <el-avatar :src="memberResult.member.avatar" :size="40">
            {{ (memberResult.member.nickname || '会').slice(0, 1) }}
          </el-avatar>
          <strong style="font-size: 16px;">{{ memberResult.member.nickname || '未命名会员' }}</strong>
          <el-tag
            :style="{ backgroundColor: memberResult.member.theme_color, borderColor: memberResult.member.theme_color, color: '#fff' }"
            effect="dark"
          >
            {{ memberResult.member.level_name }}
          </el-tag>
          <span style="color:#909399; font-size:13px;">
            <span v-if="memberResult.member.expire_time">会员到期 {{ memberResult.member.expire_time }}</span>
            <span v-else>未开通会员</span>
            <span style="margin-left: 8px;">本月剩余邀请 {{ memberResult.member.monthly_invite_remaining }}</span>
          </span>
          <el-button size="small" link @click="closeMemberResult">关闭</el-button>
        </div>
      </template>

      <!-- 待核销预约列表 -->
      <div v-if="memberResult.today_reservations.length > 0">
        <h4 style="margin: 0 0 12px 0;">今日待核销预约（{{ memberResult.today_reservations.length }}）</h4>
        <el-card
          v-for="r in memberResult.today_reservations"
          :key="r.id"
          shadow="hover"
          style="margin-bottom: 8px;"
        >
          <div style="display:flex; justify-content:space-between; align-items:center; gap: 8px;">
            <div style="flex: 1;">
              <div style="font-size: 14px;">
                <strong>{{ r.venue_name }}</strong>
                <span style="margin-left: 8px;">{{ r.start_time }} - {{ r.end_time }}</span>
                <span style="color:#909399; margin-left: 8px;">({{ r.duration }}分钟)</span>
              </div>
              <div v-if="r.coach_name" style="color:#909399; font-size:13px; margin-top: 4px;">
                教练：{{ r.coach_name }}
              </div>
              <div style="color:#E6A23C; font-size:13px; margin-top: 4px;">
                ¥{{ r.total_price }}（{{ payTypeText(r.pay_type) }}）
              </div>
            </div>
            <el-button
              type="success"
              :loading="verifyingId === r.id"
              @click="verifyReservationItem(r.id)"
            >
              核销
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 散客场景 -->
      <div v-else>
        <el-alert title="该会员今日无可核销预约" type="warning" :closable="false" />
        <div style="margin-top: 12px;">
          <el-checkbox v-model="hasInviter" @change="onHasInviterChange">
            是否由会员邀请而来（仅 SS/SSS 会员可担保邀请）
          </el-checkbox>
        </div>

        <!-- 未扫邀请人码 -->
        <div v-if="hasInviter && !inviterToken" style="margin-top: 8px; color: #E6A23C;">
          请扫描邀请人的会员二维码 →
          <el-button size="small" type="primary" @click="startScan('inviter')">
            扫邀请人码
          </el-button>
        </div>

        <!-- 已扫邀请人码 -->
        <div v-if="hasInviter && inviterToken" style="margin-top: 8px; color: #67C23A;">
          ✓ 已记录邀请人 token
          <el-button size="small" link type="danger" @click="inviterToken = ''">清除</el-button>
        </div>

        <el-button
          type="primary"
          style="margin-top: 12px;"
          :disabled="currentVenueId === null || (hasInviter && !inviterToken)"
          :loading="walkInLoading"
          @click="handleWalkInCheckin"
        >
          记一条到店记录
        </el-button>
        <div v-if="currentVenueId === null" style="margin-top: 8px; color: #F56C6C; font-size: 12px;">
          请先在顶部选择"当前服务场馆"
        </div>
      </div>
    </el-card>

    <!-- 错误提示 -->
    <el-card v-if="errorMsg" class="result-card" style="margin-top: 16px;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px;">
          <el-icon color="#F56C6C" :size="20"><CircleCloseFilled /></el-icon>
          <span>核销失败</span>
        </div>
      </template>
      <div style="color: #F56C6C; font-size: 15px;">{{ errorMsg }}</div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { verifyCoupon } from '@/api/coupon'
import { verifyReservationByNo } from '@/api/reservation'
import { getVenueList } from '@/api/venue'
import {
  staffScanMember,
  staffVerifyWithCheckin,
  staffWalkInCheckin,
} from '@/api/staff'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'

type ScanTarget =
  | { kind: 'coupon'; couponId: number }
  | { kind: 'reservation'; reservationNo: string }
  | { kind: 'member'; token: string }
  | null

type VerifyResult =
  | { kind: 'coupon'; data: any }
  | { kind: 'reservation'; data: any }
  | null

interface MemberScanResult {
  member: {
    id: number
    nickname: string
    phone: string
    avatar: string
    level_code: string
    level_name: string
    theme_color: string
    expire_time: string | null
    subscription_status: string
    monthly_invite_remaining: number
  }
  today_reservations: Array<{
    id: number
    reservation_no: string
    venue_id: number
    venue_name: string
    start_time: string
    end_time: string
    duration: number
    coach_id: number | null
    coach_name: string | null
    total_price: number
    pay_type: string
    status: string
  }>
}

type ScanMode = 'main' | 'inviter'

const couponInput = ref('')
const loading = ref(false)
const result = ref<VerifyResult>(null)
const errorMsg = ref('')
const inputRef = ref()
const scanning = ref(false)
const scanDebug = ref('')

// 当前服务场馆
const currentVenueId = ref<number | null>(null)
const venueOptions = ref<Array<{ id: number; name: string }>>([])

// 会员扫码相关
const memberResult = ref<MemberScanResult | null>(null)
const verifyingId = ref<number | null>(null)
const hasInviter = ref(false)
const inviterToken = ref('')
const walkInLoading = ref(false)

let html5Qrcode: Html5Qrcode | null = null
let scanMode: ScanMode = 'main'

const VENUE_LS_KEY = 'staff_current_venue_id'

const typeMap: Record<string, string> = {
  cash: '代金券',
  discount: '折扣券',
  gift: '赠品券',
  hour_free: '时长券',
  experience: '体验券'
}

const reservationStatusMap: Record<string, string> = {
  pending: '待确认',
  confirmed: '已确认',
  in_progress: '进行中',
  completed: '已完成',
  cancelled: '已取消',
}

function reservationStatusText(status: string): string {
  return reservationStatusMap[status] || status || '-'
}

function payTypeText(payType: string): string {
  if (payType === 'coin') return '金币'
  if (payType === 'wechat') return '微信'
  if (payType === 'free') return '免费'
  return payType || '-'
}

function parseScanInput(raw: string): ScanTarget {
  const input = (raw || '').trim()
  if (!input) return null

  // 会员动态二维码：MEMBER:<jwt>
  if (input.startsWith('MEMBER:')) {
    const token = input.substring('MEMBER:'.length).trim()
    return token ? { kind: 'member', token } : null
  }

  // 预约二维码：VERIFY:xxx (member_api.py:_generate_verify_qrcode)
  if (input.startsWith('VERIFY:')) {
    const no = input.substring('VERIFY:'.length).trim()
    return no ? { kind: 'reservation', reservationNo: no } : null
  }

  // 优惠券二维码：COUPON_VERIFY:xxx
  if (input.startsWith('COUPON_VERIFY:')) {
    const id = parseInt(input.substring('COUPON_VERIFY:'.length), 10)
    return isNaN(id) ? null : { kind: 'coupon', couponId: id }
  }

  // 兜底：纯数字 → 当优惠券（保持老行为）
  if (/^\d+$/.test(input)) {
    return { kind: 'coupon', couponId: parseInt(input, 10) }
  }

  // 其他字母数字串 → 当预约编号
  if (/^[A-Za-z0-9_-]+$/.test(input)) {
    return { kind: 'reservation', reservationNo: input }
  }

  return null
}

function clearAllResults() {
  result.value = null
  memberResult.value = null
  errorMsg.value = ''
  hasInviter.value = false
  inviterToken.value = ''
}

function closeMemberResult() {
  memberResult.value = null
  hasInviter.value = false
  inviterToken.value = ''
}

function onVenueChange(id: number | null) {
  // 包含哨兵值 0（散客接待），只有 null 才不持久化
  if (id !== null && id !== undefined) {
    localStorage.setItem(VENUE_LS_KEY, String(id))
  }
}

function onHasInviterChange(val: boolean) {
  if (!val) {
    inviterToken.value = ''
  }
}

async function handleVerify() {
  const target = parseScanInput(couponInput.value)
  if (!target) {
    ElMessage.warning('请输入有效的二维码内容或编号')
    return
  }

  // 会员动态二维码：直接调接口，不弹确认框
  if (target.kind === 'member') {
    loading.value = true
    clearAllResults()
    try {
      const res: any = await staffScanMember({
        token: target.token,
        current_venue_id: currentVenueId.value ?? undefined,
      })
      memberResult.value = res.data as MemberScanResult
      couponInput.value = ''
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || '扫码失败'
      errorMsg.value = detail
    } finally {
      loading.value = false
      nextTick(() => inputRef.value?.focus())
    }
    return
  }

  // 优惠券/预约：保留旧的确认弹窗流程
  const confirmText =
    target.kind === 'coupon'
      ? `确认核销券号 ${target.couponId} ？核销后不可撤销。`
      : `确认核销预约 ${target.reservationNo} ？核销后不可撤销。`

  try {
    await ElMessageBox.confirm(
      confirmText,
      '确认核销',
      { confirmButtonText: '确认核销', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  loading.value = true
  clearAllResults()

  try {
    if (target.kind === 'coupon') {
      const res: any = await verifyCoupon({ coupon_id: target.couponId })
      result.value = { kind: 'coupon', data: res.data }
    } else {
      const res: any = await verifyReservationByNo(target.reservationNo)
      result.value = { kind: 'reservation', data: res.data }
    }
    ElMessage.success('核销成功')
    couponInput.value = ''
  } catch (err: any) {
    const detail = err.response?.data?.detail || err.message || '核销失败'
    errorMsg.value = detail
  } finally {
    loading.value = false
    nextTick(() => inputRef.value?.focus())
  }
}

// 单条预约核销（会员卡片内的 [核销] 按钮）
async function verifyReservationItem(reservationId: number) {
  try {
    await ElMessageBox.confirm(
      `确认核销该预约？核销后将同步打卡。`,
      '确认核销',
      { confirmButtonText: '核销', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }

  verifyingId.value = reservationId
  try {
    const res: any = await staffVerifyWithCheckin({ reservation_id: reservationId })
    const data = res.data || {}
    const points = data.points_earned || 0
    ElMessage.success(points > 0 ? `核销成功 +${points} 积分` : '核销成功')

    // 从列表移除已核销的项
    if (memberResult.value) {
      memberResult.value.today_reservations = memberResult.value.today_reservations.filter(
        (r) => r.id !== reservationId
      )
    }
  } catch (err: any) {
    const detail = err.response?.data?.detail || err.message || '核销失败'
    ElMessage.error(detail)
  } finally {
    verifyingId.value = null
  }
}

// 散客到店登记
async function handleWalkInCheckin() {
  if (!memberResult.value || currentVenueId.value === null) return

  if (hasInviter.value && !inviterToken.value) {
    ElMessage.warning('请先扫描邀请人的会员二维码')
    return
  }

  walkInLoading.value = true
  try {
    const res: any = await staffWalkInCheckin({
      member_id: memberResult.value.member.id,
      current_venue_id: currentVenueId.value,
      inviter_token: hasInviter.value ? inviterToken.value : undefined,
    })
    const data = res.data || {}
    let msg = '到店登记成功'
    if (typeof data.inviter_remaining === 'number') {
      msg += `（邀请人本月剩余 ${data.inviter_remaining} 次）`
    }
    ElMessage.success(msg)
    closeMemberResult()
  } catch (err: any) {
    const detail = err.response?.data?.detail || err.message || '登记失败'
    ElMessage.error(detail)
  } finally {
    walkInLoading.value = false
  }
}

async function startScan(mode: ScanMode = 'main') {
  try {
    scanMode = mode
    scanning.value = true
    await nextTick()

    html5Qrcode = new Html5Qrcode('qr-reader', {
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
      verbose: false,
    })

    let frameCount = 0
    scanDebug.value = mode === 'inviter'
      ? '请扫描邀请人会员动态码（MEMBER:开头）...'
      : '摄像头已启动，请对准二维码...'

    await html5Qrcode.start(
      { facingMode: 'environment' },
      { fps: 10 },
      (decodedText) => {
        scanDebug.value = '识别成功: ' + decodedText
        // 邀请人扫码：要求 MEMBER: 协议
        if (scanMode === 'inviter') {
          if (decodedText.startsWith('MEMBER:')) {
            const token = decodedText.substring('MEMBER:'.length).trim()
            if (token) {
              inviterToken.value = token
              ElMessage.success('已记录邀请人 token')
              stopScan()
              return
            }
          }
          ElMessage.error('请扫描会员动态码（MEMBER:开头）')
          stopScan()
          return
        }
        // 主扫码：填入输入框并触发验证流程
        couponInput.value = decodedText
        stopScan()
        handleVerify()
      },
      () => {
        frameCount++
        if (frameCount % 30 === 0) {
          scanDebug.value = `扫描中... 已分析 ${frameCount} 帧，未识别到二维码`
        }
      }
    )
  } catch (err) {
    scanning.value = false
    scanDebug.value = ''
    console.error('摄像头启动失败:', err)
    ElMessage.error('无法启动摄像头，请检查权限或使用 HTTPS 访问')
  }
}

async function stopScan() {
  if (html5Qrcode) {
    try {
      await html5Qrcode.stop()
    } catch {
      // 忽略停止时的错误
    }
    html5Qrcode = null
  }
  scanning.value = false
}

async function loadVenues() {
  try {
    const res: any = await getVenueList({ page: 1, page_size: 100 })
    const list = res.data?.items || res.data || []
    // 过滤掉后端的"散客接待"虚拟场馆行（避免和顶部哨兵项重复）
    const realVenues = (list as any[])
      .filter((v) => v.name !== '散客接待')
      .map((v) => ({ id: v.id, name: v.name }))
    // 顶部固定加一项哨兵：散客接待（无场地），value=0
    venueOptions.value = [
      { id: 0, name: '散客接待（无场地）' },
      ...realVenues,
    ]

    // 从 localStorage 恢复（包括 id=0）
    const saved = localStorage.getItem(VENUE_LS_KEY)
    if (saved !== null) {
      const id = parseInt(saved, 10)
      if (!isNaN(id) && venueOptions.value.some((v) => v.id === id)) {
        currentVenueId.value = id
      }
    }
  } catch (err) {
    console.error('加载场馆列表失败:', err)
  }
}

onMounted(() => {
  inputRef.value?.focus()
  loadVenues()
})

onBeforeUnmount(() => {
  stopScan()
})
</script>

<style scoped>
.page-container {
  padding: 20px;
}
.search-card {
  margin-bottom: 0;
}
.result-card :deep(.el-descriptions) {
  margin-top: 0;
}
.qr-reader-wrapper {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
#qr-reader {
  width: 100%;
  max-width: 400px;
}
</style>
