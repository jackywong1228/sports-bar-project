<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode'

/**
 * 微信付款码扫码组件
 * 两条输入通道：
 *  1. 摄像头扫码（html5-qrcode，Code128 条形码）
 *  2. 手动/蓝牙扫码枪输入（扫码枪=键盘输入+回车）
 * 识别到合法的 18 位数字付款码（10-15 开头）后 emit('scan', code)
 */

const emit = defineEmits<{ (e: 'scan', code: string): void }>()

/** 微信付款码：18 位数字，10-15 开头 */
const PAY_CODE_RE = /^1[0-5]\d{16}$/

const activeTab = ref<'camera' | 'manual'>('camera')
const emitted = ref(false) // 防止一次扫码重复上报

// ── 摄像头扫码 ──
const cameraStarted = ref(false)
const cameraStarting = ref(false)
const cameraError = ref('')
let scanner: Html5Qrcode | null = null

const startCamera = async () => {
  if (cameraStarting.value || cameraStarted.value) return
  cameraError.value = ''
  cameraStarting.value = true
  try {
    scanner = new Html5Qrcode('pay-code-reader', {
      formatsToSupport: [Html5QrcodeSupportedFormats.CODE_128],
      verbose: false
    })
    await scanner.start(
      { facingMode: 'environment' },
      { fps: 10, qrbox: { width: 320, height: 140 } },
      onDecode,
      () => { /* 持续解码中，忽略单帧失败 */ }
    )
    cameraStarted.value = true
  } catch (e: any) {
    scanner = null
    const name = e?.name || ''
    if (name === 'NotAllowedError') {
      cameraError.value = '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头，或切换到手动输入'
    } else if (name === 'NotFoundError') {
      cameraError.value = '未检测到摄像头设备，请切换到手动输入'
    } else if (!window.isSecureContext) {
      cameraError.value = '摄像头需要 HTTPS 安全环境，请切换到手动输入'
    } else {
      cameraError.value = '摄像头打开失败，可切换到手动输入'
    }
  } finally {
    cameraStarting.value = false
  }
}

const stopCamera = async () => {
  if (scanner) {
    try {
      if (cameraStarted.value) await scanner.stop()
      scanner.clear()
    } catch (_e) { /* 忽略 */ }
    scanner = null
  }
  cameraStarted.value = false
}

const onDecode = async (text: string) => {
  const code = (text || '').trim()
  if (!PAY_CODE_RE.test(code)) return // 继续扫，直到识别到合法付款码
  if (emitted.value) return
  emitted.value = true
  await stopCamera()
  emit('scan', code)
}

// ── 手动 / 扫码枪输入 ──
const manualCode = ref('')
const manualError = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

const focusInput = () => {
  nextTick(() => inputRef.value?.focus())
}

const submitManual = () => {
  const code = manualCode.value.trim()
  if (!PAY_CODE_RE.test(code)) {
    manualError.value = '请输入 18 位数字付款码（10-15 开头）'
    return
  }
  if (emitted.value) return
  emitted.value = true
  emit('scan', code)
}

const onManualInput = () => {
  manualError.value = ''
  // 扫码枪连续输入，满 18 位且合法时自动提交（不等回车）
  if (PAY_CODE_RE.test(manualCode.value.trim())) submitManual()
}

const onManualEnter = () => {
  submitManual()
}

const switchTab = async (tab: 'camera' | 'manual') => {
  if (activeTab.value === tab) return
  activeTab.value = tab
  if (tab === 'manual') {
    await stopCamera()
    focusInput()
  }
}

onMounted(() => {
  if (activeTab.value === 'manual') focusInput()
})

onBeforeUnmount(() => {
  stopCamera()
})

defineExpose({ stopCamera })
</script>

<template>
  <div class="pay-code-scanner">
    <!-- 模式切换 -->
    <div class="mode-tabs">
      <div
        class="mode-tab"
        :class="{ active: activeTab === 'camera' }"
        @click="switchTab('camera')"
      >
        <van-icon name="photograph" size="16" />
        摄像头扫码
      </div>
      <div
        class="mode-tab"
        :class="{ active: activeTab === 'manual' }"
        @click="switchTab('manual')"
      >
        <van-icon name="keyboard" size="16" />
        扫码枪/手输
      </div>
    </div>

    <!-- 摄像头模式 -->
    <div v-show="activeTab === 'camera'" class="camera-pane">
      <!-- reader 容器始终存在于 DOM，供 html5-qrcode 挂载；未启动时用 idle 遮罩盖住 -->
      <div class="reader-wrap">
        <div id="pay-code-reader" class="reader" />
        <div v-if="cameraStarted" class="aim-line" />
        <div v-if="!cameraStarted" class="camera-idle">
          <van-icon name="scan" size="48" color="#1989fa" />
          <div class="camera-tip">请顾客打开微信「收付款」出示付款码</div>
          <van-button
            type="primary"
            round
            size="large"
            :loading="cameraStarting"
            loading-text="正在打开摄像头…"
            @click="startCamera"
          >打开摄像头扫码</van-button>
          <div v-if="cameraError" class="camera-error">{{ cameraError }}</div>
        </div>
      </div>
      <div v-if="cameraStarted" class="camera-tip">对准付款码条形码（18 位数字），识别后自动收款</div>
    </div>

    <!-- 手动 / 扫码枪模式 -->
    <div v-show="activeTab === 'manual'" class="manual-pane">
      <div class="manual-tip">扫码枪扫描付款码，或手动输入 18 位数字后回车</div>
      <input
        ref="inputRef"
        v-model="manualCode"
        class="manual-input"
        type="text"
        inputmode="numeric"
        pattern="[0-9]*"
        maxlength="18"
        placeholder="付款码（18 位数字）"
        autocomplete="off"
        @input="onManualInput"
        @keydown.enter.prevent="onManualEnter"
      />
      <div v-if="manualError" class="manual-error">{{ manualError }}</div>
      <van-button
        type="primary"
        round
        block
        size="large"
        :disabled="manualCode.trim().length !== 18"
        @click="submitManual"
      >确认收款码</van-button>
    </div>
  </div>
</template>

<style scoped>
.pay-code-scanner {
  padding: 12px 16px;
}

.mode-tabs {
  display: flex;
  background: #f2f3f5;
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 16px;
}

.mode-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 9px 0;
  font-size: 14px;
  color: #666;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
}

.mode-tab.active {
  background: #fff;
  color: var(--van-primary-color);
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

/* ── 摄像头 ── */
.reader-wrap {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
  min-height: 240px;
}

.reader {
  width: 100%;
}

.camera-idle {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  background: #fafafa;
  padding: 16px;
}

.camera-tip {
  font-size: 13px;
  color: #888;
  text-align: center;
  margin-top: 10px;
}

.camera-idle .camera-tip {
  margin-top: 0;
}

.camera-error {
  font-size: 13px;
  color: #ee0a24;
  text-align: center;
  line-height: 1.5;
  padding: 0 8px;
}

.aim-line {
  position: absolute;
  left: 8%;
  right: 8%;
  top: 50%;
  height: 2px;
  background: rgba(25, 137, 250, 0.9);
  box-shadow: 0 0 8px rgba(25, 137, 250, 0.8);
  pointer-events: none;
}

/* ── 手动输入 ── */
.manual-pane {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.manual-tip {
  font-size: 13px;
  color: #888;
  text-align: center;
}

.manual-input {
  width: 100%;
  box-sizing: border-box;
  border: 1.5px solid #dcdee0;
  border-radius: 10px;
  padding: 13px 14px;
  font-size: 20px;
  letter-spacing: 2px;
  text-align: center;
  outline: none;
  color: #333;
  background: #fff;
}

.manual-input:focus {
  border-color: var(--van-primary-color);
}

.manual-error {
  font-size: 13px;
  color: #ee0a24;
  text-align: center;
}
</style>
