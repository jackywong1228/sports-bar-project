<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { Html5Qrcode } from 'html5-qrcode'
import { verifyReservationByNo } from '@/api/reservation'
import { staffScanMember, staffLookupMember, staffVerifyWithCheckin } from '@/api/staff'

interface MemberInfo {
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

interface TodayReservation {
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
}

interface MemberScanResult {
  member: MemberInfo
  today_reservations: TodayReservation[]
}

const router = useRouter()

const scanning = ref(false)
const result = ref<any>(null)
const error = ref('')
const memberResult = ref<MemberScanResult | null>(null)
const verifyingId = ref<number | null>(null)
const phoneInput = ref('')
const phoneLoading = ref(false)
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

// 会员识别结果（扫码 MEMBER: / 手机号查询共用）
const applyMemberResult = (data: MemberScanResult) => {
  memberResult.value = data
  error.value = ''
}

const loadMemberByToken = async (token: string) => {
  try {
    const res = await staffScanMember({ token })
    applyMemberResult(res.data as unknown as MemberScanResult)
  } catch (e: any) {
    error.value = e.response?.data?.detail || e.message || '会员识别失败'
  }
}

const onScanSuccess = async (decodedText: string) => {
  await stopScan()

  const content = (decodedText || '').trim()

  // 会员动态二维码：MEMBER:{短码或token} → 会员卡片 + 今日待核销预约
  if (content.startsWith('MEMBER:')) {
    const token = content.substring(7).trim()
    if (!token) {
      error.value = '无效的会员二维码'
      return
    }
    await loadMemberByToken(token)
    return
  }

  // 预约二维码：VERIFY:{reservation_no}
  let reservationNo = content
  if (content.startsWith('VERIFY:')) {
    reservationNo = content.substring(7)
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

// 手机号快捷核销入口
const handlePhoneLookup = async () => {
  const phone = phoneInput.value.trim()
  if (!/^\d{11}$/.test(phone)) {
    showToast('请输入 11 位手机号')
    return
  }
  phoneLoading.value = true
  try {
    const res = await staffLookupMember(phone)
    applyMemberResult(res.data as unknown as MemberScanResult)
    phoneInput.value = ''
  } catch (_e) {
    // 拦截器已 toast 具体原因（如「该手机号未注册会员」）
  } finally {
    phoneLoading.value = false
  }
}

// 会员卡片内单条预约核销
const handleVerifyItem = async (item: TodayReservation) => {
  try {
    await showConfirmDialog({
      title: '确认核销',
      message: `确认核销「${item.venue_name} ${item.start_time}~${item.end_time}」？核销后将同步打卡。`,
    })
  } catch {
    return
  }

  verifyingId.value = item.id
  try {
    const res = await staffVerifyWithCheckin(item.id)
    const points = (res.data as any)?.points_earned || 0
    showToast({ message: points > 0 ? `核销成功 +${points} 积分` : '核销成功', type: 'success' })
    if (memberResult.value) {
      memberResult.value.today_reservations = memberResult.value.today_reservations.filter(
        (r) => r.id !== item.id
      )
    }
  } catch (_e) {
    // 拦截器已 toast 具体原因
  } finally {
    verifyingId.value = null
  }
}

const payTypeText = (payType: string) => {
  if (payType === 'coin') return '金币'
  if (payType === 'wechat') return '微信'
  if (payType === 'free') return '免费'
  return payType || '-'
}

const closeMemberResult = () => {
  memberResult.value = null
}

const handleContinue = () => {
  result.value = null
  memberResult.value = null
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
        <p class="scan-tip">请将预约二维码或会员码对准扫描框</p>
      </div>

      <!-- 会员识别结果（MEMBER: 扫码 / 手机号查询） -->
      <div v-if="memberResult" class="member-section">
        <van-cell-group inset class="member-card">
          <van-cell>
            <template #title>
              <div class="member-header">
                <van-image
                  v-if="memberResult.member.avatar"
                  :src="memberResult.member.avatar"
                  round
                  width="44"
                  height="44"
                  fit="cover"
                />
                <div v-else class="avatar-placeholder">
                  {{ (memberResult.member.nickname || '会').charAt(0) }}
                </div>
                <div class="member-info">
                  <div class="member-name">
                    {{ memberResult.member.nickname || '未命名会员' }}
                    <van-tag
                      :color="memberResult.member.theme_color || '#999'"
                      class="level-tag"
                    >
                      {{ memberResult.member.level_name }}
                    </van-tag>
                  </div>
                  <div class="member-sub">
                    {{ memberResult.member.phone || '-' }}
                    <span v-if="memberResult.member.expire_time">
                      · 会员到期 {{ memberResult.member.expire_time }}
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </van-cell>
        </van-cell-group>

        <template v-if="memberResult.today_reservations.length > 0">
          <p class="section-title">今日待核销预约（{{ memberResult.today_reservations.length }}）</p>
          <van-cell-group
            v-for="r in memberResult.today_reservations"
            :key="r.id"
            inset
            class="reservation-card"
          >
            <van-cell :title="r.venue_name" :label="`${r.start_time} - ${r.end_time}（${r.duration}分钟）${r.coach_name ? ' · 教练：' + r.coach_name : ''}`">
              <template #value>
                <van-button
                  type="success"
                  size="small"
                  :loading="verifyingId === r.id"
                  @click="handleVerifyItem(r)"
                >
                  核销
                </van-button>
              </template>
            </van-cell>
            <van-cell title="费用" :value="`¥${r.total_price}（${payTypeText(r.pay_type)}）`" />
          </van-cell-group>
        </template>
        <van-empty v-else description="该会员今日无可核销预约" image-size="80" />

        <div class="continue-btn">
          <van-button type="primary" block round size="large" @click="handleContinue">
            继续扫码
          </van-button>
          <van-button block round size="large" class="close-btn" @click="closeMemberResult">
            关闭
          </van-button>
        </div>
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
        <h3 class="error-title">操作失败</h3>
        <p class="error-msg">{{ error }}</p>
        <div class="continue-btn">
          <van-button type="primary" block round size="large" @click="handleContinue">
            重新扫码
          </van-button>
        </div>
      </div>

      <!-- 初始状态（非扫描，无结果，无错误，无会员卡片） -->
      <div v-if="!scanning && !result && !error && !memberResult" class="start-section">
        <van-button type="primary" block round size="large" icon="scan" @click="startScan">
          开始扫码
        </van-button>
      </div>

      <!-- 手机号快捷核销入口 -->
      <div v-if="!memberResult && !result" class="phone-section">
        <van-cell-group inset>
          <van-field
            v-model="phoneInput"
            type="tel"
            maxlength="11"
            label="手机号"
            placeholder="输入会员手机号核销"
            clearable
            @keyup.enter="handlePhoneLookup"
          />
        </van-cell-group>
        <van-button
          type="primary"
          block
          round
          class="phone-btn"
          :loading="phoneLoading"
          :disabled="phoneInput.trim().length !== 11"
          @click="handlePhoneLookup"
        >
          查询并核销
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

/* 会员卡片 */
.member-section {
  padding-top: 8px;
}

.member-card {
  margin-bottom: 12px;
}

.member-header {
  display: flex;
  align-items: center;
}

.avatar-placeholder {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #1A5D3A;
  color: #fff;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.member-info {
  margin-left: 12px;
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
}

.level-tag {
  margin-left: 8px;
}

.member-sub {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.section-title {
  margin: 16px 16px 8px;
  font-size: 14px;
  color: #666;
}

.reservation-card {
  margin-bottom: 8px;
}

.close-btn {
  margin-top: 12px;
}

/* 手机号核销入口 */
.phone-section {
  margin-top: 32px;
}

.phone-btn {
  margin-top: 16px;
}
</style>
