# 小程序虚拟支付合规改造（路线B）Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** 移除小程序内全部"虚拟商品在线购买"入口（金币充值、会员卡在线购买），改为到店办理引导，使提交版本符合微信「小程序虚拟支付」审核规则，重新提交审核通过。

**Architecture:** 纯前端入口与文案改造，后端接口全部保留（无前端入口即不会触发审核；后续路线A接入官方虚拟支付时可复用）。金币支付预约、积分商城（积分免费获得）、邀请赠币均为合规场景，不动。

**Tech Stack:** 微信小程序原生（WXML/JS），FastAPI 后端（仅 1 处文案微调）。

**背景（审核驳回原因）：** 微信官方《虚拟支付》文档规定：小程序内虚拟商品（虚拟货币、订阅内容、付费功能等）的购买和支付必须接入官方「小程序虚拟支付」。本小程序的金币充值（`/payment/create-order`）和会员卡在线购买（`buy_member_card`）被认定为虚拟商品。场馆预约微信支付属于线下实体服务消费，合规。

**现状调查结论（2026-08-07 实测）：**
- 线上支付场景共 3 个：金币充值、会员卡购买、场馆预约微信支付（合规保留）
- 数据库 banner / announcement 表均为空，activity 表无充值宣传文案 → 无运营位文案风险
- 教练端未上线，但 coach-wallet 页在同一代码包内，需一并处理（改动极小）
- coach-wallet.js 的 `goToRecharge` 本来就是"功能开发中"桩函数，从未真正可用

---

### Task 1: 钱包页（wallet）移除充值按钮

**Files:**
- Modify: `user-miniprogram/pages/wallet/wallet.wxml:21`
- Modify: `user-miniprogram/pages/wallet/wallet.js:83-88`

**Step 1: wxml 删除充值按钮，替换为到店提示**

将：

```xml
      <button class="btn-recharge" bindtap="goToRecharge" wx:if="{{currentTab === 'coin'}}">充值</button>
```

替换为：

```xml
      <view class="recharge-tip" wx:if="{{currentTab === 'coin'}}">金币充值请前往门店前台办理</view>
```

**Step 2: js 删除 goToRecharge 死代码**

将 wallet.js 末尾：

```js
  // 去充值
  goToRecharge() {
    wx.navigateTo({
      url: '/pages/recharge/recharge'
    })
  }
})
```

替换为：

```js
})
```

**Step 3: 校验**

Run: `node --check user-miniprogram/pages/wallet/wallet.js`
Expected: 无输出（语法通过）

---

### Task 2: 个人中心（profile）移除"金币充值"资产项

**Files:**
- Modify: `user-miniprogram/pages/profile/profile.wxml:73-77`
- Modify: `user-miniprogram/pages/profile/profile.js:210-219`

**Step 1: wxml 删除第三个资产项（含分隔线）**

将：

```xml
    <view class="asset-divider"></view>
    <view class="asset-item" bindtap="goToRecharge">
      <text class="asset-value recharge-btn">充值</text>
      <text class="asset-label">金币充值</text>
    </view>
  </view>
```

替换为：

```xml
  </view>
```

（即资产卡片只保留"金币"和"积分"两项，均跳转钱包页查看余额——查看余额本身合规）

**Step 2: js 删除 goToRecharge 方法**

将 profile.js 中：

```js
  // 充值
  goToRecharge() {
    if (!this.data.isLoggedIn) {
      this.goToLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/recharge/recharge'
    })
  },

```

整段删除。

**Step 3: 校验**

Run: `node --check user-miniprogram/pages/profile/profile.js`
Expected: 无输出

---

### Task 3: 充值页改造为"到店充值说明"页

页面保留注册（app.json 不动），但内容整体替换：不再展示套餐、不再发起支付。防止任何残留入口（如运营配置跳转）落到支付流程。

**Files:**
- Modify: `user-miniprogram/pages/recharge/recharge.wxml`（整体替换）
- Modify: `user-miniprogram/pages/recharge/recharge.js`（整体替换）

**Step 1: wxml 整体替换为**

```xml
<view class="container">
  <view class="notice">
    <view class="notice-title">金币充值</view>
    <view class="notice-item">本店金币为到店储值余额，如需充值请前往门店前台办理。</view>
  </view>

  <view class="notice">
    <view class="notice-title">金币使用规则</view>
    <view class="notice-item">1. 金币可用于场馆预约、教练预约等店内消费</view>
    <view class="notice-item">2. 金币不可提现、不可转让</view>
    <view class="notice-item">3. 如有问题，请联系客服</view>
  </view>
</view>
```

**Step 2: js 整体替换为**

```js
Page({
  data: {}
})
```

**Step 3: 校验**

Run: `node --check user-miniprogram/pages/recharge/recharge.js`
Expected: 无输出

注意：wxss 中套餐/按钮样式变为无用类，保留不删（无功能影响，避免误删共用样式）。

---

### Task 4: 会员中心（member）在线购买改"到店开通"

会员卡套餐列表继续展示（属于线下服务报价展示，合规），但点击行为从"拉起微信支付"改为"到店办理提示"。

**Files:**
- Modify: `user-miniprogram/pages/member/member.js:93-190`（buyCard 改写 + 删除 doPurchase）
- Modify: `user-miniprogram/pages/member/member.wxml:65,69`

**Step 1: member.js 改写 buyCard、删除 doPurchase**

将 `// 购买会员卡` 起至文件末尾 `}` 前的 `buyCard` 与 `doPurchase` 两个方法，替换为：

```js
  // 会员套餐点击：引导到店开通
  buyCard(e) {
    const cardId = e.currentTarget.dataset.id
    const card = this.data.cards.find(c => c.id === cardId)

    if (!card) {
      wx.showToast({ title: '套餐不存在', icon: 'none' })
      return
    }

    wx.showModal({
      title: '到店开通',
      content: `「${card.name}」\n价格：¥${card.price}\n有效期：${card.duration_days}天\n\n会员开通与续费请前往门店前台办理`,
      confirmText: '我知道了',
      showCancel: false
    })
  }
})
```

**Step 2: member.wxml 文案调整**

- 第 65 行：`<view class="card-btn">立即开通</view>` → `<view class="card-btn">到店开通</view>`
- 第 69 行：`<text>暂无可购买的套餐</text>` → `<text>暂无会员套餐</text>`

**Step 3: 校验**

Run: `node --check user-miniprogram/pages/member/member.js`
Expected: 无输出

注意：`utils/api.js` 中 `purchaseMemberCard` / `queryMemberCardOrder` 变为未引用函数，**保留**（路线A复用）。member.js 顶部若 `api` 引用因此未再使用，保留 import 不影响运行。

---

### Task 5: 教练钱包页（coach-wallet）移除充值按钮与宣传文案

教练端未上线，但在同一代码包内，审核可触达，一并处理。

**Files:**
- Modify: `user-miniprogram/pages/coach-wallet/coach-wallet.wxml:17-19,27`
- Modify: `user-miniprogram/pages/coach-wallet/coach-wallet.js:83-89`

**Step 1: wxml 删除充值按钮区**

将：

```xml
    <view class="action-buttons" wx:if="{{currentTab === 'coin'}}">
      <button class="action-btn" bindtap="goToRecharge">充值</button>
    </view>
```

整段删除。

**Step 2: wxml 修改规则文案**

将：

```xml
      <text>• 教练享受专属充值优惠</text>
```

替换为：

```xml
      <text>• 金币充值请前往门店前台办理</text>
```

**Step 3: js 删除 goToRecharge 桩函数**

将：

```js
  // 跳转充值
  goToRecharge() {
    wx.showToast({
      title: '功能开发中',
      icon: 'none'
    })
  }
})
```

替换为：

```js
})
```

**Step 4: 校验**

Run: `node --check user-miniprogram/pages/coach-wallet/coach-wallet.js`
Expected: 无输出

---

### Task 6: 后端余额不足提示文案微调

用户用金币支付预约但余额不足时，引导到店充值（纯文案，不动逻辑）。

**Files:**
- Modify: `backend/app/api/v1/member_api.py`（约 1237 行，`create_reservation` 内）

**Step 1: 修改文案**

将：

```python
            raise HTTPException(status_code=400, detail="金币余额不足")
```

替换为：

```python
            raise HTTPException(status_code=400, detail="金币余额不足，请到店充值")
```

（先 `grep -n "金币余额不足" backend/app/api/v1/member_api.py` 确认仅 1 处）

**Step 2: 部署到服务器并重启**

```bash
scp -i security-incident-20260806/id_ed25519_rebuild backend/app/api/v1/member_api.py ubuntu@yunlifang.cloud:/tmp/
ssh -i security-incident-20260806/id_ed25519_rebuild ubuntu@yunlifang.cloud \
  "sudo cp /tmp/member_api.py /var/www/sports-bar-project/backend/app/api/v1/member_api.py && cd /var/www/sports-bar-project/backend && ./venv/bin/python -c 'import app.main' && sudo systemctl restart sports-bar && sleep 2 && sudo systemctl is-active sports-bar"
```

Expected: 输出 `active`

---

### Task 7: 全量自查与验证

**Step 1: 残留检查（应只剩合规表述）**

```bash
grep -rn "确认充值\|立即开通\|充值套餐\|选择套餐\|充值优惠" user-miniprogram/pages --include="*.wxml" --include="*.js"
```

Expected: 无输出（recharge 页已改造、member 按钮已改名、coach-wallet 优惠文案已删）

```bash
grep -rn "pages/recharge/recharge" user-miniprogram --include="*.js" --include="*.wxml" --include="*.json"
```

Expected: 仅剩 `app.json` 的页面注册（无任何跳转入口）

**Step 2: 全部改动文件语法校验**

```bash
node --check user-miniprogram/pages/wallet/wallet.js && \
node --check user-miniprogram/pages/profile/profile.js && \
node --check user-miniprogram/pages/recharge/recharge.js && \
node --check user-miniprogram/pages/member/member.js && \
node --check user-miniprogram/pages/coach-wallet/coach-wallet.js && echo ALL_OK
```

**Step 3: 微信开发者工具人工走查清单**

- [ ] 我的（profile）：资产区只有"金币""积分"两项，无充值入口
- [ ] 钱包（wallet）：金币 tab 下显示"金币充值请前往门店前台办理"，无充值按钮
- [ ] 充值页（直接输入路径进入）：只有到店办理说明，无套餐、无支付按钮
- [ ] 会员中心（member）：卡片显示"到店开通"，点击弹"到店开通"提示，不拉起支付
- [ ] 场馆预约：微信支付正常拉起（合规场景，回归验证）
- [ ] 场馆预约：金币支付正常（回归验证）

---

### Task 8: 提交

```bash
git add user-miniprogram/pages/wallet user-miniprogram/pages/profile \
  user-miniprogram/pages/recharge user-miniprogram/pages/member \
  user-miniprogram/pages/coach-wallet backend/app/api/v1/member_api.py
git commit -m "fix: 虚拟支付合规改造（路线B）——金币充值/会员卡购买转到店办理

- 钱包页/个人中心/教练钱包：移除充值入口
- 充值页：改造为到店充值说明页，移除套餐与支付
- 会员中心：在线购买改为到店开通提示
- 后端：金币余额不足提示补充到店充值引导
- 后端支付接口保留（无前端入口，后续接入官方虚拟支付时复用）"
```

---

## 明确不变更的部分

| 内容 | 原因 |
|---|---|
| 后端 `/payment/create-order`、`/payment/packages`、`buy_member_card` 接口 | 无前端入口即不触发审核；路线A复用 |
| admin 后台充值套餐管理、手动加金币（`recharge_coin`） | 线下充值后的操作工具，正是路线B的配套 |
| 金币支付预约、补支付 `/repay` | 消费储值余额，非购买虚拟商品 |
| 积分商城（积分兑换） | 积分免费获得（签到/活动），无购买行为 |
| 邀请赠币 | 免费获得，非购买 |
| app.json 页面注册 | 页面保留但内容合规，避免残留链接 404 |

## 重新提交审核时的建议

1. 审核说明（选填）写：「本小程序为线下体育场馆预约服务，线上支付均为场馆场地等实体服务消费；金币为到店储值余额，仅支持门店前台充值，小程序内不提供虚拟商品购买。」
2. 上传前在开发者工具"详情-本地设置"确认无体验版残留入口。
3. 若再次被驳回且仍指向虚拟支付，把驳回截图发我，再针对性排查（可能存在未发现的入口）。

## 回滚方案

全部改动为单一 commit，`git revert <commit>` 即可恢复线上充值能力（如后续路线A落地）。
