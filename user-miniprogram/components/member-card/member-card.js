/**
 * 会员卡片组件
 * 根据会员等级显示不同主题色
 */
const app = getApp()

Component({
  properties: {
    // 会员信息
    memberInfo: {
      type: Object,
      value: null
    },
    // 会员等级: GUEST, MEMBER（兼容旧值 TRIAL/S/SS/SSS）
    level: {
      type: String,
      value: 'GUEST'
    },
    // 是否显示详细信息
    showDetail: {
      type: Boolean,
      value: true
    },
    // 是否可点击
    clickable: {
      type: Boolean,
      value: true
    }
  },

  data: {
    // 主题配置（单一会员制）
    themeConfig: {
      GUEST: {
        primary: '#999999',
        gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)',
        name: '普通用户',
        icon: '/assets/icons/level-guest.png'
      },
      MEMBER: {
        primary: '#C9A962',
        gradient: 'linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)',
        name: '尊享会员',
        icon: '/assets/icons/level-member.png'
      }
    },
    // 旧等级映射（兼容）
    legacyLevelMap: {
      TRIAL: 'GUEST',
      S: 'MEMBER',
      SS: 'MEMBER',
      SSS: 'MEMBER'
    },
    currentTheme: null,
    currentLevel: 'GUEST',  // 实际使用的等级（GUEST/MEMBER）
    isMember: false,
    memberExpireTime: null
  },

  observers: {
    'level': function(newLevel) {
      // 只有在 memberInfo 没有提供等级时才使用 level 属性
      if (!this.data.memberInfo || (!this.data.memberInfo.member_level && !this.data.memberInfo.level_code)) {
        this.updateTheme(newLevel)
      }
    },
    'memberInfo': function(info) {
      if (info) {
        this.updateMemberExpire(info)
        // 如果 memberInfo 中包含 level_code 或 member_level，优先使用
        const levelFromInfo = info.member_level || info.level_code
        if (levelFromInfo) {
          this.updateTheme(levelFromInfo)
        } else {
          // 否则使用传入的 level 属性
          this.updateTheme(this.data.level)
        }
      }
    }
  },

  lifetimes: {
    attached() {
      // 优先从 memberInfo 获取等级
      const memberInfo = this.data.memberInfo
      const levelFromInfo = memberInfo && (memberInfo.member_level || memberInfo.level_code)
      const initialLevel = levelFromInfo || this.data.level || 'GUEST'
      this.updateTheme(initialLevel)
      if (memberInfo) {
        this.updateMemberExpire(memberInfo)
      }
    }
  },

  methods: {
    // 更新主题（兼容旧等级名）
    updateTheme(level) {
      const mappedLevel = this.data.legacyLevelMap[level] || level || 'GUEST'
      const theme = this.data.themeConfig[mappedLevel] || this.data.themeConfig.GUEST
      this.setData({
        currentTheme: theme,
        currentLevel: mappedLevel,
        isMember: (mappedLevel === 'MEMBER')
      })
    },

    // 更新会员有效期信息
    updateMemberExpire(info) {
      this.setData({
        memberExpireTime: info.member_expire_time || null
      })
    },

    // 卡片点击
    onCardTap() {
      if (this.data.clickable) {
        this.triggerEvent('tap', {
          level: this.data.level,
          memberInfo: this.data.memberInfo
        })
      }
    },

    // 跳转升级
    onUpgradeTap() {
      wx.navigateTo({
        url: '/pages/member/member'
      })
    }
  }
})
