const { request, BASE_URL } = require('../../utils/api')
const { isLoggedIn } = require('../../utils/auth')

function formatDate(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function displayDate(d) {
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function formatCompletedAt(value) {
  if (!value) return '已完成'
  try {
    const d = new Date(value)
    const h = String(d.getHours()).padStart(2, '0')
    const m = String(d.getMinutes()).padStart(2, '0')
    return `${h}:${m}`
  } catch (e) {
    return '已完成'
  }
}

function resolvePhotoUrl(photoUrl) {
  if (photoUrl.startsWith('http://') || photoUrl.startsWith('https://')) return photoUrl
  return BASE_URL + photoUrl
}

Page({
  data: {
    progress: null,
    sortedTasks: [],
    progressPercent: 0,
    loading: true,
    currentDate: null,
    displayDate: '',
    childId: null
  },

  onShow() {
    if (!isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    if (!this.data.currentDate) {
      this.setData({ currentDate: new Date() })
    }
    const childId = wx.getStorageSync('selectedChildId')
    if (childId) {
      this.setData({ childId })
      this.loadProgress(childId)
    }
  },

  onChildChange(e) {
    const childId = e.detail.childId
    this.setData({ childId })
    this.loadProgress(childId)
  },

  prevDay() {
    const d = new Date(this.data.currentDate)
    d.setDate(d.getDate() - 1)
    this.setData({ currentDate: d })
    this.loadProgress(this.data.childId)
  },

  nextDay() {
    const d = new Date(this.data.currentDate)
    d.setDate(d.getDate() + 1)
    this.setData({ currentDate: d })
    this.loadProgress(this.data.childId)
  },

  loadProgress(childId) {
    if (!childId) return
    this.setData({ loading: true, displayDate: displayDate(this.data.currentDate) })
    const dateStr = formatDate(this.data.currentDate)

    request({ url: `/api/progress/${childId}/${dateStr}` }).then(progress => {
      const sortedTasks = progress.tasks.map(t => {
        const isDone = t.status === 'done'
        let timeText = isDone ? formatCompletedAt(t.completed_at) : '未完成'
        if (isDone && t.completed_by_username) {
          timeText += ` · 提交人：${t.completed_by_username}`
        }
        const photoUrls = (t.photos || []).map(p => resolvePhotoUrl(p.photo_url))
        return { ...t, timeText, photoUrls }
      })

      const total = progress.total_tasks
      const percent = total > 0 ? Math.round(progress.completed_tasks / total * 100) : 0

      this.setData({ progress, sortedTasks, progressPercent: percent, loading: false })
    }).catch(() => {
      this.setData({ loading: false })
    })
  },

  viewPhotos(e) {
    const urls = e.currentTarget.dataset.photos
    if (urls && urls.length > 0) {
      wx.previewImage({ current: urls[0], urls })
    }
  }
})
