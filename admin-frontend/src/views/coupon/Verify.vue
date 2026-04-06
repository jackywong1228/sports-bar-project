<template>
  <div class="page-container">
    <el-card class="search-card">
      <template #header>
        <span>扫码核销（优惠券 / 预约）</span>
      </template>
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
            @click="scanning ? stopScan() : startScan()"
          >
            {{ scanning ? '停止扫码' : '扫一扫' }}
          </el-button>
        </el-form-item>
      </el-form>
      <div style="color: #909399; font-size: 13px; margin-top: 8px;">
        支持优惠券二维码 (COUPON_VERIFY:xx) 和预约二维码 (VERIFY:xxx)，也可手动输入券号或预约编号
      </div>

      <div v-show="scanning" class="qr-reader-wrapper">
        <div id="qr-reader"></div>
        <div v-if="scanDebug" style="margin-top: 8px; color: #67C23A; font-size: 13px; text-align: center;">
          {{ scanDebug }}
        </div>
      </div>
    </el-card>

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
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'

type ScanTarget =
  | { kind: 'coupon'; couponId: number }
  | { kind: 'reservation'; reservationNo: string }
  | null

type VerifyResult =
  | { kind: 'coupon'; data: any }
  | { kind: 'reservation'; data: any }
  | null

const couponInput = ref('')
const loading = ref(false)
const result = ref<VerifyResult>(null)
const errorMsg = ref('')
const inputRef = ref()
const scanning = ref(false)
const scanDebug = ref('')

let html5Qrcode: Html5Qrcode | null = null

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

function parseScanInput(raw: string): ScanTarget {
  const input = (raw || '').trim()
  if (!input) return null

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

  // 其他字母数字串 → 当预约编号（reservation_no 格式如 RES20260405xxxABC）
  if (/^[A-Za-z0-9_-]+$/.test(input)) {
    return { kind: 'reservation', reservationNo: input }
  }

  return null
}

async function handleVerify() {
  const target = parseScanInput(couponInput.value)
  if (!target) {
    ElMessage.warning('请输入有效的券号或预约编号')
    return
  }

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
  result.value = null
  errorMsg.value = ''

  try {
    if (target.kind === 'coupon') {
      const res = await verifyCoupon({ coupon_id: target.couponId })
      result.value = { kind: 'coupon', data: res.data }
    } else {
      const res = await verifyReservationByNo(target.reservationNo)
      result.value = { kind: 'reservation', data: res.data }
    }
    ElMessage.success('核销成功')
    couponInput.value = ''
  } catch (err: any) {
    const detail = err.response?.data?.detail || err.message || '核销失败'
    errorMsg.value = detail
  } finally {
    loading.value = false
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
}

async function startScan() {
  try {
    // 1. 先显示容器，确保 DOM 尺寸正确
    scanning.value = true
    await nextTick()

    // 2. 容器可见后再创建实例（只检测 QR 码）
    html5Qrcode = new Html5Qrcode('qr-reader', {
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
      verbose: false,
    })

    let frameCount = 0
    scanDebug.value = '摄像头已启动，请对准二维码...'

    await html5Qrcode.start(
      { facingMode: 'environment' },
      { fps: 10 },
      (decodedText) => {
        // 扫码成功
        scanDebug.value = '识别成功: ' + decodedText
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

onMounted(() => {
  inputRef.value?.focus()
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
  justify-content: center;
}
#qr-reader {
  width: 100%;
  max-width: 400px;
}
</style>
