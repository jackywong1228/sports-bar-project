# 运动社交小程序 UI 改造设计文档

> 版本: 1.0
> 日期: 2026-01-28
> 参考风格: 高端运动俱乐部/高尔夫会所小程序

---

## 一、现状分析

### 1.1 当前设计风格

当前小程序已经采用了"温网风格"（墨绿+薰衣草紫），但存在以下问题：

| 问题 | 现状 | 目标 |
|------|------|------|
| 首页设计 | 传统列表式布局，轮播图+快捷入口+列表 | 沉浸式全屏设计，大气高端 |
| 视觉层次 | 层次感不够强，缺乏焦点 | 主次分明，突出核心功能 |
| 品牌感 | 普通运动APP风格 | 高端会所/俱乐部调性 |
| 色彩使用 | 部分页面仍使用橙色(#FF6B35) | 统一墨绿主题 |
| 字体排版 | 普通中文排版 | 中英双语，精致排版 |

### 1.2 当前页面结构

```
pages/
├── index/         # 首页 - 轮播图+快捷入口+热门列表
├── venue/         # 预约 - 类型筛选+场馆列表
├── activity/      # 活动 - 标签栏+活动卡片
├── profile/       # 我的 - 用户信息+资产+菜单
├── coach-list/    # 教练列表
├── venue-detail/  # 场馆详情
├── ...            # 其他子页面
```

### 1.3 发现的问题

1. **venue.wxss, coach-list.wxss, activity.wxss** 仍使用旧的橙色配色 (#FF6B35)
2. 首页缺乏品牌感和沉浸式体验
3. 各页面风格不够统一
4. 缺少中英文双语设计元素
5. 图标和视觉素材缺乏高端感

---

## 二、设计规范

### 2.1 色彩规范

#### 主色调 - 墨绿系

| 名称 | 色值 | 用途 |
|------|------|------|
| **主色 Primary** | `#1A5D3A` | 主按钮、导航栏、重要文字 |
| **主色浅 Primary Light** | `#2E7D52` | 渐变色、hover状态 |
| **主色深 Primary Dark** | `#144A2E` | 深色背景、强调 |
| **主色透明** | `rgba(26, 93, 58, 0.1)` | 标签背景、浅色强调 |

#### 辅助色 - 薰衣草紫

| 名称 | 色值 | 用途 |
|------|------|------|
| **辅色 Secondary** | `#6B5B95` | 次要按钮、辅助信息 |
| **辅色浅** | `#8677A9` | 渐变色 |
| **辅色透明** | `rgba(107, 91, 149, 0.1)` | 标签背景 |

#### 点缀色 - 金色

| 名称 | 色值 | 用途 |
|------|------|------|
| **金色 Gold** | `#C9A962` | 会员标识、星级、奖杯 |
| **金色浅** | `#D4B97A` | 高亮、边框 |
| **金色深** | `#A68B3E` | 深色文字 |

#### 功能色

| 名称 | 色值 | 用途 |
|------|------|------|
| **成功 Success** | `#2E7D52` | 可预约、成功状态 |
| **警告 Warning** | `#C9A962` | 即将开始、提醒 |
| **错误 Danger** | `#C75050` | 错误、已满 |
| **信息 Info** | `#6B7B6E` | 次要信息 |

#### 中性色

| 名称 | 色值 | 用途 |
|------|------|------|
| **背景 Background** | `#F5F7F5` | 页面背景 |
| **卡片 Card** | `#FFFFFF` | 卡片背景 |
| **文字主 Text Primary** | `#2C3E2D` | 主要文字 |
| **文字次 Text Secondary** | `#6B7B6E` | 次要文字 |
| **文字弱 Text Muted** | `#9CA89D` | 辅助文字 |
| **边框 Border** | `#E8EDE9` | 分割线、边框 |
| **边框浅** | `#F0F4F1` | 浅色分割线 |

### 2.2 字体规范

#### 字体家族
```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
             'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
```

#### 英文标题字体（推荐）
- 大标题建议使用: `'Playfair Display'`, `'Didot'`, `'Georgia'` 风格
- 可通过图片形式实现特殊英文字体效果

#### 字号规范

| 级别 | 大小 | 行高 | 用途 |
|------|------|------|------|
| **H1 超大标题** | 72rpx | 1.2 | 首页品牌标题 |
| **H2 大标题** | 48rpx | 1.3 | 页面标题 |
| **H3 中标题** | 36rpx | 1.4 | 区块标题 |
| **H4 小标题** | 32rpx | 1.4 | 卡片标题 |
| **正文** | 28rpx | 1.6 | 正文内容 |
| **辅助文字** | 26rpx | 1.5 | 次要信息 |
| **小字** | 24rpx | 1.5 | 标签、提示 |
| **微小字** | 22rpx | 1.4 | 角标、注释 |

#### 字重规范

| 名称 | 值 | 用途 |
|------|------|------|
| Regular | 400 | 正文 |
| Medium | 500 | 次要标题 |
| Semibold | 600 | 主要标题 |
| Bold | 700 | 强调、价格 |

### 2.3 间距规范

基础单位: `8rpx`

| 名称 | 值 | 用途 |
|------|------|------|
| xs | 8rpx | 元素内部间距 |
| sm | 16rpx | 紧凑间距 |
| md | 24rpx | 常规间距 |
| lg | 32rpx | 宽松间距 |
| xl | 48rpx | 区块间距 |
| 2xl | 64rpx | 大区块间距 |

### 2.4 圆角规范

| 名称 | 值 | 用途 |
|------|------|------|
| sm | 8rpx | 小标签 |
| md | 12rpx | 输入框、小卡片 |
| lg | 16rpx | 卡片、按钮 |
| xl | 24rpx | 大卡片 |
| 2xl | 32rpx | 弹窗 |
| full | 50% | 圆形头像 |
| pill | 999rpx | 胶囊按钮 |

### 2.5 阴影规范

```css
/* 小阴影 - 浅层次 */
.shadow-sm {
  box-shadow: 0 2rpx 8rpx rgba(26, 93, 58, 0.04);
}

/* 中阴影 - 卡片 */
.shadow {
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.08);
}

/* 大阴影 - 弹出层 */
.shadow-lg {
  box-shadow: 0 8rpx 32rpx rgba(26, 93, 58, 0.12);
}

/* 按钮阴影 */
.shadow-btn {
  box-shadow: 0 6rpx 20rpx rgba(26, 93, 58, 0.3);
}
```

---

## 三、组件规范

### 3.1 按钮 Button

#### 主按钮
```css
.btn-primary {
  height: 92rpx;
  border-radius: 46rpx;
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 500;
  box-shadow: 0 6rpx 20rpx rgba(26, 93, 58, 0.3);
}
```

#### 次要按钮
```css
.btn-secondary {
  height: 92rpx;
  border-radius: 46rpx;
  background: linear-gradient(135deg, #6B5B95 0%, #8677A9 100%);
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 500;
  box-shadow: 0 6rpx 20rpx rgba(107, 91, 149, 0.3);
}
```

#### 轮廓按钮
```css
.btn-outline {
  height: 92rpx;
  border-radius: 46rpx;
  background: transparent;
  border: 2rpx solid #1A5D3A;
  color: #1A5D3A;
  font-size: 32rpx;
  font-weight: 500;
}
```

#### 金色按钮（高端感）
```css
.btn-gold {
  height: 92rpx;
  border-radius: 46rpx;
  background: linear-gradient(135deg, #C9A962 0%, #D4B97A 100%);
  color: #FFFFFF;
  font-size: 32rpx;
  font-weight: 500;
  box-shadow: 0 6rpx 20rpx rgba(201, 169, 98, 0.3);
}
```

### 3.2 卡片 Card

#### 基础卡片
```css
.card {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.08);
}
```

#### 高端卡片（带金色边框）
```css
.card-premium {
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 28rpx;
  border: 1rpx solid rgba(201, 169, 98, 0.3);
  box-shadow: 0 4rpx 20rpx rgba(201, 169, 98, 0.15);
}
```

### 3.3 标签 Tag

```css
/* 主色标签 */
.tag-primary {
  background: rgba(26, 93, 58, 0.1);
  color: #1A5D3A;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  font-weight: 500;
}

/* 金色标签 */
.tag-gold {
  background: linear-gradient(135deg, #F5E6C8 0%, #E8D5A8 100%);
  color: #8B7333;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  font-weight: 500;
}
```

### 3.4 输入框 Input

```css
.input {
  background: #FFFFFF;
  border: 2rpx solid #E8EDE9;
  border-radius: 12rpx;
  padding: 24rpx;
  font-size: 28rpx;
  color: #2C3E2D;
  transition: border-color 0.2s;
}

.input:focus {
  border-color: #1A5D3A;
}
```

---

## 四、首页 (index) 改造方案

### 4.1 设计目标

将首页从传统的列表式布局改造为**沉浸式品牌展示页**，参考高端高尔夫俱乐部小程序设计。

### 4.2 新首页结构

```
┌─────────────────────────────────┐
│  [状态栏 - 透明]                 │
├─────────────────────────────────┤
│                                 │
│     [全屏背景图/视频]            │
│                                 │
│     ┌─────────────────┐         │
│     │   SPORTS        │ ← 英文大标题
│     │     CLUB        │
│     │                 │
│     │  运动 · 健康 · 社交 │ ← 中文标语
│     └─────────────────┘         │
│                                 │
│     ┌───────────────────┐       │
│     │   立 即 预 约      │ ← 主CTA按钮
│     └───────────────────┘       │
│                                 │
│  ┌──────────┐  ┌──────────┐    │
│  │ 🏟 场馆   │  │ 👨‍🏫 教练  │    │ ← 底部快捷入口
│  └──────────┘  └──────────┘    │
│                                 │
├─────────────────────────────────┤
│  [TabBar - 白色/半透明]          │
└─────────────────────────────────┘
```

### 4.3 首页 WXML 改造方案

```xml
<!-- pages/index/index.wxml -->
<view class="hero-container">
  <!-- 沉浸式背景 -->
  <view class="hero-background">
    <image
      class="hero-bg-image"
      src="{{heroImage}}"
      mode="aspectFill"
    ></image>
    <view class="hero-overlay"></view>
  </view>

  <!-- 主内容区 -->
  <view class="hero-content">
    <!-- 品牌标题 -->
    <view class="brand-section">
      <text class="brand-title-en">SPORTS</text>
      <text class="brand-title-en brand-title-sub">CLUB</text>
      <text class="brand-slogan">运动 · 健康 · 社交</text>
    </view>

    <!-- 主按钮 -->
    <view class="hero-cta">
      <button class="btn-hero" bindtap="goToVenue">立即预约</button>
    </view>

    <!-- 底部快捷入口 -->
    <view class="hero-shortcuts">
      <view class="shortcut-item" bindtap="goToVenue">
        <view class="shortcut-icon-wrap">
          <image class="shortcut-icon" src="/assets/icons/venue-hero.png"></image>
        </view>
        <text class="shortcut-text">场馆预约</text>
        <text class="shortcut-text-en">VENUE</text>
      </view>
      <view class="shortcut-item" bindtap="goToCoach">
        <view class="shortcut-icon-wrap">
          <image class="shortcut-icon" src="/assets/icons/coach-hero.png"></image>
        </view>
        <text class="shortcut-text">私教课程</text>
        <text class="shortcut-text-en">COACH</text>
      </view>
    </view>
  </view>

  <!-- 下拉提示（可选） -->
  <view class="scroll-hint" wx:if="{{showScrollHint}}">
    <text class="scroll-hint-text">上滑查看更多</text>
    <view class="scroll-hint-arrow">∨</view>
  </view>
</view>

<!-- 内容区域（下滑展示） -->
<view class="content-container" wx:if="{{showContent}}">
  <!-- 公告轮播 -->
  <view class="announcement-bar" wx:if="{{announcements.length > 0}}">
    <swiper class="announcement-swiper" autoplay circular vertical>
      <swiper-item wx:for="{{announcements}}" wx:key="id">
        <view class="announcement-item">
          <text class="announcement-tag">公告</text>
          <text class="announcement-text">{{item.title}}</text>
        </view>
      </swiper-item>
    </swiper>
  </view>

  <!-- 热门场馆 -->
  <view class="section">
    <view class="section-header">
      <view class="section-title-wrap">
        <text class="section-title-en">POPULAR</text>
        <text class="section-title">热门场馆</text>
      </view>
      <view class="section-more" bindtap="viewMoreVenues">
        <text>查看全部</text>
        <text class="more-arrow">→</text>
      </view>
    </view>
    <!-- 场馆卡片列表 -->
    <scroll-view class="venue-scroll" scroll-x>
      <view class="venue-card-premium" wx:for="{{hotVenues}}" wx:key="id" bindtap="goToVenueDetail" data-id="{{item.id}}">
        <image class="venue-card-image" src="{{item.image}}" mode="aspectFill"></image>
        <view class="venue-card-info">
          <text class="venue-card-name">{{item.name}}</text>
          <view class="venue-card-meta">
            <text class="venue-card-type">{{item.type_name}}</text>
            <view class="venue-card-price">
              <text class="price-symbol">¥</text>
              <text class="price-value">{{item.price}}</text>
              <text class="price-unit">/小时</text>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>

  <!-- 推荐教练 -->
  <view class="section">
    <view class="section-header">
      <view class="section-title-wrap">
        <text class="section-title-en">COACHES</text>
        <text class="section-title">推荐教练</text>
      </view>
      <view class="section-more" bindtap="viewMoreCoaches">
        <text>查看全部</text>
        <text class="more-arrow">→</text>
      </view>
    </view>
    <!-- 教练卡片 -->
    <view class="coach-grid">
      <view class="coach-card-premium" wx:for="{{hotCoaches}}" wx:key="id" bindtap="goToCoachDetail" data-id="{{item.id}}">
        <image class="coach-avatar" src="{{item.avatar}}" mode="aspectFill"></image>
        <text class="coach-name">{{item.name}}</text>
        <text class="coach-specialty">{{item.type_name}}</text>
        <view class="coach-rating">
          <text class="rating-star">★</text>
          <text class="rating-value">{{item.rating || 5.0}}</text>
        </view>
      </view>
    </view>
  </view>

  <!-- 热门活动 -->
  <view class="section">
    <view class="section-header">
      <view class="section-title-wrap">
        <text class="section-title-en">EVENTS</text>
        <text class="section-title">热门活动</text>
      </view>
      <view class="section-more" bindtap="viewMoreActivities">
        <text>查看全部</text>
        <text class="more-arrow">→</text>
      </view>
    </view>
    <!-- 活动卡片 -->
    <view class="activity-card-premium" wx:for="{{hotActivities}}" wx:key="id" bindtap="goToActivityDetail" data-id="{{item.id}}">
      <image class="activity-card-image" src="{{item.image}}" mode="aspectFill"></image>
      <view class="activity-card-content">
        <text class="activity-card-title">{{item.title}}</text>
        <view class="activity-card-info">
          <text class="activity-card-time">{{item.start_date}} {{item.start_time}}</text>
          <view class="activity-card-price">
            <text wx:if="{{item.price > 0}}">¥{{item.price}}</text>
            <text wx:else class="free-tag">免费</text>
          </view>
        </view>
      </view>
    </view>
  </view>

  <!-- 底部留白 -->
  <view class="safe-bottom"></view>
</view>
```

### 4.4 首页 WXSS 改造方案

```css
/* pages/index/index.wxss - 高端沉浸式设计 */

/* ===== 沉浸式首屏 ===== */
.hero-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.hero-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.hero-bg-image {
  width: 100%;
  height: 100%;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    180deg,
    rgba(26, 93, 58, 0.3) 0%,
    rgba(26, 93, 58, 0.6) 50%,
    rgba(20, 74, 46, 0.85) 100%
  );
}

.hero-content {
  position: relative;
  z-index: 10;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0 60rpx;
  padding-bottom: 200rpx;
}

/* 品牌标题 */
.brand-section {
  text-align: center;
  margin-bottom: 80rpx;
}

.brand-title-en {
  display: block;
  font-size: 96rpx;
  font-weight: 300;
  color: #FFFFFF;
  letter-spacing: 24rpx;
  text-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.3);
  font-family: 'Georgia', 'Times New Roman', serif;
}

.brand-title-sub {
  font-size: 72rpx;
  letter-spacing: 20rpx;
  margin-top: -10rpx;
}

.brand-slogan {
  display: block;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 12rpx;
  margin-top: 32rpx;
}

/* 主CTA按钮 */
.hero-cta {
  margin-bottom: 80rpx;
}

.btn-hero {
  width: 400rpx;
  height: 100rpx;
  line-height: 100rpx;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #1A5D3A;
  font-size: 34rpx;
  font-weight: 600;
  letter-spacing: 8rpx;
  border-radius: 50rpx;
  border: none;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.2);
}

.btn-hero::after {
  border: none;
}

/* 底部快捷入口 */
.hero-shortcuts {
  display: flex;
  gap: 60rpx;
}

.shortcut-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.shortcut-icon-wrap {
  width: 100rpx;
  height: 100rpx;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
  margin-bottom: 16rpx;
}

.shortcut-icon {
  width: 48rpx;
  height: 48rpx;
}

.shortcut-text {
  font-size: 26rpx;
  color: #FFFFFF;
  font-weight: 500;
}

.shortcut-text-en {
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 4rpx;
  margin-top: 4rpx;
}

/* 下拉提示 */
.scroll-hint {
  position: absolute;
  bottom: 180rpx;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  animation: bounce 2s infinite;
}

.scroll-hint-text {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.6);
}

.scroll-hint-arrow {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 8rpx;
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateX(-50%) translateY(0);
  }
  40% {
    transform: translateX(-50%) translateY(-16rpx);
  }
  60% {
    transform: translateX(-50%) translateY(-8rpx);
  }
}

/* ===== 内容区域 ===== */
.content-container {
  background: #F5F7F5;
  padding-top: 24rpx;
}

/* 公告栏 */
.announcement-bar {
  background: linear-gradient(135deg, rgba(26, 93, 58, 0.08) 0%, rgba(107, 91, 149, 0.08) 100%);
  margin: 0 24rpx 24rpx;
  border-radius: 12rpx;
  padding: 0 20rpx;
}

.announcement-swiper {
  height: 72rpx;
}

.announcement-item {
  display: flex;
  align-items: center;
  height: 72rpx;
}

.announcement-tag {
  background: #1A5D3A;
  color: #FFFFFF;
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  margin-right: 16rpx;
}

.announcement-text {
  font-size: 26rpx;
  color: #2C3E2D;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 区块 */
.section {
  background: #FFFFFF;
  margin: 0 24rpx 24rpx;
  padding: 32rpx;
  border-radius: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(26, 93, 58, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 28rpx;
}

.section-title-wrap {
  display: flex;
  flex-direction: column;
}

.section-title-en {
  font-size: 22rpx;
  color: #C9A962;
  letter-spacing: 4rpx;
  font-weight: 600;
  margin-bottom: 4rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: 600;
  color: #2C3E2D;
}

.section-more {
  display: flex;
  align-items: center;
  font-size: 26rpx;
  color: #6B7B6E;
}

.more-arrow {
  margin-left: 8rpx;
  color: #1A5D3A;
}

/* 场馆卡片 - 高端版 */
.venue-scroll {
  white-space: nowrap;
  margin: 0 -32rpx;
  padding: 0 32rpx;
}

.venue-card-premium {
  display: inline-block;
  width: 320rpx;
  margin-right: 24rpx;
  border-radius: 16rpx;
  overflow: hidden;
  background: #FFFFFF;
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.1);
}

.venue-card-image {
  width: 320rpx;
  height: 200rpx;
}

.venue-card-info {
  padding: 20rpx;
}

.venue-card-name {
  font-size: 30rpx;
  font-weight: 600;
  color: #2C3E2D;
  display: block;
  margin-bottom: 12rpx;
}

.venue-card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.venue-card-type {
  font-size: 22rpx;
  color: #1A5D3A;
  background: rgba(26, 93, 58, 0.1);
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
}

.venue-card-price {
  color: #1A5D3A;
}

.venue-card-price .price-symbol {
  font-size: 22rpx;
}

.venue-card-price .price-value {
  font-size: 36rpx;
  font-weight: bold;
}

.venue-card-price .price-unit {
  font-size: 22rpx;
  color: #6B7B6E;
}

/* 教练网格 */
.coach-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20rpx;
}

.coach-card-premium {
  width: calc(50% - 10rpx);
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  text-align: center;
  border: 1rpx solid #E8EDE9;
  box-shadow: 0 2rpx 12rpx rgba(26, 93, 58, 0.06);
}

.coach-card-premium .coach-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  margin-bottom: 16rpx;
  border: 3rpx solid rgba(201, 169, 98, 0.3);
}

.coach-card-premium .coach-name {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #2C3E2D;
  margin-bottom: 8rpx;
}

.coach-card-premium .coach-specialty {
  display: block;
  font-size: 24rpx;
  color: #6B7B6E;
  margin-bottom: 12rpx;
}

.coach-card-premium .coach-rating {
  display: inline-flex;
  align-items: center;
  background: rgba(201, 169, 98, 0.1);
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
}

.coach-card-premium .rating-star {
  color: #C9A962;
  font-size: 24rpx;
  margin-right: 6rpx;
}

.coach-card-premium .rating-value {
  font-size: 24rpx;
  color: #A68B3E;
  font-weight: 500;
}

/* 活动卡片 - 高端版 */
.activity-card-premium {
  display: flex;
  background: #FFFFFF;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(26, 93, 58, 0.06);
}

.activity-card-image {
  width: 240rpx;
  height: 160rpx;
  flex-shrink: 0;
}

.activity-card-content {
  flex: 1;
  padding: 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.activity-card-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #2C3E2D;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.activity-card-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-card-time {
  font-size: 24rpx;
  color: #6B7B6E;
}

.activity-card-price {
  font-size: 28rpx;
  font-weight: bold;
  color: #1A5D3A;
}

.activity-card-price .free-tag {
  color: #2E7D52;
  font-weight: 500;
}

/* 底部安全区 */
.safe-bottom {
  height: 120rpx;
}
```

---

## 五、场馆页面 (venue) 改造方案

### 5.1 改造目标

- 统一使用墨绿色配色方案
- 提升卡片精致度
- 增加中英双语元素

### 5.2 WXSS 改造要点

```css
/* pages/venue/venue.wxss - 改造后 */

.container {
  min-height: 100vh;
  background: #F5F7F5;
}

/* 类型筛选 - 统一墨绿风格 */
.type-scroll {
  display: flex;
  white-space: nowrap;
  background: #FFFFFF;
  padding: 24rpx 30rpx;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2rpx 8rpx rgba(26, 93, 58, 0.04);
}

.type-item {
  display: inline-block;
  padding: 16rpx 32rpx;
  margin-right: 20rpx;
  border-radius: 30rpx;
  font-size: 28rpx;
  color: #6B7B6E;
  background: #F5F7F5;
  transition: all 0.2s;
}

.type-item.active {
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  color: #FFFFFF;
  box-shadow: 0 4rpx 12rpx rgba(26, 93, 58, 0.3);
}

/* 场馆卡片 */
.venue-card {
  background: #FFFFFF;
  border-radius: 16rpx;
  margin-bottom: 20rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.08);
}

/* 标签统一墨绿色 */
.tag {
  display: inline-block;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
  background: rgba(26, 93, 58, 0.1);
  color: #1A5D3A;
}

.tag-hot {
  background: rgba(201, 169, 98, 0.15);
  color: #A68B3E;
}

/* 状态标签 */
.venue-status.available {
  background: rgba(46, 125, 82, 0.1);
  color: #2E7D52;
}

.venue-status.unavailable {
  background: rgba(107, 123, 110, 0.1);
  color: #6B7B6E;
}

/* 预约按钮 - 墨绿渐变 */
.btn-book {
  width: 100%;
  height: 80rpx;
  line-height: 80rpx;
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  color: #FFFFFF;
  font-size: 28rpx;
  font-weight: 500;
  border-radius: 40rpx;
  border: none;
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.25);
}

.btn-book::after {
  border: none;
}
```

---

## 六、教练列表页 (coach-list) 改造方案

### 6.1 WXSS 改造要点

```css
/* pages/coach-list/coach-list.wxss - 改造后 */

.container {
  min-height: 100vh;
  background: #F5F7F5;
}

/* 类型筛选 */
.type-bar {
  display: flex;
  background: #FFFFFF;
  padding: 24rpx 20rpx;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2rpx 8rpx rgba(26, 93, 58, 0.04);
}

.type-item {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 28rpx;
  color: #6B7B6E;
  border-radius: 30rpx;
  margin: 0 10rpx;
  transition: all 0.2s;
}

.type-item.active {
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  color: #FFFFFF;
  box-shadow: 0 4rpx 12rpx rgba(26, 93, 58, 0.3);
}

/* 教练卡片 */
.coach-card {
  display: flex;
  background: #FFFFFF;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.08);
}

.coach-avatar {
  width: 140rpx;
  height: 140rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
  border: 2rpx solid rgba(201, 169, 98, 0.2);
}

/* 等级星星 - 金色 */
.level-star {
  color: #C9A962;
  font-size: 24rpx;
}

/* 标签 - 墨绿色 */
.tag {
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
  background: rgba(26, 93, 58, 0.1);
  color: #1A5D3A;
}

/* 价格 - 墨绿色 */
.price-value {
  font-size: 36rpx;
  font-weight: bold;
  color: #1A5D3A;
}
```

---

## 七、活动页面 (activity) 改造方案

### 7.1 WXSS 改造要点

```css
/* pages/activity/activity.wxss - 改造后 */

.container {
  min-height: 100vh;
  background: #F5F7F5;
}

/* 标签栏 */
.tab-bar {
  display: flex;
  background: #FFFFFF;
  padding: 20rpx 30rpx;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2rpx 8rpx rgba(26, 93, 58, 0.04);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 16rpx 0;
  font-size: 28rpx;
  color: #6B7B6E;
  position: relative;
}

.tab-item.active {
  color: #1A5D3A;
  font-weight: 600;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 6rpx;
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  border-radius: 3rpx;
}

/* 活动卡片 */
.activity-card {
  background: #FFFFFF;
  border-radius: 16rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.08);
}

/* 活动状态 */
.activity-status.upcoming {
  background: linear-gradient(135deg, #C9A962 0%, #D4B97A 100%);
}

.activity-status.ongoing {
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
}

.activity-status.ended {
  background: rgba(107, 123, 110, 0.8);
}

/* 价格 */
.activity-price .price {
  font-size: 36rpx;
  font-weight: bold;
  color: #1A5D3A;
}

.activity-price .free {
  font-size: 30rpx;
  color: #2E7D52;
  font-weight: 600;
}

/* 进度条 */
.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  border-radius: 6rpx;
}
```

---

## 八、我的页面 (profile) 改造方案

### 8.1 改造目标

当前 profile 页面已较好地遵循墨绿主题，需要优化：
- 统一教练入口卡片配色
- 统一排行榜入口卡片配色
- 增强高端感

### 8.2 WXSS 改造要点

```css
/* 教练入口卡片 - 改为墨绿系 */
.coach-entry-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
  margin: 0 24rpx 20rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 20rpx rgba(26, 93, 58, 0.3);
}

/* 排行榜入口卡片 - 改为金色系 */
.rank-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #C9A962 0%, #D4B97A 100%);
  margin: 0 24rpx 20rpx;
  padding: 28rpx;
  border-radius: 16rpx;
  box-shadow: 0 4rpx 20rpx rgba(201, 169, 98, 0.3);
}
```

---

## 九、全局样式 (app.wxss) 补充

### 9.1 新增高端组件类

```css
/* app.wxss 新增 */

/* ===== 高端双语标题 ===== */
.title-bilingual {
  display: flex;
  flex-direction: column;
}

.title-en {
  font-size: 22rpx;
  color: #C9A962;
  letter-spacing: 4rpx;
  font-weight: 600;
  text-transform: uppercase;
}

.title-cn {
  font-size: 36rpx;
  font-weight: 600;
  color: #2C3E2D;
  margin-top: 4rpx;
}

/* ===== 金色强调元素 ===== */
.gold-highlight {
  color: #C9A962;
}

.gold-bg {
  background: linear-gradient(135deg, #C9A962 0%, #D4B97A 100%);
}

.gold-border {
  border: 1rpx solid rgba(201, 169, 98, 0.3);
}

/* ===== 高端卡片 ===== */
.card-luxury {
  background: #FFFFFF;
  border-radius: 20rpx;
  padding: 32rpx;
  box-shadow: 0 8rpx 32rpx rgba(26, 93, 58, 0.1);
  border: 1rpx solid rgba(201, 169, 98, 0.15);
}

/* ===== 磨砂玻璃效果 ===== */
.glass-effect {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1rpx solid rgba(255, 255, 255, 0.2);
}

/* ===== 渐变文字 ===== */
.text-gradient-gold {
  background: linear-gradient(135deg, #C9A962 0%, #D4B97A 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ===== 高级按钮 ===== */
.btn-luxury {
  height: 100rpx;
  line-height: 100rpx;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%);
  color: #1A5D3A;
  font-size: 32rpx;
  font-weight: 600;
  letter-spacing: 6rpx;
  border-radius: 50rpx;
  border: none;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.15);
}

/* ===== 图标容器 ===== */
.icon-wrap {
  width: 88rpx;
  height: 88rpx;
  background: rgba(26, 93, 58, 0.1);
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-wrap-gold {
  background: rgba(201, 169, 98, 0.15);
}

/* ===== 分割线高级版 ===== */
.divider-gradient {
  height: 2rpx;
  background: linear-gradient(90deg, transparent 0%, #E8EDE9 50%, transparent 100%);
  margin: 32rpx 0;
}

/* ===== 价格展示 ===== */
.price-display {
  display: flex;
  align-items: baseline;
  color: #1A5D3A;
}

.price-display .symbol {
  font-size: 26rpx;
  font-weight: 500;
}

.price-display .amount {
  font-size: 48rpx;
  font-weight: bold;
  margin: 0 4rpx;
}

.price-display .unit {
  font-size: 24rpx;
  color: #6B7B6E;
}
```

---

## 十、资源素材清单

### 10.1 需要新增/更新的图标

| 图标名称 | 用途 | 规格 | 风格要求 |
|----------|------|------|----------|
| venue-hero.png | 首页场馆入口 | 96x96 | 白色线性图标 |
| coach-hero.png | 首页教练入口 | 96x96 | 白色线性图标 |
| hero-bg-1.jpg | 首页背景图1 | 1125x2436 | 运动场景，深色调 |
| hero-bg-2.jpg | 首页背景图2 | 1125x2436 | 健身场景，深色调 |
| hero-bg-3.jpg | 首页背景图3 | 1125x2436 | 球类运动，深色调 |

### 10.2 TabBar 图标更新建议

当前图标可保持，但建议调整为更精致的线性风格。

### 10.3 背景图要求

- 分辨率: 1125x2436px (3x)
- 色调: 偏暗，便于叠加墨绿色遮罩
- 主题: 运动场馆、健身器材、网球/高尔夫场景
- 格式: JPG，压缩至 200KB 以内

---

## 十一、实施优先级

### 阶段一：配色统一（紧急）

1. 修复 venue.wxss 中的橙色配色 (#FF6B35 -> #1A5D3A)
2. 修复 coach-list.wxss 中的橙色配色
3. 修复 activity.wxss 中的橙色配色
4. 修复 profile.wxss 中不协调的渐变色

### 阶段二：首页改造（重要）

1. 实现沉浸式首页布局
2. 添加品牌标题区域
3. 优化快捷入口设计
4. 添加下拉内容区域

### 阶段三：细节优化（一般）

1. 添加中英双语元素
2. 优化卡片阴影和圆角
3. 更新图标素材
4. 添加动画效果

### 阶段四：资源更新（后续）

1. 设计并更换首页背景图
2. 更新 TabBar 图标
3. 更新快捷入口图标

---

## 十二、改造进度记录

> 更新时间：2026-01-28

### 已完成页面

| 页面 | 路径 | 改造内容 | 完成状态 |
|------|------|----------|----------|
| **首页** | `pages/index/` | 沉浸式全屏品牌展示页设计，墨绿渐变叠加层，品牌标题区域，快捷入口卡片 | ✅ 已完成 |
| **场馆页** | `pages/venue/` | 类型筛选标签统一墨绿配色，场馆卡片样式优化，状态标签颜色调整 | ✅ 已完成 |
| **教练列表** | `pages/coach-list/` | 类型筛选墨绿渐变，教练卡片配色统一，等级星星改为金色 | ✅ 已完成 |
| **活动页** | `pages/activity/` | 标签栏下划线墨绿渐变，活动状态标签颜色调整，价格文字统一墨绿 | ✅ 已完成 |
| **我的页面** | `pages/profile/` | 教练中心入口卡片改为墨绿渐变，排行榜入口卡片改为金色渐变 | ✅ 已完成 |
| **全局样式** | `app.wxss` | CSS变量定义，高端组件类（双语标题、金色强调、高端卡片、磨砂玻璃效果等） | ✅ 已完成 |

### 待改造页面

以下页面仍使用旧橙色配色 `#FF6B35`，需要改造：

#### 高优先级（核心用户流程）

| 页面 | 路径 | 当前问题 | 建议改造 |
|------|------|----------|----------|
| 场馆详情 | `pages/venue-detail/` | 橙色预约按钮、价格文字 | 改为墨绿渐变按钮 |
| 教练详情 | `pages/coach-detail/` | 橙色预约按钮、价格文字 | 改为墨绿渐变按钮 |
| 活动详情 | `pages/activity-detail/` | 橙色报名按钮、状态标签 | 改为墨绿渐变按钮 |
| 登录页 | `pages/login/` | 橙色登录按钮 | 改为墨绿渐变按钮 |
| 钱包页 | `pages/wallet/` | 橙色充值按钮、资产数字 | 改为墨绿/金色配色 |
| 充值页 | `pages/recharge/` | 橙色套餐选中、支付按钮 | 改为墨绿渐变 |
| 订单列表 | `pages/orders/` | 橙色状态标签、操作按钮 | 改为墨绿配色 |
| 订单详情 | `pages/order-detail/` | 橙色状态、操作按钮 | 改为墨绿配色 |

#### 中优先级（次要功能）

| 页面 | 路径 | 当前问题 | 建议改造 |
|------|------|----------|----------|
| 点餐首页 | `pages/food/` | 橙色分类标签、加购按钮 | 改为墨绿配色 |
| 购物车 | `pages/food-cart/` | 橙色结算按钮、数量调整 | 改为墨绿渐变 |
| 下单页 | `pages/food-order/` | 橙色提交按钮 | 改为墨绿渐变 |
| 积分商城 | `pages/mall/` | 橙色兑换按钮 | 改为墨绿/金色配色 |
| 商品详情 | `pages/mall-detail/` | 橙色兑换按钮 | 改为墨绿渐变 |
| 组队广场 | `pages/team/` | 橙色创建/加入按钮 | 改为墨绿渐变 |
| 组队详情 | `pages/team-detail/` | 橙色操作按钮 | 改为墨绿配色 |

#### 低优先级（辅助页面）

| 页面 | 路径 | 当前问题 | 建议改造 |
|------|------|----------|----------|
| 会员中心 | `pages/member/` | 橙色会员卡样式 | 改为墨绿/金色配色 |
| 优惠券 | `pages/coupons/` | 橙色优惠券样式 | 改为墨绿/金色配色 |
| 设置页 | `pages/settings/` | 橙色开关、按钮 | 改为墨绿配色 |
| 场馆预约 | `pages/venue-booking/` | 橙色时段选中、确认按钮 | 改为墨绿渐变 |
| 教练预约 | `pages/coach-booking/` | 橙色时段选中、确认按钮 | 改为墨绿渐变 |

#### 教练端页面（需评估）

| 页面 | 路径 | 说明 |
|------|------|------|
| 教练首页 | `pages/coach-home/` | 预约日历，需检查配色 |
| 教练登录 | `pages/coach-login/` | 登录按钮 |
| 教练个人 | `pages/coach-profile/` | 菜单样式 |
| 排期管理 | `pages/coach-schedule/` | 时段选择样式 |
| 教练码 | `pages/coach-code/` | 二维码展示样式 |
| 课程收入 | `pages/coach-income/` | 数据展示样式 |
| 教练钱包 | `pages/coach-wallet/` | 资产展示样式 |
| 教练订单 | `pages/coach-orders/` | 订单卡片样式 |
| 教练推广 | `pages/coach-promote/` | 推广码样式 |
| 预约详情 | `pages/coach-reservation-detail/` | 详情卡片样式 |

### 改造统计

| 分类 | 已完成 | 待完成 | 完成率 |
|------|--------|--------|--------|
| 主要TabBar页面 | 4 | 0 | 100% |
| 详情页 | 0 | 3 | 0% |
| 核心流程页 | 0 | 5 | 0% |
| 餐饮相关 | 0 | 3 | 0% |
| 商城相关 | 0 | 2 | 0% |
| 组队相关 | 0 | 2 | 0% |
| 辅助页面 | 0 | 5 | 0% |
| 教练端页面 | 0 | 10 | 0% |
| **总计** | **4+2** | **30** | **17%** |

> 注：已完成包括 4 个主要页面 + 首页 + 全局样式

### 配色参考速查

```css
/* 主色墨绿 */
--color-primary: #1A5D3A;
--color-primary-light: #2E7D52;
--color-primary-dark: #144A2E;

/* 金色点缀 */
--color-gold: #C9A962;
--color-gold-light: #D4B97A;
--color-gold-dark: #A68B3E;

/* 背景色 */
--color-bg: #F5F7F5;

/* 渐变按钮 */
background: linear-gradient(135deg, #1A5D3A 0%, #2E7D52 100%);
box-shadow: 0 4rpx 16rpx rgba(26, 93, 58, 0.25);

/* 需要替换的旧橙色 */
/* #FF6B35 -> #1A5D3A */
/* #E55A2B -> #2E7D52 */
```

---

## 十二、注意事项

1. **渐进式改造**：建议按阶段实施，避免一次性大改动影响线上体验
2. **设备兼容**：沉浸式设计需考虑不同机型的安全区域
3. **性能优化**：首页背景图需要做好压缩和懒加载
4. **A/B测试**：首页改版可考虑做灰度发布
5. **用户反馈**：改版后收集用户反馈，持续优化

---

## 附录：CSS 变量参考

```css
/* 建议在 app.wxss 顶部定义 CSS 变量（小程序需兼容处理） */
page {
  --color-primary: #1A5D3A;
  --color-primary-light: #2E7D52;
  --color-primary-dark: #144A2E;
  --color-secondary: #6B5B95;
  --color-secondary-light: #8677A9;
  --color-gold: #C9A962;
  --color-gold-light: #D4B97A;
  --color-gold-dark: #A68B3E;
  --color-success: #2E7D52;
  --color-warning: #C9A962;
  --color-danger: #C75050;
  --color-bg: #F5F7F5;
  --color-card: #FFFFFF;
  --color-text: #2C3E2D;
  --color-text-secondary: #6B7B6E;
  --color-text-muted: #9CA89D;
  --color-border: #E8EDE9;
  --color-border-light: #F0F4F1;
  --radius-sm: 8rpx;
  --radius-md: 12rpx;
  --radius-lg: 16rpx;
  --radius-xl: 24rpx;
  --shadow-sm: 0 2rpx 8rpx rgba(26, 93, 58, 0.04);
  --shadow-md: 0 4rpx 16rpx rgba(26, 93, 58, 0.08);
  --shadow-lg: 0 8rpx 32rpx rgba(26, 93, 58, 0.12);
}
```

---

**文档结束**

> 本设计文档由架构师 (Architect Agent) + UI/UX PRO MAX 于 2026-01-28 输出
> 如有疑问，请联系开发团队
