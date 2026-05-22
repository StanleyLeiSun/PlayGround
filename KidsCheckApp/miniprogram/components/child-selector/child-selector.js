const { request } = require('../../utils/api')

Component({
  properties: {},

  data: {
    children: [],
    currentChild: {},
    showPicker: false
  },

  lifetimes: {
    attached() {
      this.loadChildren()
    }
  },

  methods: {
    loadChildren() {
      request({ url: '/api/children' }).then(children => {
        const savedId = wx.getStorageSync('selectedChildId')
        const current = children.find(c => c.id === savedId) || children[0] || {}
        this.setData({ children, currentChild: current })
        if (current.id) {
          wx.setStorageSync('selectedChildId', current.id)
          this.triggerEvent('change', { childId: current.id })
        }
      }).catch(() => {})
    },

    onTap() {
      if (this.data.children.length > 1) {
        this.setData({ showPicker: true })
      }
    },

    closePicker() {
      this.setData({ showPicker: false })
    },

    onSelect(e) {
      const child = e.currentTarget.dataset.child
      wx.setStorageSync('selectedChildId', child.id)
      this.setData({ currentChild: child, showPicker: false })
      this.triggerEvent('change', { childId: child.id })
    }
  }
})
