<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getMemberDetail, rechargeCoin, rechargePoint } from '@/api/member'

const route = useRoute()
const router = useRouter()

const member = ref<any>({})
const loading = ref(true)

const levelColors: Record<string, string> = {
  S: '#999999',
  SS: '#C9A962',
  SSS: '#8B7355'
}

// 充值弹窗
const showRecharge = ref(false)
const rechargeType = ref<'coin' | 'point'>('coin')
const rechargeForm = ref({ amount: '', remark: '' })

const fetchDetail = async () => {
  loading.value = true
  try {
    const id = Number(route.params.id)
    const res = await getMemberDetail(id)
    member.value = res.data
  } finally {
    loading.value = false
  }
}

const openRecharge = (type: 'coin' | 'point') => {
  rechargeType.value = type
  rechargeForm.value = { amount: '', remark: '' }
  showRecharge.value = true
}

const handleRecharge = async () => {
  const amount = Number(rechargeForm.value.amount)
  if (!amount || amount === 0) {
    showToast('请输入有效数量')
    return
  }

  try {
    const data = {
      member_id: member.value.id,
      amount,
      remark: rechargeForm.value.remark || undefined
    }
    if (rechargeType.value === 'coin') {
      await rechargeCoin(data)
    } else {
      await rechargePoint(data)
    }
    showToast({ message: '操作成功', type: 'success' })
    showRecharge.value = false
    fetchDetail()
  } catch (_e) {
    // 错误已在拦截器中处理
  }
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="会员详情" left-arrow @click-left="router.back()" />

    <div v-if="loading" style="padding: 40px; text-align: center;">
      <van-loading size="36" />
    </div>

    <template v-else>
      <!-- 会员头部 -->
      <div class="member-header" :style="{ backgroundColor: levelColors[member.level_code] || '#999' }">
        <van-image
          :src="member.avatar || ''"
          width="64"
          height="64"
          round
          fit="cover"
          class="member-avatar"
        >
          <template #error>
            <van-icon name="user-o" size="36" color="#fff" />
          </template>
        </van-image>
        <div class="member-name">{{ member.nickname || member.phone || '-' }}</div>
        <van-tag v-if="member.level_code" plain color="#fff" text-color="#fff" size="large">
          {{ member.level_code }}级会员
        </van-tag>
      </div>

      <!-- 资产信息 -->
      <van-cell-group inset class="info-group">
        <van-grid :column-num="2" :border="false">
          <van-grid-item @click="openRecharge('coin')">
            <div class="asset-value">{{ member.coin_balance || 0 }}</div>
            <div class="asset-label">金币余额 <van-icon name="edit" /></div>
          </van-grid-item>
          <van-grid-item @click="openRecharge('point')">
            <div class="asset-value">{{ member.points || 0 }}</div>
            <div class="asset-label">积分 <van-icon name="edit" /></div>
          </van-grid-item>
        </van-grid>
      </van-cell-group>

      <!-- 基本信息 -->
      <van-cell-group inset title="基本信息" class="info-group">
        <van-cell title="手机号" :value="member.phone || '-'" />
        <van-cell title="性别" :value="member.gender === 1 ? '男' : member.gender === 2 ? '女' : '-'" />
        <van-cell title="注册时间" :value="member.created_at || '-'" />
        <van-cell title="订阅状态" :value="member.subscription_status === 'active' ? '有效' : '未订阅'" />
        <van-cell title="到期时间" :value="member.member_expire_time || '-'" />
      </van-cell-group>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <van-button type="primary" plain round block @click="openRecharge('coin')">
          金币充值
        </van-button>
        <van-button type="warning" plain round block @click="openRecharge('point')" style="margin-top: 10px;">
          积分充值
        </van-button>
      </div>
    </template>

    <!-- 充值弹窗 -->
    <van-popup v-model:show="showRecharge" round position="bottom" :style="{ padding: '16px' }">
      <h3 style="text-align: center; margin: 0 0 16px;">
        {{ rechargeType === 'coin' ? '金币充值' : '积分充值' }}
      </h3>
      <van-field
        v-model="rechargeForm.amount"
        type="number"
        :label="rechargeType === 'coin' ? '金币数量' : '积分数量'"
        :placeholder="`请输入${rechargeType === 'coin' ? '金币' : '积分'}数量（正数增加，负数减少）`"
      />
      <van-field
        v-model="rechargeForm.remark"
        label="备注"
        placeholder="请输入备注（选填）"
      />
      <div style="padding: 16px 0;">
        <van-button type="primary" block round @click="handleRecharge">确认</van-button>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.member-header {
  padding: 30px 16px;
  text-align: center;
  color: #fff;
}

.member-avatar {
  margin-bottom: 10px;
}

.member-name {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 8px;
}

.info-group {
  margin-top: 12px;
}

.asset-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--staff-primary);
  text-align: center;
}

.asset-label {
  font-size: 12px;
  color: #999;
  text-align: center;
  margin-top: 4px;
}

.action-buttons {
  padding: 20px 16px;
}
</style>
