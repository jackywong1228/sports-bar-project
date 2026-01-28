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
    // 会员等级: TRIAL, S, SS, SSS
    level: {
      type: String,
      value: 'TRIAL'
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
    // 主题配置
    themeConfig: {
      TRIAL: {
        primary: '#999999',
        gradient: 'linear-gradient(135deg, #999999 0%, #BBBBBB 100%)',
        name: '体验会员',
        icon: '/assets/icons/level-trial.png'
      },
      S: {
        primary: '#4A90E2',
        gradient: 'linear-gradient(135deg, #4A90E2 0%, #6BA8F0 100%)',
        name: 'S级会员',
        icon: '/assets/icons/level-s.png'
      },
      SS: {
        primary: '#9B59B6',
        gradient: 'linear-gradient(135deg, #9B59B6 0%, #B07CC8 100%)',
        name: 'SS级会员',
        icon: '/assets/icons/level-ss.png'
      },
      SSS: {
        primary: '#F39C12',
        gradient: 'linear-gradient(135deg, #F39C12 0%, #F5B041 100%)',
        name: 'SSS级会员',
        icon: '/assets/icons/level-sss.png'
      }
    },
    currentTheme: null,
    currentLevel: 'TRIAL',  // 实际使用的等级（优先从memberInfo获取）
    quotaInfo: {
      daily: 0,
      used: 0,
      remaining: 0
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
      const initialLevel = levelFromInfo || this.data.level || 'TRIAL'
      this.updateTheme(initialLevel)
    }
  },

  methods: {
    // 更新主题
    updateTheme(level) {
      const validLevel = level || 'TRIAL'
      const theme = this.data.themeConfig[validLevel] || this.data.themeConfig.TRIAL
      this.setData({
        currentTheme: theme,
        currentLevel: validLevel
      })
    },

    // 更新额度信息
    updateQuotaInfo(info) {
      const quotaMap = {
        TRIAL: 0,
        S: 2,
        SS: 4,
        SSS: 8
      }
      // 优先使用 member_level 或 level_code
      const level = info.member_level || info.level_code || this.data.level
      const daily = info.booking_quota || quotaMap[level] || 0
      const used = info.used_quota || 0

      this.setData({
        quotaInfo: {
          daily: daily,
          used: used,
          remaining: Math.max(0, daily - used)
        }
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
