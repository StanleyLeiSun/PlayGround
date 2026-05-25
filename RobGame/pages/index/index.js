const LEVELS = [
  { id: 1, rows: 3, cols: 4, desc: '基础关卡', visibleTime: 2000, spawnMin: 800, spawnMax: 1200, bombChance: 0.25, goldChance: 0, movingChance: 0 },
  { id: 2, rows: 4, cols: 4, desc: '速度加快', visibleTime: 1500, spawnMin: 600, spawnMax: 1000, bombChance: 0.25, goldChance: 0, movingChance: 0 },
  { id: 3, rows: 5, cols: 4, desc: '金色地鼠', visibleTime: 1200, spawnMin: 600, spawnMax: 1000, bombChance: 0.25, goldChance: 0.2, movingChance: 0 },
  { id: 4, rows: 6, cols: 4, desc: '平移地鼠', visibleTime: 1000, spawnMin: 500, spawnMax: 900, bombChance: 0.25, goldChance: 0.15, movingChance: 0.25 }
]

Page({
  data: {
    levels: []
  },

  onShow() {
    const unlocked = wx.getStorageSync('unlockedLevel') || 1
    const levels = LEVELS.map(l => ({
      ...l,
      unlocked: l.id <= unlocked
    }))
    this.setData({ levels })
  },

  selectLevel(e) {
    const id = e.currentTarget.dataset.id
    const level = this.data.levels.find(l => l.id === id)
    if (!level || !level.unlocked) return

    wx.navigateTo({
      url: `/pages/game/game?level=${id}`
    })
  }
})
