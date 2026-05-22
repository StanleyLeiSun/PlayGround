const BASE_URL = 'http://47.94.167.238'

function getToken() {
  return wx.getStorageSync('token') || ''
}

function request(options) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const header = { 'Content-Type': 'application/json' }
    if (token) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: `${BASE_URL}${options.url}`,
      method: options.method || 'GET',
      data: options.data,
      header: { ...header, ...options.header },
      success(res) {
        if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.redirectTo({ url: '/pages/login/login' })
          reject(new Error('Unauthorized'))
          return
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error(res.data.detail || `HTTP ${res.statusCode}`))
        }
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

function uploadFile(url, filePath, name) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    wx.uploadFile({
      url: `${BASE_URL}${url}`,
      filePath,
      name,
      header: { 'Authorization': `Bearer ${token}` },
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data))
        } else {
          reject(new Error(`Upload failed: ${res.statusCode}`))
        }
      },
      fail(err) {
        reject(err)
      }
    })
  })
}

module.exports = { request, uploadFile, BASE_URL }
