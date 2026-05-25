const { silentLogin, bind } = require('../../utils/auth')

Page({
  data: {
    showBindForm: false,
    selectedUser: '',
    password: '',
    loading: false,
    errorMsg: '',
    openid: '',
    users: [
      { username: 'baba', label: '爸爸', icon: '👨' },
      { username: 'mama', label: '妈妈', icon: '👩' },
      { username: 'yeye', label: '爷爷', icon: '👴' },
      { username: 'nainai', label: '奶奶', icon: '👵' },
      { username: 'laolao', label: '姥姥', icon: '👵' },
      { username: 'laoye', label: '姥爷', icon: '👴' }
    ]
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

  onSelectUser(e) {
    const user = e.currentTarget.dataset.user
    this.setData({ selectedUser: user.username, errorMsg: '' })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  onBind() {
    const { openid, selectedUser, password } = this.data
    if (!selectedUser || !password) return
    this.setData({ loading: true, errorMsg: '' })
    bind(openid, selectedUser, password).then(() => {
      wx.switchTab({ url: '/pages/tasks/tasks' })
    }).catch(err => {
      this.setData({ errorMsg: err.message || '绑定失败', loading: false })
    })
  }
})
