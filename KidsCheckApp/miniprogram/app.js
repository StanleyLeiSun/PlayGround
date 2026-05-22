const { silentLogin, isLoggedIn } = require('./utils/auth')

App({
  onLaunch() {
    if (!isLoggedIn()) {
      silentLogin().then(result => {
        if (result.needBinding) {
          wx.redirectTo({ url: '/pages/login/login' })
        }
      }).catch(() => {
        wx.redirectTo({ url: '/pages/login/login' })
      })
    }
  },

  globalData: {
    selectedChildId: null
  }
})
