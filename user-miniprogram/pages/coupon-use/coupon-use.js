const app = getApp()
const { drawQRCode } = require('../../utils/qrcode')

Page({
  data: {
    coupon: null,
    loading: true,
    error: ''
  },

  onLoad(options) {
    const id = options.id
    if (!id) {
      this.setData({ loading: false, error: '缺少优惠券信息' })
      return
    }
    this.couponId = id
    this.loadCoupon(id)
  },

  async loadCoupon(id) {
    try {
      const res = await app.request({ url: '/member/coupons' })
      const list = res.data || []
      const item = list.find(c => String(c.id) === String(id))

      if (!item) {
        this.setData({ loading: false, error: '优惠券不存在' })
        return
      }

      // Format display fields (same logic as coupons page)
      const now = new Date().getTime()
      const endTime = item.end_time ? new Date(item.end_time.replace(/-/g, '/')).getTime() : 0
      const isExpired = item.status === 'expired' || (endTime > 0 && endTime < now)

      let expireText = ''
      if (item.end_time) {
        const endDate = item.end_time.substring(0, 10)
        const today = new Date().toISOString().substring(0, 10)
        if (endDate === today) {
          expireText = '今日 ' + item.end_time.substring(11, 16) + ' 到期'
        } else {
          expireText = endDate + ' 到期'
        }
      }

      let leftLabel = '', leftValue = ''
      if (item.type === 'gift') {
        leftLabel = '赠品'; leftValue = '免费'
      } else if (item.type === 'hour_free') {
        leftLabel = '时长券'; leftValue = (item.discount_value || 1) + 'h'
      } else if (item.type === 'cash') {
        leftLabel = '代金券'; leftValue = '\u00a5' + (item.discount_value || 0)
      } else {
        leftLabel = '优惠券'; leftValue = '\u00a5' + (item.discount_value || 0)
      }

      this.setData({
        coupon: { ...item, expireText, leftLabel, leftValue, isExpired },
        loading: false
      })

      // Draw QR code after data is set
      this.drawQR('COUPON_VERIFY:' + String(id))
    } catch (err) {
      console.error('加载优惠券详情失败:', err)
      this.setData({ loading: false, error: '加载失败，请重试' })
    }
  },

  drawQR(content) {
    const query = this.createSelectorQuery()
    query.select('#qrCanvas')
      .fields({ node: true, size: true })
      .exec((res) => {
        if (!res[0] || !res[0].node) {
          console.error('Canvas node not found')
          return
        }
        const canvas = res[0].node
        const canvasWidth = res[0].width || 200
        try {
          drawQRCode(canvas, content, canvasWidth, {
            foreground: '#1A5D3A',
            background: '#FFFFFF',
            margin: 8
          })
        } catch (err) {
          console.error('QR code generation failed:', err)
        }
      })
  }
})
