const { silentLogin, bind } = require('../../utils/auth')

Page({
  data: {
    showBindForm: false,
    username: '',
    password: '',
    loading: false,
    errorMsg: '',
    openid: ''
  },

  onLoad() {
    this.tryLogin()
  },

  tryLogin() {
    silentLogin().then(result => {
      if (result.needBinding) {
        this.setData({ showBindForm: true, openid: result.openid })
      } else {
        wx.switchTab({ url: '/pages/tasks/tasks' })
      }
    }).catch(() => {
      this.setData({ showBindForm: true })
    })
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  onBind() {
    const { openid, username, password } = this.data
    if (!username || !password) {
      this.setData({ errorMsg: '请输入用户名和密码' })
      return
    }
    this.setData({ loading: true, errorMsg: '' })
    bind(openid, username, password).then(() => {
      wx.switchTab({ url: '/pages/tasks/tasks' })
    }).catch(err => {
      this.setData({ errorMsg: err.message || '绑定失败，请检查账号密码', loading: false })
    })
  }
})
