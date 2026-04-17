<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { Html5Qrcode } from 'html5-qrcode'
import { verifyReservationByNo } from '@/api/reservation'

const router = useRouter()

const scanning = ref(false)
const result = ref<any>(null)
const error = ref('')
let html5Qrcode: Html5Qrcode | null = null

const startScan = async () => {
  result.value = null
  error.value = ''
  scanning.value = true

  try {
    html5Qrcode = new Html5Qrcode('qr-reader')
    await html5Qrcode.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 250, height: 250 } },
      onScanSuccess,
      () => {} // 忽略扫描失败
    )
  } catch (e: any) {
    error.value = '无法打开相机：' + (e.message || e)
    scanning.value = false
  }
}

const stopScan = async () => {
  if (html5Qrcode) {
    try {
      await html5Qrcode.stop()
    } catch (_e) { /* 忽略 */ }
    html5Qrcode = null
  }
  scanning.value = false
}

const onScanSuccess = async (decodedText: string) => {
  await stopScan()

  // 解析二维码内容：VERIFY:{reservation_no}
  let reservationNo = decodedText
  if (decodedText.startsWith('VERIFY:')) {
    reservationNo = decodedText.substring(7)
  }

  if (!reservationNo) {
    error.value = '无效的二维码内容'
    return
  }

  try {
    const res = await verifyReservationByNo(reservationNo)
    result.value = res.data
    showToast({ message: '核销成功', type: 'success' })
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || '核销失败'
  }
}

const handleContinue = () => {
  result.value = null
  error.value = ''
  startScan()
}

onMounted(() => {
  startScan()
})

onUnmounted(() => {
  stopScan()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="扫码核销" left-arrow @click-left="router.back()" />

    <div class="scan-area">
      <!-- 扫码区域 -->
      <div v-show="scanning" class="scanner-wrapper">
        <div id="qr-reader" class="qr-reader"></div>
        <p class="scan-tip">请将预约二维码对准扫描框</p>
      </div>

      <!-- 核销成功结果 -->
      <div v-if="result" class="result-section">
        <van-icon name="checked" size="64" color="#07c160" />
        <h3 class="result-title">核销成功</h3>

        <van-cell-group inset class="result-detail">
          <van-cell title="预约编号" :value="result.reservation_no || '-'" />
          <van-cell title="会员" :value="result.member_nickname || result.member_name || '-'" />
          <van-cell title="场馆" :value="result.venue_name || '-'" />
          <van-cell title="日期" :value="result.booking_date || '-'" />
          <van-cell title="时段" :value="result.start_time && result.end_time ? `${result.start_time} ~ ${result.end_time}` : '-'" />
        </van-cell-group>

        <div class="continue-btn">
          <van-button type="primary" block round size="large" @click="handleContinue">
            继续扫码
          </van-button>
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="error && !scanning" class="error-section">
        <van-icon name="warning-o" size="64" color="#ee0a24" />
        <h3 class="error-title">核销失败</h3>
        <p class="error-msg">{{ error }}</p>
        <div class="continue-btn">
          <van-button type="primary" block round size="large" @click="handleContinue">
            重新扫码
          </van-button>
        </div>
      </div>

      <!-- 初始状态（非扫描，无结果，无错误） -->
      <div v-if="!scanning && !result && !error" class="start-section">
        <van-button type="primary" block round size="large" icon="scan" @click="startScan">
          开始扫码
        </van-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scan-area {
  padding: 16px;
}

.scanner-wrapper {
  text-align: center;
}

.qr-reader {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  border-radius: 12px;
  overflow: hidden;
}

.scan-tip {
  margin-top: 16px;
  color: #999;
  font-size: 14px;
}

.result-section,
.error-section,
.start-section {
  text-align: center;
  padding-top: 40px;
}

.result-title,
.error-title {
  margin: 12px 0 16px;
}

.result-title {
  color: #07c160;
}

.error-title {
  color: #ee0a24;
}

.error-msg {
  color: #666;
  font-size: 14px;
  margin-bottom: 24px;
}

.result-detail {
  margin-top: 20px;
  text-align: left;
}

.continue-btn {
  padding: 24px 0;
}
</style>
