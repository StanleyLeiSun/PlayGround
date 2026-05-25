const GAME_DURATION = 30
const TARGET_SCORE = 20
const MAX_VISIBLE_MOLES = 3

const LEVELS = {
  1: { rows: 3, cols: 4, visibleTime: 2000, spawnMin: 800, spawnMax: 1200, bombChance: 0.25, goldChance: 0, movingChance: 0 },
  2: { rows: 4, cols: 4, visibleTime: 1500, spawnMin: 600, spawnMax: 1000, bombChance: 0.25, goldChance: 0, movingChance: 0 },
  3: { rows: 5, cols: 4, visibleTime: 1200, spawnMin: 600, spawnMax: 1000, bombChance: 0.25, goldChance: 0.2, movingChance: 0 },
  4: { rows: 6, cols: 4, visibleTime: 1000, spawnMin: 500, spawnMax: 900, bombChance: 0.25, goldChance: 0.15, movingChance: 0.25 }
}

function makeEmpty(n) {
  return new Array(n).fill(false)
}

Page({
  data: {
    level: 1,
    rows: 3,
    cols: 4,
    holeCount: 12,
    targetScore: TARGET_SCORE,
    score: 0,
    timeLeft: GAME_DURATION,
    moles: [],
    moleTypes: [],
    hitMoles: [],
    hammerAnim: [],
    movingMoles: [],
    gameActive: false,
    gameOver: false,
    passed: false,
    hitCount: 0,
    bombCount: 0,
    goldCount: 0
  },

  _config: null,
  _timerInterval: null,
  _spawnTimeout: null,
  _moleTimeouts: [],

  onLoad(options) {
    const level = parseInt(options.level) || 1
    const config = LEVELS[level] || LEVELS[1]
    this._config = config
    const holeCount = config.rows * config.cols

    this.setData({
      level,
      rows: config.rows,
      cols: config.cols,
      holeCount,
      moles: makeEmpty(holeCount),
      moleTypes: new Array(holeCount).fill(''),
      hitMoles: makeEmpty(holeCount),
      hammerAnim: makeEmpty(holeCount),
      movingMoles: makeEmpty(holeCount)
    })

    this.startGame()
  },

  startGame() {
    this._clearAllTimers()
    const holeCount = this.data.holeCount

    this.setData({
      score: 0,
      timeLeft: GAME_DURATION,
      moles: makeEmpty(holeCount),
      moleTypes: new Array(holeCount).fill(''),
      hitMoles: makeEmpty(holeCount),
      hammerAnim: makeEmpty(holeCount),
      movingMoles: makeEmpty(holeCount),
      gameActive: true,
      gameOver: false,
      passed: false,
      hitCount: 0,
      bombCount: 0,
      goldCount: 0
    })

    this._startTimer()
    this._spawnMole()
  },

  _startTimer() {
    this._timerInterval = setInterval(() => {
      const timeLeft = this.data.timeLeft - 1
      if (timeLeft <= 0) {
        this._endGame(false)
      } else {
        this.setData({ timeLeft })
      }
    }, 1000)
  },

  _spawnMole() {
    if (!this.data.gameActive) return
    const config = this._config

    const visibleCount = this.data.moles.filter(m => m).length
    if (visibleCount < MAX_VISIBLE_MOLES) {
      const availableHoles = []
      this.data.moles.forEach((visible, i) => {
        if (!visible) availableHoles.push(i)
      })

      if (availableHoles.length > 0) {
        const randomIndex = availableHoles[Math.floor(Math.random() * availableHoles.length)]
        const moles = [...this.data.moles]
        const moleTypes = [...this.data.moleTypes]
        const movingMoles = [...this.data.movingMoles]

        moles[randomIndex] = true

        const rand = Math.random()
        if (rand < config.bombChance) {
          moleTypes[randomIndex] = 'bomb'
        } else if (rand < config.bombChance + config.goldChance) {
          moleTypes[randomIndex] = 'gold'
        } else if (rand < config.bombChance + config.goldChance + config.movingChance) {
          moleTypes[randomIndex] = 'moving'
          movingMoles[randomIndex] = true
        } else {
          moleTypes[randomIndex] = 'normal'
        }

        this.setData({ moles, moleTypes, movingMoles })

        if (moleTypes[randomIndex] === 'moving') {
          setTimeout(() => {
            this._moveMole(randomIndex)
          }, config.visibleTime / 2)
        }

        const hideTimeout = setTimeout(() => {
          this._hideMole(randomIndex)
        }, config.visibleTime)
        this._moleTimeouts.push(hideTimeout)
      }
    }

    const nextSpawn = config.spawnMin + Math.random() * (config.spawnMax - config.spawnMin)
    this._spawnTimeout = setTimeout(() => {
      this._spawnMole()
    }, nextSpawn)
  },

  _moveMole(fromIndex) {
    if (!this.data.moles[fromIndex] || !this.data.gameActive) return
    if (this.data.hitMoles[fromIndex]) return

    const cols = this.data.cols
    const rows = this.data.rows
    const row = Math.floor(fromIndex / cols)
    const col = fromIndex % cols

    const neighbors = []
    if (col > 0) neighbors.push(fromIndex - 1)
    if (col < cols - 1) neighbors.push(fromIndex + 1)
    if (row > 0) neighbors.push(fromIndex - cols)
    if (row < rows - 1) neighbors.push(fromIndex + cols)

    const available = neighbors.filter(i => !this.data.moles[i])
    if (available.length === 0) return

    const toIndex = available[Math.floor(Math.random() * available.length)]

    const moles = [...this.data.moles]
    const moleTypes = [...this.data.moleTypes]
    const movingMoles = [...this.data.movingMoles]
    const hitMoles = [...this.data.hitMoles]
    const hammerAnim = [...this.data.hammerAnim]

    moles[fromIndex] = false
    moleTypes[fromIndex] = ''
    movingMoles[fromIndex] = false
    hitMoles[fromIndex] = false
    hammerAnim[fromIndex] = false

    moles[toIndex] = true
    moleTypes[toIndex] = 'moving'
    movingMoles[toIndex] = true

    this.setData({ moles, moleTypes, movingMoles, hitMoles, hammerAnim })
  },

  _hideMole(index) {
    if (!this.data.moles[index]) return
    const moles = [...this.data.moles]
    const hitMoles = [...this.data.hitMoles]
    const moleTypes = [...this.data.moleTypes]
    const hammerAnim = [...this.data.hammerAnim]
    const movingMoles = [...this.data.movingMoles]

    moles[index] = false
    hitMoles[index] = false
    moleTypes[index] = ''
    hammerAnim[index] = false
    movingMoles[index] = false
    this.setData({ moles, hitMoles, moleTypes, hammerAnim, movingMoles })
  },

  hitHole(e) {
    if (!this.data.gameActive) return

    const index = e.currentTarget.dataset.index
    if (!this.data.moles[index] || this.data.hitMoles[index]) return

    const hitMoles = [...this.data.hitMoles]
    const hammerAnim = [...this.data.hammerAnim]
    hitMoles[index] = true
    hammerAnim[index] = true

    const type = this.data.moleTypes[index]
    let scoreDelta = 1
    const update = { hitMoles, hammerAnim }

    if (type === 'bomb') {
      scoreDelta = -1
      update.bombCount = this.data.bombCount + 1
    } else if (type === 'gold') {
      scoreDelta = 2
      update.goldCount = this.data.goldCount + 1
      update.hitCount = this.data.hitCount + 1
    } else {
      update.hitCount = this.data.hitCount + 1
    }

    update.score = this.data.score + scoreDelta
    this.setData(update)

    if (this.data.hitCount >= TARGET_SCORE) {
      this._endGame(true)
      return
    }

    setTimeout(() => {
      this._hideMole(index)
    }, 400)
  },

  _endGame(passed) {
    this._clearAllTimers()
    const holeCount = this.data.holeCount

    if (passed) {
      const currentUnlocked = wx.getStorageSync('unlockedLevel') || 1
      const nextLevel = this.data.level + 1
      if (nextLevel > currentUnlocked) {
        wx.setStorageSync('unlockedLevel', nextLevel)
      }
    }

    this.setData({
      gameActive: false,
      gameOver: true,
      passed,
      timeLeft: passed ? this.data.timeLeft : 0,
      moles: makeEmpty(holeCount),
      moleTypes: new Array(holeCount).fill(''),
      hammerAnim: makeEmpty(holeCount),
      movingMoles: makeEmpty(holeCount)
    })
  },

  goBack() {
    wx.navigateBack()
  },

  _clearAllTimers() {
    if (this._timerInterval) {
      clearInterval(this._timerInterval)
      this._timerInterval = null
    }
    if (this._spawnTimeout) {
      clearTimeout(this._spawnTimeout)
      this._spawnTimeout = null
    }
    this._moleTimeouts.forEach(t => clearTimeout(t))
    this._moleTimeouts = []
  },

  onUnload() {
    this._clearAllTimers()
  }
})
