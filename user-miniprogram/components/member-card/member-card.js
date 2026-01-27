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
    quotaInfo: {
      daily: 0,
      used: 0,
      remaining: 0
    }
  },

  observers: {
    'level': function(newLevel) {
      this.updateTheme(newLevel)
    },
    'memberInfo': function(info) {
      if (info) {
        this.updateQuotaInfo(info)
      }
    }
  },

  lifetimes: {
    attached() {
      this.updateTheme(this.data.level)
    }
  },

  methods: {
    // 更新主题
    updateTheme(level) {
      const theme = this.data.themeConfig[level] || this.data.themeConfig.TRIAL
      this.setData({
        currentTheme: theme
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
      const level = info.member_level || this.data.level
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
