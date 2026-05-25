# Whack-a-Mole WeChat Mini-Program Design

## Overview

A whack-a-mole game built as a WeChat mini-program. Players tap moles as they pop up from holes within a time limit.

## Requirements

- 12 holes arranged in a 4x3 grid
- Moles appear randomly for 2 seconds before hiding
- Multiple moles can appear simultaneously
- 30-second countdown timer
- Score tracking: +1 per successful hit
- Cartoon/cute visual style (emoji-based)
- Hit feedback animation

## Architecture

Single-page WeChat mini-program using WXML + CSS animations (no Canvas).

### File Structure

```
RobGame/
├── app.js
├── app.json
├── app.wxss
├── project.config.json
└── pages/
    └── game/
        ├── game.wxml
        ├── game.wxss
        ├── game.js
        └── game.json
```

## Game Logic

### State

- `score`: current score (integer)
- `timeLeft`: countdown seconds remaining
- `moles`: array of 12 booleans indicating which holes have a visible mole
- `hitMoles`: array of 12 booleans for hit animation state
- `gameActive`: whether game is running

### Flow

1. User taps "Start" button
2. Timer starts at 30s, counting down each second
3. Game loop spawns moles at random holes every ~1s
4. Each mole stays visible for 2s, then hides automatically
5. Tapping a visible mole: score +1, mole hides with hit animation
6. When timer reaches 0: game ends, show final score
7. User can tap "Play Again" to restart

### Mole Spawning

- Use `setTimeout` to spawn a new mole every 800-1200ms (randomized interval)
- Each mole has its own 2s timer before auto-hiding
- Max 3 moles visible simultaneously to keep difficulty manageable

## Visual Design

- Background: green gradient (grass)
- Holes: brown ellipses with inner shadow
- Moles: emoji character popping up from hole with CSS translateY animation
- Hit feedback: brief scale animation + star emoji
- Score/timer: top bar with large readable font
- Start button: centered, prominent

## Edge Cases

- Tapping an already-hit mole before it disappears: no double scoring
- Tapping an empty hole: no effect
- Multiple rapid taps: only first tap on each mole counts
