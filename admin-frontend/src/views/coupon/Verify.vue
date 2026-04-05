<template>
  <div class="page-container">
    <el-card class="search-card">
      <template #header>
        <span>扫码核销优惠券</span>
      </template>
      <el-form :inline="true" @submit.prevent="handleVerify">
        <el-form-item label="券号">
          <el-input
            ref="inputRef"
            v-model="couponInput"
            placeholder="扫码或输入券号（如 COUPON_VERIFY:42 或 42）"
            clearable
            style="width: 400px"
            @keyup.enter="handleVerify"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleVerify">核销</el-button>
        </el-form-item>
      </el-form>
      <div style="color: #909399; font-size: 13px; margin-top: 8px;">
        提示：使用扫码枪扫描会员优惠券二维码，或手动输入券号后点击核销
      </div>
    </el-card>

    <el-card v-if="result" class="result-card" style="margin-top: 16px;">
      <template #header>
        <div style="display: flex; align-items: center; gap: 8px;">
          <el-icon color="#67C23A" :size="20"><CircleCheckFilled /></el-icon>
          <span>核销成功</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="券ID">{{ result.coupon_id }}</el-descriptions-item>
        <el-descriptions-item label="券名称">{{ result.coupon_name }}</el-descriptions-item>
        <el-descriptions-item label="券类型">
          <el-tag>{{ typeMap[result.coupon_type] || result.coupon_type }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会员昵称">{{ result.member_nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="会员手机">{{ result.member_phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="核销时间">{{ result.verified_at }}</el-descriptions-item>
        <el-descriptions-item label="核销人">{{ result.verified_by }}</el-descriptions-item>
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
import { ref, nextTick, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { verifyCoupon } from '@/api/coupon'

const couponInput = ref('')
const loading = ref(false)
const result = ref<any>(null)
const errorMsg = ref('')
const inputRef = ref()

const typeMap: Record<string, string> = {
  cash: '代金券',
  discount: '折扣券',
  gift: '赠品券',
  hour_free: '时长券',
  experience: '体验券'
}

function parseCouponId(input: string): number | null {
  const trimmed = input.trim()
  if (!trimmed) return null
  // 支持 COUPON_VERIFY:42 格式
  const prefix = 'COUPON_VERIFY:'
  if (trimmed.startsWith(prefix)) {
    const id = parseInt(trimmed.substring(prefix.length), 10)
    return isNaN(id) ? null : id
  }
  // 支持纯数字
  const id = parseInt(trimmed, 10)
  return isNaN(id) ? null : id
}

async function handleVerify() {
  const couponId = parseCouponId(couponInput.value)
  if (couponId === null) {
    ElMessage.warning('请输入有效的券号')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确认核销券号 ${couponId} ？核销后不可撤销。`,
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
    const res = await verifyCoupon({ coupon_id: couponId })
    if (res.data?.code === 200 || res.data?.code === 0) {
      result.value = res.data.data
      ElMessage.success('核销成功')
      couponInput.value = ''
    } else {
      errorMsg.value = res.data?.message || '核销失败'
    }
  } catch (err: any) {
    const detail = err.response?.data?.detail || err.response?.data?.message || '核销失败'
    errorMsg.value = detail
  } finally {
    loading.value = false
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
}

onMounted(() => {
  inputRef.value?.focus()
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
</style>
