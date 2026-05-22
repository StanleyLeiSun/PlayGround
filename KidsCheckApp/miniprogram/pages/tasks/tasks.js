const { request, uploadFile } = require('../../utils/api')
const { isLoggedIn } = require('../../utils/auth')

function getToday() {
  const d = new Date()
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

Page({
  data: {
    tasks: [],
    requiredTasks: [],
    conditionalTasks: [],
    hasUncompletedRequired: false,
    loading: true,
    childId: null
  },

  onShow() {
    if (!isLoggedIn()) {
      wx.redirectTo({ url: '/pages/login/login' })
      return
    }
    const childId = wx.getStorageSync('selectedChildId')
    if (childId) {
      this.setData({ childId })
      this.loadTasks(childId)
    }
  },

  onChildChange(e) {
    const childId = e.detail.childId
    this.setData({ childId })
    this.loadTasks(childId)
  },

  loadTasks(childId) {
    this.setData({ loading: true })
    const today = getToday()
    request({ url: `/api/daily-tasks/${childId}/${today}` }).then(tasks => {
      const requiredTasks = tasks.filter(t => !t.is_conditional)
      const conditionalTasks = tasks.filter(t => t.is_conditional)
      const hasUncompletedRequired = requiredTasks.some(t => t.status === 'pending')
      this.setData({ tasks, requiredTasks, conditionalTasks, hasUncompletedRequired, loading: false })
    }).catch(() => {
      this.setData({ loading: false })
    })
  },

  onTaskTap(e) {
    const task = e.currentTarget.dataset.task
    if (task.status === 'done') return

    if (task.type === 'written') {
      wx.showActionSheet({
        itemList: ['拍照存证并完成', '从相册选择并完成'],
        success: (res) => {
          if (res.tapIndex === 0) {
            this.chooseAndUpload(task, 'camera')
          } else if (res.tapIndex === 1) {
            this.chooseAndUpload(task, 'album')
          }
        }
      })
    } else {
      wx.showModal({
        title: '确认完成',
        content: `确认完成「${task.title}」？`,
        success: (res) => {
          if (res.confirm) {
            this.checkIn(task.id)
          }
        }
      })
    }
  },

  chooseAndUpload(task, sourceType) {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: [sourceType],
      sizeType: ['compressed'],
      success: (res) => {
        const tempFilePath = res.tempFiles[0].tempFilePath
        wx.showLoading({ title: '上传中...' })
        uploadFile(`/api/daily-tasks/${task.id}/check-in`, tempFilePath, 'photo').then(() => {
          wx.hideLoading()
          wx.showToast({ title: '打卡成功 ⭐', icon: 'success' })
          this.loadTasks(this.data.childId)
        }).catch(() => {
          wx.hideLoading()
          wx.showToast({ title: '上传失败', icon: 'none' })
        })
      }
    })
  },

  checkIn(taskId) {
    request({ url: `/api/daily-tasks/${taskId}/check-in`, method: 'POST' }).then(() => {
      wx.showToast({ title: '打卡成功 ⭐', icon: 'success' })
      this.loadTasks(this.data.childId)
    }).catch(() => {
      wx.showToast({ title: '打卡失败', icon: 'none' })
    })
  }
})
