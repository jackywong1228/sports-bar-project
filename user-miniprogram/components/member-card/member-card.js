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
    // 会员等级: S, SS, SSS（兼容旧值 GUEST/TRIAL/MEMBER）
    level: {
      type: String,
      value: 'S'
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
    // 主题配置（三级会员制：S/SS/SSS）
    themeConfig: {
      S: {
        primary: '#999999',
        gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)',
        name: 'S级会员'
      },
      SS: {
        primary: '#C9A962',
        gradient: 'linear-gradient(135deg, #C9A962 0%, #E8D5A3 100%)',
        name: 'SS级会员'
      },
      SSS: {
        primary: '#8B7355',
        gradient: 'linear-gradient(135deg, #8B7355 0%, #C9A962 50%, #E8D5A3 100%)',
        name: 'SSS级会员'
      }
    },
    // 旧等级映射到新等级（兼容旧值）
    legacyLevelMap: {
      GUEST: 'S',
      TRIAL: 'S',
      MEMBER: 'SS'
    },
    currentTheme: null,
    currentLevel: 'S',  // 实际使用的等级（S/SS/SSS）
    isMember: false,
    memberExpireTime: null,
    quotaInfo: {
      daily: '-',
      remaining: '-'
    }
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
        this.updateQuotaInfo(info)
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
      const initialLevel = levelFromInfo || this.data.level || 'S'
      this.updateTheme(initialLevel)
      if (memberInfo) {
        this.updateMemberExpire(memberInfo)
        this.updateQuotaInfo(memberInfo)
      }
    }
  },

  methods: {
    // 更新主题（兼容旧等级名，映射到 S/SS/SSS）
    updateTheme(level) {
      const mappedLevel = this.data.legacyLevelMap[level] || level || 'S'
      const theme = this.data.themeConfig[mappedLevel] || this.data.themeConfig.S
      this.setData({
        currentTheme: theme,
        currentLevel: mappedLevel,
        isMember: (mappedLevel === 'SS' || mappedLevel === 'SSS')
      })
    },

    // 更新会员有效期信息
    updateMemberExpire(info) {
      this.setData({
        memberExpireTime: info.member_expire_time || null
      })
    },

    // 更新预约额度信息
    updateQuotaInfo(info) {
      const levelCode = info.member_level || info.level_code || 'S'
      const mapped = this.data.legacyLevelMap[levelCode] || levelCode
      if (mapped === 'SSS') {
        const daily = info.daily_free_hours || 2
        const remaining = info.daily_free_hours_remaining != null ? info.daily_free_hours_remaining : daily
        this.setData({
          quotaInfo: {
            daily: daily + 'h',
            remaining: parseFloat(remaining.toFixed(1)) + 'h'
          }
        })
      } else if (mapped === 'SS') {
        this.setData({
          quotaInfo: {
            daily: '当天',
            remaining: '可约'
          }
        })
      } else {
        this.setData({
          quotaInfo: {
            daily: '-',
            remaining: '-'
          }
        })
      }
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
