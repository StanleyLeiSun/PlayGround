const { request } = require('./api')

function isLoggedIn() {
  return !!wx.getStorageSync('token')
}

function saveLoginResult(data) {
  wx.setStorageSync('token', data.access_token)
  wx.setStorageSync('user', data.user)
}

function clearAuth() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('user')
  wx.removeStorageSync('selectedChildId')
}

function silentLogin() {
  return new Promise((resolve, reject) => {
    wx.login({
      success(loginRes) {
        if (!loginRes.code) {
          reject(new Error('wx.login failed'))
          return
        }
        request({
          url: '/api/auth/wechat-login',
          method: 'POST',
          data: { code: loginRes.code }
        }).then(data => {
          if (data.need_binding) {
            resolve({ needBinding: true, openid: data.openid })
          } else {
            saveLoginResult(data)
            resolve({ needBinding: false })
          }
        }).catch(reject)
      },
      fail: reject
    })
  })
}

function bind(openid, username, password) {
  return request({
    url: '/api/auth/wechat-bind',
    method: 'POST',
    data: { openid, username, password }
  }).then(data => {
    saveLoginResult(data)
    return data
  })
}

module.exports = { isLoggedIn, silentLogin, bind, clearAuth, saveLoginResult }
