<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { getMemberList } from '@/api/member'

const router = useRouter()

const keyword = ref('')
const loading = ref(false)
const finished = ref(false)
const list = ref<any[]>([])
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const searched = ref(false)

const levelColors: Record<string, string> = {
  S: '#999999',
  SS: '#C9A962',
  SSS: '#8B7355'
}

const onSearch = () => {
  list.value = []
  pagination.page = 1
  searched.value = true
  fetchList()
}

const fetchList = async (isLoadMore = false) => {
  if (!isLoadMore) {
    pagination.page = 1
    finished.value = false
  }
  loading.value = true
  try {
    const res = await getMemberList({
      keyword: keyword.value,
      page: pagination.page,
      page_size: pagination.pageSize
    })
    const data = res.data.list || res.data.items || []
    if (isLoadMore) {
      list.value.push(...data)
    } else {
      list.value = data
    }
    pagination.total = res.data.total || 0
    if (list.value.length >= pagination.total) {
      finished.value = true
    }
  } finally {
    loading.value = false
  }
}

const onLoadMore = () => {
  pagination.page++
  fetchList(true)
}

const goDetail = (id: number) => {
  router.push(`/member/${id}`)
}
</script>

<template>
  <div class="page-container">
    <van-nav-bar title="会员查询" left-arrow @click-left="router.back()" />

    <van-search
      v-model="keyword"
      placeholder="搜索手机号/昵称"
      show-action
      @search="onSearch"
    >
      <template #action>
        <div @click="onSearch">搜索</div>
      </template>
    </van-search>

    <van-list
      v-model:loading="loading"
      :finished="finished"
      :finished-text="searched ? '没有更多了' : ''"
      @load="onLoadMore"
    >
      <van-cell
        v-for="item in list"
        :key="item.id"
        is-link
        @click="goDetail(item.id)"
      >
        <template #title>
          <div class="member-item">
            <van-image
              :src="item.avatar || ''"
              width="40"
              height="40"
              round
              fit="cover"
            >
              <template #error>
                <van-icon name="user-o" size="24" color="#ddd" />
              </template>
            </van-image>
            <div class="member-info">
              <div class="member-name">
                {{ item.nickname || item.phone || '-' }}
                <van-tag
                  v-if="item.level_code"
                  :color="levelColors[item.level_code] || '#999'"
                  size="medium"
                  style="margin-left: 6px;"
                >{{ item.level_code }}</van-tag>
              </div>
              <div class="member-phone">{{ item.phone || '-' }}</div>
            </div>
          </div>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="searched && !loading && list.length === 0" description="未找到会员" />
  </div>
</template>

<style scoped>
.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.member-info {
  flex: 1;
}

.member-name {
  font-size: 15px;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.member-phone {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
}
</style>
