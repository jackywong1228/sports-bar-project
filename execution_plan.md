# 会员制度改造执行计划

> 版本：1.0
> 日期：2026-01-28
> 作者：superpowers 规划师

---

## 一、总体进度

### 已完成任务
- [x] **Phase 1**: 架构设计 (task_plan.md)
- [x] **Phase 2**: 后端数据模型和 API 实现
  - 会员等级模型扩展
  - 预约/违约/发券模型
  - 5 个新 API 接口
  - 预约权限检查服务
  - 餐食折扣服务
  - 数据库迁移脚本

### 待完成任务
- [ ] **Phase 3**: 小程序开发 (预计 5 天)
- [ ] **Phase 4**: 管理后台改造 (预计 3 天)
- [ ] **Phase 5**: 测试验证 (预计 2 天)
- [ ] **Phase 6**: 文档更新 (预计 0.5 天)

---

## 二、UI 主题方案设计 (Brainstorm)

### 2.1 会员等级主题色定义

| 等级代码 | 等级名称 | 主题色 | 渐变色 | 应用场景 |
|---------|---------|--------|--------|---------|
| TRIAL | 体验会员 | `#999999` | `linear-gradient(135deg, #999999, #666666)` | 灰色调，强调"试用"感 |
| S | 初级会员 | `#4A90E2` | `linear-gradient(135deg, #4A90E2, #357ABD)` | 蓝色调，稳重可靠 |
| SS | 中级会员 | `#9B59B6` | `linear-gradient(135deg, #9B59B6, #8E44AD)` | 紫色调，高端进阶 |
| SSS | VIP会员 | `#F39C12` | `linear-gradient(135deg, #F39C12, #E67E22)` | 金色调，尊贵荣耀 |

### 2.2 需要应用主题色的页面

| 优先级 | 页面 | 应用位置 | 说明 |
|-------|------|---------|------|
| P0 | 我的页面 (profile) | 头部区域、会员卡片 | 最重要，用户首先感知 |
| P0 | 场馆预约 (venue-booking) | 权限提示、预约按钮 | 核心功能入口 |
| P1 | 首页 (index) | 用户头像边框、会员标签 | 品牌露出 |
| P1 | 会员中心 (member) | 等级卡片、权益展示 | 订阅购买入口 |
| P2 | 点餐页面 (food) | 折扣标签 | 权益体现 |
| P2 | 订单页面 (orders) | 会员标识 | 辅助展示 |

### 2.3 主题切换实现方案

**方案选择：CSS 变量 + JS 动态设置**

```css
/* app.wxss 新增 */
page {
  /* 会员等级主题色变量 */
  --member-theme-color: #999999;
  --member-theme-gradient: linear-gradient(135deg, #999999, #666666);
  --member-theme-light: rgba(153, 153, 153, 0.1);
}
```

```javascript
// 在 app.js 登录后调用
setMemberTheme(levelCode) {
  const themes = {
    'TRIAL': { color: '#999999', gradient: 'linear-gradient(135deg, #999999, #666666)' },
    'S': { color: '#4A90E2', gradient: 'linear-gradient(135deg, #4A90E2, #357ABD)' },
    'SS': { color: '#9B59B6', gradient: 'linear-gradient(135deg, #9B59B6, #8E44AD)' },
    'SSS': { color: '#F39C12', gradient: 'linear-gradient(135deg, #F39C12, #E67E22)' }
  }
  this.globalData.memberTheme = themes[levelCode] || themes['TRIAL']
}
```

### 2.4 会员卡片组件设计

```
+------------------------------------------+
|  [头像]   用户昵称                  SSS   |
|           ID: 12345               VIP会员 |
+------------------------------------------+
|  本月剩余预约: 4次    |    可预约范围: 30天 |
+------------------------------------------+
|  [渐变背景 + 等级主题色]                  |
+------------------------------------------+
```

---

## 三、小程序改造执行计划 (Write-Plan)

### 3.1 文件改动清单

#### 3.1.1 需要修改的文件 (共 14 个)

| 序号 | 文件路径 | 改动类型 | 预计耗时 |
|-----|---------|---------|---------|
| 1 | `app.js` | 修改 | 2h |
| 2 | `app.wxss` | 修改 | 1h |
| 3 | `utils/api.js` | 修改 | 1h |
| 4 | `pages/profile/profile.js` | 修改 | 3h |
| 5 | `pages/profile/profile.wxml` | 修改 | 2h |
| 6 | `pages/profile/profile.wxss` | 修改 | 2h |
| 7 | `pages/venue-booking/venue-booking.js` | 修改 | 4h |
| 8 | `pages/venue-booking/venue-booking.wxml` | 修改 | 2h |
| 9 | `pages/venue-booking/venue-booking.wxss` | 修改 | 1h |
| 10 | `pages/food/food.js` | 修改 | 2h |
| 11 | `pages/food/food.wxml` | 修改 | 1h |
| 12 | `pages/food-order/food-order.js` | 修改 | 2h |
| 13 | `pages/food-order/food-order.wxml` | 修改 | 1h |
| 14 | `pages/member/member.js` | 修改 | 3h |
| 15 | `pages/member/member.wxml` | 修改 | 2h |

#### 3.1.2 需要新增的文件 (共 6 个)

| 序号 | 文件路径 | 功能说明 | 预计耗时 |
|-----|---------|---------|---------|
| 1 | `components/member-card/member-card.js` | 会员卡片组件 | 2h |
| 2 | `components/member-card/member-card.wxml` | 会员卡片模板 | 1h |
| 3 | `components/member-card/member-card.wxss` | 会员卡片样式 | 1h |
| 4 | `components/member-card/member-card.json` | 组件配置 | 0.5h |
| 5 | `components/booking-permission/booking-permission.js` | 预约权限提示组件 | 2h |
| 6 | `components/booking-permission/booking-permission.wxml` | 权限提示模板 | 1h |
| 7 | `components/booking-permission/booking-permission.wxss` | 权限提示样式 | 1h |
| 8 | `components/booking-permission/booking-permission.json` | 组件配置 | 0.5h |
| 9 | `pages/member-benefits/member-benefits.js` | 会员权益页面 | 3h |
| 10 | `pages/member-benefits/member-benefits.wxml` | 权益展示模板 | 2h |
| 11 | `pages/member-benefits/member-benefits.wxss` | 权益页面样式 | 1h |
| 12 | `pages/member-benefits/member-benefits.json` | 页面配置 | 0.5h |

### 3.2 详细改动说明

#### 3.2.1 app.js 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\app.js`

**改动点**:

1. **globalData 新增字段** (第 1-11 行后):
```javascript
globalData: {
  // ... 现有字段
  memberLevel: null,        // 会员等级信息对象
  memberTheme: {            // 当前主题配置
    color: '#999999',
    gradient: 'linear-gradient(135deg, #999999, #666666)'
  },
  canBook: false,           // 是否可预约
  bookingQuota: 0,          // 剩余预约次数
  bookingRangeDays: 0,      // 可预约天数范围
  isPenalized: false        // 是否处于惩罚期
}
```

2. **新增主题设置方法** (在 getMemberInfo 方法后):
```javascript
// 设置会员主题
setMemberTheme(levelCode) {
  const themes = {
    'TRIAL': { color: '#999999', gradient: 'linear-gradient(135deg, #999999, #666666)', light: 'rgba(153, 153, 153, 0.1)' },
    'S': { color: '#4A90E2', gradient: 'linear-gradient(135deg, #4A90E2, #357ABD)', light: 'rgba(74, 144, 226, 0.1)' },
    'SS': { color: '#9B59B6', gradient: 'linear-gradient(135deg, #9B59B6, #8E44AD)', light: 'rgba(155, 89, 182, 0.1)' },
    'SSS': { color: '#F39C12', gradient: 'linear-gradient(135deg, #F39C12, #E67E22)', light: 'rgba(243, 156, 18, 0.1)' }
  }
  this.globalData.memberTheme = themes[levelCode] || themes['TRIAL']
}
```

3. **修改 getMemberInfo 方法** (第 39-54 行):
```javascript
getMemberInfo() {
  const that = this
  wx.request({
    url: `${this.globalData.baseUrl}/member/profile`,
    method: 'GET',
    header: {
      'Authorization': `Bearer ${this.globalData.token}`
    },
    success(res) {
      if (res.data.code === 200) {
        const data = res.data.data
        that.globalData.memberInfo = data

        // 新增：设置会员等级相关信息
        if (data.level_info) {
          that.globalData.memberLevel = data.level_info
          that.setMemberTheme(data.level_info.level_code)
        }
        if (data.booking_privileges) {
          that.globalData.canBook = data.booking_privileges.can_book
          that.globalData.bookingQuota = data.booking_privileges.remaining_bookings
          that.globalData.bookingRangeDays = data.booking_privileges.booking_range_days
        }
        if (data.penalty_info) {
          that.globalData.isPenalized = data.penalty_info.is_penalized
        }
      }
    }
  })
}
```

#### 3.2.2 utils/api.js 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\utils\api.js`

**新增接口** (在文件末尾 module.exports 前):

```javascript
// ==================== 会员权限 ====================

/**
 * 检查预约权限
 * @param {number} venueTypeId 场馆类型ID
 * @param {string} date 预约日期 YYYY-MM-DD
 */
const checkBookingPermission = (venueTypeId, date) => {
  return get('/member/booking-permission', { venue_type_id: venueTypeId, date })
}

/**
 * 获取餐食折扣信息
 */
const getFoodDiscount = () => {
  return get('/member/food-discount')
}

/**
 * 获取违约记录
 */
const getViolations = () => {
  return get('/member/violations')
}

/**
 * 预约核销
 * @param {number} reservationId 预约ID
 * @param {string} verifyCode 核销码
 */
const verifyReservation = (reservationId, verifyCode) => {
  return post(`/member/reservations/${reservationId}/verify`, { verify_code: verifyCode })
}
```

**module.exports 新增**:
```javascript
// 会员权限
checkBookingPermission,
getFoodDiscount,
getViolations,
verifyReservation,
```

#### 3.2.3 pages/venue-booking/venue-booking.wxml 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\pages\venue-booking\venue-booking.wxml`

**改动点 1**: 移除价格显示 (第 40 行)
```xml
<!-- 删除或注释掉这行 -->
<!-- <text class="venue-price">¥{{item.price}}/时</text> -->
```

**改动点 2**: 移除底部价格汇总 (第 114-117 行)
```xml
<!-- 删除合计价格行 -->
<!-- <view class="summary-row">
  <text class="summary-label">合计：</text>
  <text class="summary-price">¥{{utils.getTotalPrice(selectedVenuePrice, selectedSlots)}}</text>
</view> -->
```

**改动点 3**: 新增权限提示 (在第 3 行类型选择后)
```xml
<!-- 会员预约权限提示 -->
<view class="permission-tip" wx:if="{{!canBook}}">
  <view class="tip-icon">!</view>
  <view class="tip-content">
    <text class="tip-title">{{permissionTip.title}}</text>
    <text class="tip-desc">{{permissionTip.desc}}</text>
  </view>
  <view class="tip-action" wx:if="{{memberLevel.level_code === 'TRIAL'}}" bindtap="contactService">
    咨询客服
  </view>
</view>

<!-- 剩余预约次数提示 -->
<view class="quota-tip" wx:if="{{canBook && bookingQuota > 0}}">
  <text>{{quotaPeriodDesc}}剩余 {{bookingQuota}} 次预约</text>
</view>
```

**改动点 4**: 修改日期选择逻辑，添加不可选标记 (第 18-29 行)
```xml
<scroll-view class="date-scroll" scroll-x enable-flex>
  <view
    class="date-item {{selectedDate === item.date ? 'active' : ''}} {{!item.canBook ? 'disabled' : ''}}"
    wx:for="{{dates}}"
    wx:key="date"
    bindtap="selectDate"
    data-date="{{item.date}}"
    data-can-book="{{item.canBook}}"
  >
    <text class="date-week">{{item.weekDay}}</text>
    <text class="date-day">{{item.day}}</text>
    <text class="date-lock" wx:if="{{!item.canBook}}">锁</text>
  </view>
</scroll-view>
```

#### 3.2.4 pages/venue-booking/venue-booking.js 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\pages\venue-booking\venue-booking.js`

**新增 data 字段**:
```javascript
data: {
  // ... 现有字段
  canBook: true,
  bookingQuota: 0,
  memberLevel: null,
  permissionTip: {
    title: '',
    desc: ''
  },
  quotaPeriodDesc: ''
}
```

**新增方法**:
```javascript
// 检查预约权限
async checkPermission() {
  const app = getApp()
  const { checkBookingPermission } = require('../../utils/api')

  if (!app.globalData.token) {
    this.setData({
      canBook: false,
      permissionTip: {
        title: '请先登录',
        desc: '登录后查看预约权限'
      }
    })
    return
  }

  try {
    const res = await checkBookingPermission(this.data.currentTypeId, this.data.selectedDate)
    if (res.code === 200) {
      const data = res.data
      this.setData({
        canBook: data.can_book,
        bookingQuota: data.remaining_quota || 0,
        permissionTip: {
          title: data.can_book ? '' : '无法预约',
          desc: data.reason || ''
        },
        quotaPeriodDesc: data.quota_period_desc || ''
      })

      // 更新可预约日期范围
      if (data.booking_range) {
        this.updateDateRange(data.booking_range.min_date, data.booking_range.max_date)
      }
    }
  } catch (e) {
    console.error('检查权限失败', e)
  }
},

// 更新日期范围的可预约状态
updateDateRange(minDate, maxDate) {
  const dates = this.data.dates.map(item => ({
    ...item,
    canBook: item.date >= minDate && item.date <= maxDate
  }))
  this.setData({ dates })
},

// 联系客服
contactService() {
  wx.makePhoneCall({
    phoneNumber: '400-xxx-xxxx'
  })
}
```

**修改 onLoad**:
```javascript
onLoad() {
  // 现有代码...

  // 新增：检查预约权限
  this.checkPermission()
}
```

**修改 selectDate**:
```javascript
selectDate(e) {
  const { date, canBook } = e.currentTarget.dataset

  // 新增：检查日期是否可预约
  if (!canBook) {
    wx.showToast({
      title: '该日期不在可预约范围内',
      icon: 'none'
    })
    return
  }

  // 原有代码...
}
```

#### 3.2.5 pages/profile/profile.wxml 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\pages\profile\profile.wxml`

**改动点 1**: 替换用户头部为会员卡片组件 (第 2-15 行)
```xml
<!-- 会员卡片组件 -->
<member-card
  wx:if="{{isLoggedIn && memberInfo}}"
  member-info="{{memberInfo}}"
  level-info="{{memberLevel}}"
  booking-privileges="{{bookingPrivileges}}"
  bind:tapCard="goToMemberCenter"
/>

<!-- 未登录状态保持不变 -->
<view class="user-header guest" wx:else bindtap="goToLogin">
  ...
</view>
```

**改动点 2**: 新增惩罚状态提示 (在教练入口前)
```xml
<!-- 惩罚状态提示 -->
<view class="penalty-warning" wx:if="{{isPenalized}}">
  <image class="warning-icon" src="/assets/icons/warning.png" />
  <view class="warning-content">
    <text class="warning-title">预约权限受限</text>
    <text class="warning-desc">{{penaltyReason}}</text>
  </view>
  <text class="warning-link" bindtap="viewViolations">查看详情</text>
</view>
```

#### 3.2.6 pages/food/food.wxml 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\pages\food\food.wxml`

**改动点**: 添加折扣标签和折扣价 (第 21-22 行)
```xml
<view class="food-bottom">
  <!-- 折扣标签 -->
  <view class="discount-tag" wx:if="{{discountInfo.discount_rate < 1}}">
    {{discountInfo.discount_desc}}
  </view>
  <!-- 原价和折扣价 -->
  <view class="price-wrapper">
    <text class="food-price" wx:if="{{discountInfo.discount_rate < 1}}">
      ¥{{item.price * discountInfo.discount_rate}}
    </text>
    <text class="food-price {{discountInfo.discount_rate < 1 ? 'original-price' : ''}}">
      ¥{{item.price}}
    </text>
  </view>
  <view class="add-btn" catchtap="addToCart" data-id="{{item.id}}">+</view>
</view>
```

#### 3.2.7 pages/food/food.js 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\pages\food\food.js`

**新增**:
```javascript
data: {
  // ... 现有字段
  discountInfo: {
    is_discount_time: false,
    discount_rate: 1.0,
    discount_desc: ''
  }
}

// 获取折扣信息
async loadDiscountInfo() {
  const { getFoodDiscount } = require('../../utils/api')
  try {
    const res = await getFoodDiscount()
    if (res.code === 200) {
      this.setData({
        discountInfo: res.data
      })
    }
  } catch (e) {
    console.error('获取折扣信息失败', e)
  }
}

// 在 onLoad 中调用
onLoad() {
  // ... 现有代码
  this.loadDiscountInfo()
}
```

#### 3.2.8 pages/member/member.wxml 改动

**文件路径**: `D:\sports-bar-project\user-miniprogram\pages\member\member.wxml`

**完全重构为订阅会员介绍页**:
```xml
<view class="container">
  <!-- 当前会员状态 -->
  <view class="current-status">
    <view class="status-card" style="background: {{memberTheme.gradient}}">
      <view class="status-level">{{memberInfo.level_name || '体验会员'}}</view>
      <view class="status-expire" wx:if="{{memberInfo.subscription_info}}">
        {{memberInfo.subscription_info.status === 'active' ? '有效期至：' + memberInfo.subscription_info.expire_date : '未订阅'}}
      </view>
    </view>
  </view>

  <!-- 等级权益对比 -->
  <view class="benefits-section">
    <view class="section-title">会员等级权益</view>
    <view class="benefits-table">
      <view class="table-header">
        <view class="th">权益</view>
        <view class="th" wx:for="{{levels}}" wx:key="level_code">{{item.name}}</view>
      </view>
      <view class="table-row">
        <view class="td label">预约范围</view>
        <view class="td">-</view>
        <view class="td">今明两天</view>
        <view class="td">本周</view>
        <view class="td">一个月</view>
      </view>
      <view class="table-row">
        <view class="td label">预约次数</view>
        <view class="td">-</view>
        <view class="td">2次/两天</view>
        <view class="td">3次/周</view>
        <view class="td">5次/月</view>
      </view>
      <view class="table-row">
        <view class="td label">高尔夫</view>
        <view class="td">-</view>
        <view class="td">-</view>
        <view class="td">-</view>
        <view class="td">可预约</view>
      </view>
      <view class="table-row">
        <view class="td label">餐食折扣</view>
        <view class="td">无</view>
        <view class="td">97折</view>
        <view class="td">95折</view>
        <view class="td">9折</view>
      </view>
      <view class="table-row">
        <view class="td label">每月咖啡券</view>
        <view class="td">0张</view>
        <view class="td">3张</view>
        <view class="td">5张</view>
        <view class="td">10张</view>
      </view>
    </view>
  </view>

  <!-- 订阅套餐 -->
  <view class="packages-section">
    <view class="section-title">选择订阅套餐</view>
    <view class="package-list">
      <view
        class="package-card {{item.level_code === 'SSS' ? 'vip' : ''}}"
        wx:for="{{packages}}"
        wx:key="id"
        bindtap="selectPackage"
        data-id="{{item.id}}"
      >
        <view class="package-badge" wx:if="{{item.is_recommended}}">推荐</view>
        <view class="package-name">{{item.name}}</view>
        <view class="package-price">
          <text class="symbol">¥</text>
          <text class="value">{{item.price}}</text>
          <text class="unit">/{{item.duration_days}}天</text>
        </view>
        <view class="package-benefits">{{item.benefits_summary}}</view>
        <button class="package-btn">立即订阅</button>
      </view>
    </view>
  </view>
</view>
```

### 3.3 新增组件详细设计

#### 3.3.1 会员卡片组件 (member-card)

**目录结构**:
```
user-miniprogram/components/member-card/
├── member-card.js
├── member-card.wxml
├── member-card.wxss
└── member-card.json
```

**member-card.js**:
```javascript
Component({
  properties: {
    memberInfo: {
      type: Object,
      value: {}
    },
    levelInfo: {
      type: Object,
      value: {}
    },
    bookingPrivileges: {
      type: Object,
      value: {}
    }
  },

  data: {
    themes: {
      'TRIAL': { color: '#999999', gradient: 'linear-gradient(135deg, #999999, #666666)' },
      'S': { color: '#4A90E2', gradient: 'linear-gradient(135deg, #4A90E2, #357ABD)' },
      'SS': { color: '#9B59B6', gradient: 'linear-gradient(135deg, #9B59B6, #8E44AD)' },
      'SSS': { color: '#F39C12', gradient: 'linear-gradient(135deg, #F39C12, #E67E22)' }
    }
  },

  computed: {
    currentTheme() {
      const levelCode = this.data.levelInfo.level_code || 'TRIAL'
      return this.data.themes[levelCode] || this.data.themes['TRIAL']
    }
  },

  methods: {
    onTapCard() {
      this.triggerEvent('tapCard')
    }
  }
})
```

**member-card.wxml**:
```xml
<view class="member-card" style="background: {{currentTheme.gradient}}" bindtap="onTapCard">
  <view class="card-header">
    <image class="avatar" src="{{memberInfo.avatar || '/assets/images/avatar-default.png'}}" mode="aspectFill" />
    <view class="info">
      <text class="nickname">{{memberInfo.nickname || '用户'}}</text>
      <text class="member-id">ID: {{memberInfo.id}}</text>
    </view>
    <view class="level-badge">
      <text class="level-code">{{levelInfo.level_code || 'TRIAL'}}</text>
      <text class="level-name">{{levelInfo.level_name || '体验会员'}}</text>
    </view>
  </view>

  <view class="card-divider"></view>

  <view class="card-footer">
    <view class="stat-item">
      <text class="stat-value">{{bookingPrivileges.remaining_bookings || 0}}</text>
      <text class="stat-label">剩余预约</text>
    </view>
    <view class="stat-item">
      <text class="stat-value">{{bookingPrivileges.booking_range_days || 0}}天</text>
      <text class="stat-label">可约范围</text>
    </view>
    <view class="stat-item" wx:if="{{levelInfo.level_code !== 'TRIAL'}}">
      <text class="stat-value">{{memberInfo.discount_info.food_discount_rate * 100}}%</text>
      <text class="stat-label">餐食折扣</text>
    </view>
  </view>
</view>
```

#### 3.3.2 预约权限提示组件 (booking-permission)

**booking-permission.wxml**:
```xml
<view class="permission-container {{canBook ? 'success' : 'warning'}}">
  <view class="icon">
    <image src="{{canBook ? '/assets/icons/check.png' : '/assets/icons/lock.png'}}" />
  </view>
  <view class="content">
    <text class="title">{{title}}</text>
    <text class="desc">{{desc}}</text>
  </view>
  <view class="action" wx:if="{{showAction}}" bindtap="onAction">
    <text>{{actionText}}</text>
  </view>
</view>
```

---

## 四、管理后台改造执行计划

### 4.1 文件改动清单

| 序号 | 文件路径 | 改动类型 | 说明 |
|-----|---------|---------|------|
| 1 | `views/member/Level.vue` | 重构 | 新增订阅相关配置字段 |
| 2 | `views/member/List.vue` | 修改 | 显示订阅状态、惩罚状态 |
| 3 | `views/reservation/List.vue` | 修改 | 新增核销状态、核销操作 |
| 4 | `views/venue/Type.vue` | 修改 | 新增"是否高尔夫"配置 |
| 5 | `views/Dashboard.vue` | 修改 | 新增会员等级分布图 |
| 6 | `views/member/Violation.vue` | **新增** | 违约管理页面 |
| 7 | `views/coupon/Issue.vue` | **新增** | 发券管理页面 |

### 4.2 详细改动说明

#### 4.2.1 views/member/Level.vue 重构

**新增字段配置**:

```vue
<el-form-item label="等级代码" prop="level_code">
  <el-select v-model="form.level_code" placeholder="请选择">
    <el-option label="TRIAL (体验会员)" value="TRIAL" />
    <el-option label="S (初级会员)" value="S" />
    <el-option label="SS (中级会员)" value="SS" />
    <el-option label="SSS (VIP会员)" value="SSS" />
  </el-select>
</el-form-item>

<el-form-item label="预约范围(天)">
  <el-input-number v-model="form.booking_range_days" :min="0" :max="30" />
</el-form-item>

<el-form-item label="预约上限">
  <el-input-number v-model="form.booking_max_count" :min="0" :max="10" />
</el-form-item>

<el-form-item label="预约周期">
  <el-select v-model="form.booking_period">
    <el-option label="每天" value="day" />
    <el-option label="每周" value="week" />
    <el-option label="每月" value="month" />
  </el-select>
</el-form-item>

<el-form-item label="餐食折扣率">
  <el-input-number v-model="form.food_discount_rate" :min="0.5" :max="1" :step="0.01" :precision="2" />
</el-form-item>

<el-form-item label="每月发券数">
  <el-input-number v-model="form.monthly_coupon_count" :min="0" :max="20" />
</el-form-item>

<el-form-item label="可预约高尔夫">
  <el-switch v-model="form.can_book_golf" />
</el-form-item>

<el-form-item label="主题颜色">
  <el-color-picker v-model="form.theme_color" />
</el-form-item>
```

#### 4.2.2 views/reservation/List.vue 改动

**新增核销状态筛选和操作**:

```vue
<!-- 筛选条件新增 -->
<el-form-item label="核销状态">
  <el-select v-model="queryParams.is_verified" placeholder="全部" clearable>
    <el-option label="已核销" :value="true" />
    <el-option label="未核销" :value="false" />
  </el-select>
</el-form-item>

<!-- 表格新增列 -->
<el-table-column prop="is_verified" label="核销状态" width="100">
  <template #default="{ row }">
    <el-tag :type="row.is_verified ? 'success' : 'warning'">
      {{ row.is_verified ? '已核销' : '未核销' }}
    </el-tag>
  </template>
</el-table-column>

<!-- 操作新增 -->
<el-button
  v-if="!row.is_verified && row.status === 1"
  type="success"
  link
  @click="handleVerify(row)"
>
  核销
</el-button>
```

#### 4.2.3 新增 views/member/Violation.vue

**页面功能**:
- 违约记录列表展示
- 按会员、日期范围筛选
- 手动应用/解除惩罚
- 违约统计图表

---

## 五、测试计划

### 5.1 预约权限测试

| 测试场景 | 测试步骤 | 预期结果 | 优先级 |
|---------|---------|---------|-------|
| TRIAL会员预约 | 使用体验会员账号尝试预约 | 显示"无法自行预约，请致电咨询" | P0 |
| S会员今日预约 | 使用S会员预约今天的场地 | 可以成功预约 | P0 |
| S会员后天预约 | 使用S会员预约后天的场地 | 显示"超出可预约范围" | P0 |
| S会员预约高尔夫 | 使用S会员预约高尔夫场地 | 显示"您的等级不支持预约高尔夫" | P0 |
| SS会员本周预约 | 使用SS会员预约本周日的场地 | 可以成功预约 | P0 |
| SS会员下周预约 | 使用SS会员预约下周的场地 | 显示"超出可预约范围" | P0 |
| SSS会员预约高尔夫 | 使用SSS会员预约高尔夫场地 | 可以成功预约 | P0 |
| S会员超额预约 | S会员已有2次预约，尝试第3次 | 显示"今明两天预约次数已达上限" | P0 |
| SS会员超额预约 | SS会员本周已有3次预约，尝试第4次 | 显示"本周预约次数已达上限" | P0 |
| SSS会员超额预约 | SSS会员本月已有5次预约，尝试第6次 | 显示"本月预约次数已达上限" | P0 |

### 5.2 违约惩罚测试

| 测试场景 | 测试步骤 | 预期结果 | 优先级 |
|---------|---------|---------|-------|
| S会员爽约 | S会员预约后不核销，等待预约时间过期 | 降级为只能预约当天，Max 1次 | P0 |
| SS会员爽约 | SS会员一周内预约不核销 | 降级为只能预约今明两天，Max 1次 | P0 |
| SSS会员三次爽约 | SSS会员一个月内3次预约不核销 | 降级为只能预约本周，Max 1次 | P0 |
| 惩罚状态显示 | 会员处于惩罚期登录小程序 | 显示惩罚提示和原因 | P1 |
| 管理员解除惩罚 | 管理员在后台解除会员惩罚 | 会员恢复正常预约权限 | P1 |

### 5.3 餐食折扣测试

| 测试场景 | 测试步骤 | 预期结果 | 优先级 |
|---------|---------|---------|-------|
| TRIAL会员白天点餐 | 8:00-18:00期间下单 | 原价，无折扣 | P0 |
| S会员白天点餐 | 8:00-18:00期间下单 | 显示97折价格 | P0 |
| SS会员白天点餐 | 8:00-18:00期间下单 | 显示95折价格 | P0 |
| SSS会员白天点餐 | 8:00-18:00期间下单 | 显示9折价格 | P0 |
| SSS会员晚间点餐 | 18:00后下单 | 原价，显示"晚间时段不参与折扣" | P0 |
| 折扣标签显示 | 任意会员查看菜单 | 根据会员等级显示对应折扣标签 | P1 |

### 5.4 边界条件测试

| 测试场景 | 测试步骤 | 预期结果 | 优先级 |
|---------|---------|---------|-------|
| 跨日预约边界 | S会员在23:59预约明天的场地 | 按当时日期计算可预约范围 | P1 |
| 跨周预约边界 | SS会员在周日预约下周一的场地 | 不允许预约（超出本周范围） | P1 |
| 跨月预约边界 | SSS会员在月末预约下月的场地 | 按30天范围计算，可能可以预约 | P1 |
| 订阅过期边界 | 会员订阅到期时正好有预约 | 预约保持有效，但不能新建 | P1 |
| 核销时间边界 | 预约时间开始后1小时才核销 | 核销成功，记录核销时间 | P2 |
| 折扣时间边界 | 17:59下单 | 享受白天折扣 | P2 |
| 折扣时间边界 | 18:00下单 | 无折扣 | P2 |

### 5.5 自动发券测试

| 测试场景 | 测试步骤 | 预期结果 | 优先级 |
|---------|---------|---------|-------|
| 订阅首日发券 | 会员开通订阅 | 立即发放对应数量咖啡券 | P0 |
| 月度自动发券 | 等待订阅满一个月 | 自动发放下月咖啡券 | P0 |
| S会员发券数量 | 查看S会员发券记录 | 每月发放3张咖啡券 | P1 |
| SS会员发券数量 | 查看SS会员发券记录 | 每月发放5张咖啡券 | P1 |
| SSS会员发券数量 | 查看SSS会员发券记录 | 每月发放10张咖啡券 | P1 |
| 重复发券防护 | 手动执行发券任务两次 | 同一会员同月只发一次 | P0 |

---

## 六、任务分解与排期

### 6.1 按优先级排序的任务列表

#### P0 - 核心功能 (必须完成)

| 任务ID | 任务名称 | 预计耗时 | 依赖 | 负责模块 |
|-------|---------|---------|------|---------|
| T001 | app.js 会员状态管理改造 | 2h | - | 小程序 |
| T002 | api.js 新增权限检查接口 | 1h | - | 小程序 |
| T003 | 场馆预约页面移除价格 | 2h | - | 小程序 |
| T004 | 场馆预约页面权限检查 | 4h | T001, T002 | 小程序 |
| T005 | 会员卡片组件开发 | 4h | - | 小程序 |
| T006 | 我的页面集成会员卡片 | 3h | T005 | 小程序 |
| T007 | 管理后台会员等级配置改造 | 4h | - | 后台 |
| T008 | 管理后台预约列表核销功能 | 3h | - | 后台 |

#### P1 - 重要功能 (应该完成)

| 任务ID | 任务名称 | 预计耗时 | 依赖 | 负责模块 |
|-------|---------|---------|------|---------|
| T009 | 点餐页面折扣显示 | 3h | T002 | 小程序 |
| T010 | 下单页面折扣计算 | 2h | T009 | 小程序 |
| T011 | 会员中心页面重构 | 5h | T005 | 小程序 |
| T012 | 预约权限提示组件 | 3h | - | 小程序 |
| T013 | 管理后台违约管理页面 | 5h | - | 后台 |
| T014 | 管理后台发券管理页面 | 4h | - | 后台 |
| T015 | 数据看板会员统计图表 | 3h | - | 后台 |

#### P2 - 增强功能 (可选完成)

| 任务ID | 任务名称 | 预计耗时 | 依赖 | 负责模块 |
|-------|---------|---------|------|---------|
| T016 | 会员权益详情页面 | 4h | T011 | 小程序 |
| T017 | 违约记录查看页面 | 3h | - | 小程序 |
| T018 | 主题色动态切换优化 | 2h | T001 | 小程序 |
| T019 | 管理后台场馆高尔夫配置 | 2h | - | 后台 |
| T020 | 管理后台会员详情页改造 | 3h | - | 后台 |

### 6.2 详细排期建议

```
Day 1 (8h):
  [2h] T001 - app.js 会员状态管理改造
  [1h] T002 - api.js 新增权限检查接口
  [2h] T003 - 场馆预约页面移除价格
  [3h] T004 - 场馆预约页面权限检查 (部分)

Day 2 (8h):
  [1h] T004 - 场馆预约页面权限检查 (完成)
  [4h] T005 - 会员卡片组件开发
  [3h] T006 - 我的页面集成会员卡片

Day 3 (8h):
  [4h] T007 - 管理后台会员等级配置改造
  [3h] T008 - 管理后台预约列表核销功能
  [1h] Buffer

Day 4 (8h):
  [3h] T009 - 点餐页面折扣显示
  [2h] T010 - 下单页面折扣计算
  [3h] T012 - 预约权限提示组件

Day 5 (8h):
  [5h] T011 - 会员中心页面重构
  [3h] T015 - 数据看板会员统计图表

Day 6 (8h):
  [5h] T013 - 管理后台违约管理页面
  [3h] T014 - 管理后台发券管理页面 (部分)

Day 7 (8h):
  [1h] T014 - 管理后台发券管理页面 (完成)
  [4h] T016 - 会员权益详情页面
  [3h] T017 - 违约记录查看页面

Day 8 (6h): 测试与修复
  [3h] P0 功能测试
  [3h] Bug 修复

Day 9 (6h): 测试与文档
  [3h] P1 功能测试
  [2h] Bug 修复
  [1h] 文档更新
```

### 6.3 验收标准

#### T001 - app.js 会员状态管理改造
- [ ] globalData 包含 memberLevel、memberTheme、canBook、bookingQuota 等字段
- [ ] setMemberTheme 方法正确设置主题色
- [ ] getMemberInfo 正确解析新的响应字段
- [ ] 登录成功后自动设置会员主题

#### T003 - 场馆预约页面移除价格
- [ ] 表头不再显示"¥XX/时"
- [ ] 底部栏不再显示"合计：¥XXX"
- [ ] 确认预约弹窗不再显示价格

#### T004 - 场馆预约页面权限检查
- [ ] 页面加载时调用权限检查接口
- [ ] TRIAL会员显示"无法自行预约"提示
- [ ] 超出预约范围的日期显示为不可选
- [ ] 预约次数达上限时显示提示
- [ ] 权限变化时日期选择器正确更新

#### T005 - 会员卡片组件开发
- [ ] 组件根据等级显示不同主题色
- [ ] 正确显示用户头像、昵称、ID
- [ ] 正确显示等级代码和等级名称
- [ ] 正确显示剩余预约次数和可约范围

---

## 七、风险点和注意事项

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| 主题色在某些机型显示异常 | 用户体验差 | 准备降级方案，使用固定色值 |
| 权限检查接口响应慢 | 页面加载延迟 | 添加本地缓存，设置超时处理 |
| 小程序包体积增大 | 首次加载慢 | 组件分包加载，图片压缩 |
| 后台表单字段过多 | 操作复杂 | 使用分步骤表单或折叠面板 |

### 7.2 业务风险

| 风险 | 影响 | 缓解措施 |
|-----|------|---------|
| 现有会员数据迁移 | 会员权益丢失 | 提前备份，默认设为体验会员 |
| 违约惩罚过于严厉 | 用户流失 | 设置申诉渠道，管理员可手动解除 |
| 发券失败 | 会员投诉 | 设置重试机制，发送失败通知 |

### 7.3 注意事项

1. **价格移除需谨慎**
   - 仅移除预约相关价格显示
   - 保留餐饮、商城等其他模块的价格
   - 历史订单的价格信息保留不变

2. **权限检查需前后端双重校验**
   - 前端检查用于用户体验
   - 后端检查是最终安全保障
   - 两端逻辑需保持一致

3. **主题色需考虑无障碍**
   - 确保文字与背景对比度足够
   - 不完全依赖颜色传达信息
   - 关键信息使用文字描述

4. **测试环境配置**
   - 需要准备各等级的测试账号
   - 需要可以修改系统时间测试边界条件
   - 需要可以手动触发定时任务

---

## 八、附录

### A. 相关文件路径汇总

**小程序文件**:
```
user-miniprogram/
├── app.js                                    # 全局逻辑
├── app.wxss                                  # 全局样式
├── utils/
│   └── api.js                               # API 接口
├── components/
│   ├── member-card/                         # [新增] 会员卡片组件
│   └── booking-permission/                  # [新增] 预约权限提示组件
└── pages/
    ├── profile/profile.*                    # 我的页面
    ├── venue-booking/venue-booking.*        # 场馆预约页面
    ├── food/food.*                          # 点餐页面
    ├── food-order/food-order.*              # 下单页面
    ├── member/member.*                      # 会员中心页面
    └── member-benefits/                     # [新增] 会员权益页面
```

**管理后台文件**:
```
admin-frontend/src/views/
├── member/
│   ├── Level.vue                            # 会员等级管理
│   ├── List.vue                             # 会员列表
│   └── Violation.vue                        # [新增] 违约管理
├── reservation/
│   └── List.vue                             # 预约管理
├── coupon/
│   └── Issue.vue                            # [新增] 发券管理
├── venue/
│   └── Type.vue                             # 场馆类型管理
└── Dashboard.vue                            # 数据看板
```

### B. API 接口汇总

| 接口 | 方法 | 说明 |
|-----|------|------|
| `/member/profile` | GET | 获取会员信息（含等级、权限） |
| `/member/booking-permission` | GET | 检查预约权限 |
| `/member/food-discount` | GET | 获取餐食折扣信息 |
| `/member/violations` | GET | 获取违约记录 |
| `/member/reservations/{id}/verify` | POST | 预约核销 |
| `/members/{id}/penalty` | POST | 管理员处理惩罚 |
| `/coupons/monthly-issue` | POST | 批量发券 |

### C. 测试账号建议

| 账号类型 | 手机号 | 等级 | 用途 |
|---------|-------|------|------|
| 体验会员 | 13800000001 | TRIAL | 测试预约限制 |
| 初级会员 | 13800000002 | S | 测试2天范围、2次上限 |
| 中级会员 | 13800000003 | SS | 测试7天范围、3次上限 |
| VIP会员 | 13800000004 | SSS | 测试30天范围、高尔夫 |
| 惩罚会员 | 13800000005 | S | 测试惩罚状态 |
