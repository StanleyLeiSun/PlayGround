# WeChat Mini-Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a WeChat mini-program replicating "Today's Tasks" and "Progress" screens, with WeChat login + existing account binding.

**Architecture:** Backend adds 2 new auth endpoints (wechat-login, wechat-bind) and a `wechat_openid` column to User. Mini-program is native WXML/WXSS/JS, consuming the same REST API as Android. Token-based auth with JWT stored in wx storage.

**Tech Stack:** FastAPI (backend), Native WeChat Mini-Program (WXML + WXSS + JS), SQLite + Alembic migrations

---

## File Structure

### Backend (modified)

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/config.py` | Modify | Add WX_APP_ID, WX_APP_SECRET |
| `backend/app/models/models.py` | Modify | Add `wechat_openid` to User |
| `backend/app/schemas/schemas.py` | Modify | Add WechatLoginRequest, WechatBindRequest |
| `backend/app/services/auth_service.py` | Modify | Add wechat_login, wechat_bind functions |
| `backend/app/routers/auth.py` | Modify | Add /wechat-login, /wechat-bind endpoints |
| `backend/alembic/versions/xxx_add_wechat_openid.py` | Create | Migration for wechat_openid column |
| `backend/tests/test_wechat_auth.py` | Create | Tests for WeChat auth flow |

### Mini-Program (new)

| File | Responsibility |
|------|----------------|
| `miniprogram/app.js` | Global state, silent login on launch |
| `miniprogram/app.json` | Pages, tabBar, window config |
| `miniprogram/app.wxss` | Global styles, color variables |
| `miniprogram/project.config.json` | WeChat DevTools project config |
| `miniprogram/utils/api.js` | HTTP request wrapper with auth |
| `miniprogram/utils/auth.js` | Login/bind/token logic |
| `miniprogram/pages/login/login.js` | Login page logic |
| `miniprogram/pages/login/login.wxml` | Login page template |
| `miniprogram/pages/login/login.wxss` | Login page styles |
| `miniprogram/pages/login/login.json` | Login page config |
| `miniprogram/pages/tasks/tasks.js` | Tasks page logic |
| `miniprogram/pages/tasks/tasks.wxml` | Tasks page template |
| `miniprogram/pages/tasks/tasks.wxss` | Tasks page styles |
| `miniprogram/pages/tasks/tasks.json` | Tasks page config |
| `miniprogram/pages/progress/progress.js` | Progress page logic |
| `miniprogram/pages/progress/progress.wxml` | Progress page template |
| `miniprogram/pages/progress/progress.wxss` | Progress page styles |
| `miniprogram/pages/progress/progress.json` | Progress page config |
| `miniprogram/components/child-selector/child-selector.js` | Child switch logic |
| `miniprogram/components/child-selector/child-selector.wxml` | Child switch template |
| `miniprogram/components/child-selector/child-selector.wxss` | Child switch styles |
| `miniprogram/components/child-selector/child-selector.json` | Component config |

---

## Task 1: Backend — Add WeChat config and User model change

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/app/models/models.py`

- [ ] **Step 1: Add WeChat config vars**

In `backend/app/config.py`, add after the LLM_MODEL line:

```python
# WeChat Mini-Program
WX_APP_ID = os.getenv("WX_APP_ID", "")
WX_APP_SECRET = os.getenv("WX_APP_SECRET", "")
```

- [ ] **Step 2: Add wechat_openid to User model**

In `backend/app/models/models.py`, add to the User class after `role`:

```python
    wechat_openid = Column(String(128), unique=True, nullable=True)
```

- [ ] **Step 3: Create Alembic migration**

Run:
```bash
cd backend && ./.venv/bin/python -m alembic revision --autogenerate -m "add wechat_openid to user"
```

Verify the generated migration has:
```python
def upgrade() -> None:
    op.add_column('user', sa.Column('wechat_openid', sa.String(length=128), nullable=True))
    op.create_unique_constraint('uq_user_wechat_openid', 'user', ['wechat_openid'])
```

- [ ] **Step 4: Run migration locally**

```bash
cd backend && ./.venv/bin/python -m alembic upgrade head
```

Expected: No errors, migration applied.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/models/models.py backend/alembic/versions/
git commit -m "feat: add wechat_openid to User model and WX config"
```

---

## Task 2: Backend — WeChat auth schemas and service

**Files:**
- Modify: `backend/app/schemas/schemas.py`
- Modify: `backend/app/services/auth_service.py`

- [ ] **Step 1: Add WeChat schemas**

In `backend/app/schemas/schemas.py`, add after `LoginRequest`:

```python
class WechatLoginRequest(BaseModel):
    code: str

class WechatBindRequest(BaseModel):
    openid: str
    username: str
    password: str
```

- [ ] **Step 2: Add httpx to requirements**

`httpx` is already in `requirements.txt` — no change needed. Verify:
```bash
grep httpx backend/requirements.txt
```
Expected: `httpx>=0.27.0`

- [ ] **Step 3: Add wechat_login to auth_service**

In `backend/app/services/auth_service.py`, add these imports at the top:

```python
import httpx
from app.config import WX_APP_ID, WX_APP_SECRET
```

Then add after the `login` function:

```python
async def wechat_login(db: AsyncSession, code: str) -> dict:
    """Exchange wx code for openid, then check if user is bound."""
    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": WX_APP_ID,
        "secret": WX_APP_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
    data = resp.json()
    openid = data.get("openid")
    if not openid:
        return {"error": data.get("errmsg", "WeChat login failed")}

    result = await db.execute(select(User).where(User.wechat_openid == openid))
    user = result.scalar_one_or_none()
    if user:
        token = create_token(user.id, user.role.value)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {"id": user.id, "username": user.username, "role": user.role.value},
        }
    return {"need_binding": True, "openid": openid}


async def wechat_bind(db: AsyncSession, openid: str, username: str, password: str) -> dict | None:
    """Bind wechat openid to existing account after verifying credentials."""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or user.password_hash != password:
        return None
    user.wechat_openid = openid
    await db.flush()
    token = create_token(user.id, user.role.value)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "role": user.role.value},
    }
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/schemas.py backend/app/services/auth_service.py
git commit -m "feat: add wechat login/bind service and schemas"
```

---

## Task 3: Backend — WeChat auth endpoints and tests

**Files:**
- Modify: `backend/app/routers/auth.py`
- Create: `backend/tests/test_wechat_auth.py`

- [ ] **Step 1: Add endpoints to auth router**

In `backend/app/routers/auth.py`, add imports:

```python
from app.schemas.schemas import LoginRequest, TokenResponse, UserResponse, WechatLoginRequest, WechatBindRequest
```

Then add after the `/me` endpoint:

```python
@router.post("/wechat-login")
async def wechat_login(req: WechatLoginRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.wechat_login(db, req.code)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/wechat-bind")
async def wechat_bind(req: WechatBindRequest, db: AsyncSession = Depends(get_db)):
    result = await auth_service.wechat_bind(db, req.openid, req.username, req.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    await log_action(db, result["user"]["id"], "wechat_bind")
    return result
```

- [ ] **Step 2: Write test for wechat-bind endpoint**

Create `backend/tests/test_wechat_auth.py`:

```python
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import TestSession, auth_header
from app.models.models import User, UserRole


@pytest_asyncio.fixture
async def seed_wx_user():
    async with TestSession() as db:
        u = User(username="yeye_wx", password_hash="123456", role=UserRole.grandparent)
        db.add(u)
        await db.commit()
        await db.refresh(u)
        return u


@pytest.mark.asyncio
async def test_wechat_bind_success(seed_wx_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/wechat-bind", json={
            "openid": "test_openid_123",
            "username": "yeye_wx",
            "password": "123456",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == "yeye_wx"
    assert data["user"]["role"] == "grandparent"


@pytest.mark.asyncio
async def test_wechat_bind_wrong_password(seed_wx_user):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/wechat-bind", json={
            "openid": "test_openid_456",
            "username": "yeye_wx",
            "password": "wrong_password",
        })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wechat_bind_then_login(seed_wx_user):
    """After binding, the openid should be associated with the user."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First bind
        resp = await client.post("/api/auth/wechat-bind", json={
            "openid": "test_openid_789",
            "username": "yeye_wx",
            "password": "123456",
        })
        assert resp.status_code == 200

        # Verify user has openid in DB
        from sqlalchemy import select
        async with TestSession() as db:
            result = await db.execute(select(User).where(User.username == "yeye_wx"))
            user = result.scalar_one()
            assert user.wechat_openid == "test_openid_789"
```

- [ ] **Step 3: Run tests**

```bash
cd backend && ./.venv/bin/python -m pytest tests/test_wechat_auth.py -v
```

Expected: 3 tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/auth.py backend/tests/test_wechat_auth.py
git commit -m "feat: add wechat-login and wechat-bind API endpoints"
```

---

## Task 4: Mini-Program — Project scaffold and utilities

**Files:**
- Create: `miniprogram/app.json`
- Create: `miniprogram/app.js`
- Create: `miniprogram/app.wxss`
- Create: `miniprogram/project.config.json`
- Create: `miniprogram/utils/api.js`
- Create: `miniprogram/utils/auth.js`

- [ ] **Step 1: Create project config**

Create `miniprogram/project.config.json`:

```json
{
  "description": "KidsCheck WeChat Mini-Program",
  "packOptions": {
    "ignore": [],
    "include": []
  },
  "setting": {
    "bundle": false,
    "userConfirmedBundleSwitch": false,
    "urlCheck": false,
    "scopeDataCheck": false,
    "coverView": true,
    "es6": true,
    "postcss": true,
    "compileHotReLoad": false,
    "lazyloadPlaceholderEnable": false,
    "preloadBackgroundData": false,
    "minified": true,
    "autoAudits": false,
    "newFeature": false,
    "uglifyFileName": false,
    "uploadWithSourceMap": true,
    "enhance": true,
    "showShadowRootInWxmlPanel": true,
    "packNpmManually": false,
    "packNpmRelationList": [],
    "minifyWXSS": true,
    "showES6CompileOption": false,
    "checkInvalidKey": true,
    "babelSetting": {
      "ignore": [],
      "disablePlugins": [],
      "outputPath": ""
    }
  },
  "compileType": "miniprogram",
  "condition": {},
  "appid": "",
  "projectname": "kidscheck-miniprogram",
  "libVersion": "3.3.4",
  "srcMiniprogramRoot": ""
}
```

- [ ] **Step 2: Create app.json**

Create `miniprogram/app.json`:

```json
{
  "pages": [
    "pages/tasks/tasks",
    "pages/progress/progress",
    "pages/login/login"
  ],
  "window": {
    "navigationBarBackgroundColor": "#FF9800",
    "navigationBarTitleText": "KidsCheck",
    "navigationBarTextStyle": "white",
    "backgroundColor": "#F5F5F5"
  },
  "tabBar": {
    "color": "#666666",
    "selectedColor": "#FF9800",
    "backgroundColor": "#ffffff",
    "borderStyle": "black",
    "list": [
      {
        "pagePath": "pages/tasks/tasks",
        "text": "今日任务",
        "iconPath": "assets/tab-tasks.png",
        "selectedIconPath": "assets/tab-tasks-active.png"
      },
      {
        "pagePath": "pages/progress/progress",
        "text": "进度",
        "iconPath": "assets/tab-progress.png",
        "selectedIconPath": "assets/tab-progress-active.png"
      }
    ]
  },
  "style": "v2",
  "sitemapLocation": "sitemap.json"
}
```

- [ ] **Step 3: Create app.wxss**

Create `miniprogram/app.wxss`:

```css
page {
  --primary: #FF9800;
  --primary-light: #FFF3E0;
  --success: #4CAF50;
  --success-light: #E8F5E9;
  --warning: #FF5722;
  --warning-light: #FBE9E7;
  --text-primary: #1a1a1a;
  --text-secondary: #666666;
  --border: #E0E0E0;
  --bg: #F5F5F5;
  --gray: #999999;
  --gray-light: #F5F5F5;

  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background-color: var(--bg);
  color: var(--text-primary);
  font-size: 28rpx;
}

.container {
  padding: 24rpx;
}

.card {
  background: #fff;
  border-radius: 24rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.04);
}
```

- [ ] **Step 4: Create utils/api.js**

Create `miniprogram/utils/api.js`:

```javascript
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
```

- [ ] **Step 5: Create utils/auth.js**

Create `miniprogram/utils/auth.js`:

```javascript
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
```

- [ ] **Step 6: Create app.js**

Create `miniprogram/app.js`:

```javascript
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
```

- [ ] **Step 7: Create sitemap.json**

Create `miniprogram/sitemap.json`:

```json
{
  "desc": "关于本文件的更多信息，请参考文档",
  "rules": [{
    "action": "disallow",
    "page": "*"
  }]
}
```

- [ ] **Step 8: Commit**

```bash
git add miniprogram/
git commit -m "feat: scaffold miniprogram with utils and global config"
```

---

## Task 5: Mini-Program — Login page

**Files:**
- Create: `miniprogram/pages/login/login.json`
- Create: `miniprogram/pages/login/login.wxml`
- Create: `miniprogram/pages/login/login.wxss`
- Create: `miniprogram/pages/login/login.js`

- [ ] **Step 1: Create login.json**

```json
{
  "navigationBarTitleText": "登录"
}
```

- [ ] **Step 2: Create login.wxml**

```xml
<view class="login-page">
  <view class="logo-section">
    <text class="logo-text">KidsCheck</text>
    <text class="subtitle">家庭学习打卡</text>
  </view>

  <view class="form-section" wx:if="{{showBindForm}}">
    <view class="hint">首次使用，请绑定已有账号</view>
    <input
      class="input"
      placeholder="用户名"
      value="{{username}}"
      bindinput="onUsernameInput"
    />
    <input
      class="input"
      placeholder="密码"
      password="{{true}}"
      value="{{password}}"
      bindinput="onPasswordInput"
    />
    <button class="btn-primary" bindtap="onBind" loading="{{loading}}">
      绑定并登录
    </button>
    <view class="error" wx:if="{{errorMsg}}">{{errorMsg}}</view>
  </view>

  <view class="loading-section" wx:else>
    <view class="loading-text">正在登录...</view>
  </view>
</view>
```

- [ ] **Step 3: Create login.wxss**

```css
.login-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 120rpx 48rpx 48rpx;
  min-height: 100vh;
  background: #fff;
}

.logo-section {
  text-align: center;
  margin-bottom: 80rpx;
}

.logo-text {
  font-size: 56rpx;
  font-weight: bold;
  color: var(--primary);
  display: block;
}

.subtitle {
  font-size: 28rpx;
  color: var(--text-secondary);
  margin-top: 12rpx;
  display: block;
}

.form-section {
  width: 100%;
}

.hint {
  font-size: 28rpx;
  color: var(--text-secondary);
  margin-bottom: 32rpx;
  text-align: center;
}

.input {
  width: 100%;
  height: 88rpx;
  border: 2rpx solid var(--border);
  border-radius: 16rpx;
  padding: 0 24rpx;
  margin-bottom: 24rpx;
  font-size: 30rpx;
  box-sizing: border-box;
}

.btn-primary {
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  background: var(--primary);
  color: #fff;
  border-radius: 16rpx;
  font-size: 32rpx;
  font-weight: 600;
  border: none;
  margin-top: 16rpx;
}

.error {
  color: var(--warning);
  font-size: 26rpx;
  text-align: center;
  margin-top: 24rpx;
}

.loading-section {
  margin-top: 120rpx;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 30rpx;
}
```

- [ ] **Step 4: Create login.js**

```javascript
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
```

- [ ] **Step 5: Commit**

```bash
git add miniprogram/pages/login/
git commit -m "feat: add miniprogram login page with wechat bind flow"
```

---

## Task 6: Mini-Program — Child selector component

**Files:**
- Create: `miniprogram/components/child-selector/child-selector.json`
- Create: `miniprogram/components/child-selector/child-selector.wxml`
- Create: `miniprogram/components/child-selector/child-selector.wxss`
- Create: `miniprogram/components/child-selector/child-selector.js`

- [ ] **Step 1: Create child-selector.json**

```json
{
  "component": true
}
```

- [ ] **Step 2: Create child-selector.wxml**

```xml
<view class="child-selector" bindtap="onTap">
  <text class="child-name">{{currentChild.name || '选择孩子'}}</text>
  <text class="arrow">▾</text>
</view>

<view class="picker-mask" wx:if="{{showPicker}}" bindtap="closePicker">
  <view class="picker-content" catchtap>
    <view
      class="picker-item {{item.id === currentChild.id ? 'active' : ''}}"
      wx:for="{{children}}"
      wx:key="id"
      bindtap="onSelect"
      data-child="{{item}}"
    >
      <text>{{item.name}}</text>
      <text wx:if="{{item.nickname}}" class="nickname">（{{item.nickname}}）</text>
    </view>
  </view>
</view>
```

- [ ] **Step 3: Create child-selector.wxss**

```css
.child-selector {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 24rpx;
  background: #fff;
  border-radius: 32rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.06);
}

.child-name {
  font-size: 30rpx;
  font-weight: 600;
  color: var(--text-primary);
}

.arrow {
  margin-left: 8rpx;
  font-size: 24rpx;
  color: var(--gray);
}

.picker-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  z-index: 999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.picker-content {
  background: #fff;
  border-radius: 24rpx;
  padding: 24rpx;
  width: 60%;
}

.picker-item {
  padding: 24rpx;
  border-radius: 12rpx;
  font-size: 30rpx;
  text-align: center;
}

.picker-item.active {
  background: var(--primary-light);
  color: var(--primary);
  font-weight: 600;
}

.nickname {
  font-size: 26rpx;
  color: var(--text-secondary);
}
```

- [ ] **Step 4: Create child-selector.js**

```javascript
const { request } = require('../../utils/api')

Component({
  properties: {},

  data: {
    children: [],
    currentChild: {},
    showPicker: false
  },

  lifetimes: {
    attached() {
      this.loadChildren()
    }
  },

  methods: {
    loadChildren() {
      request({ url: '/api/children' }).then(children => {
        const savedId = wx.getStorageSync('selectedChildId')
        const current = children.find(c => c.id === savedId) || children[0] || {}
        this.setData({ children, currentChild: current })
        if (current.id) {
          wx.setStorageSync('selectedChildId', current.id)
          this.triggerEvent('change', { childId: current.id })
        }
      }).catch(() => {})
    },

    onTap() {
      if (this.data.children.length > 1) {
        this.setData({ showPicker: true })
      }
    },

    closePicker() {
      this.setData({ showPicker: false })
    },

    onSelect(e) {
      const child = e.currentTarget.dataset.child
      wx.setStorageSync('selectedChildId', child.id)
      this.setData({ currentChild: child, showPicker: false })
      this.triggerEvent('change', { childId: child.id })
    }
  }
})
```

- [ ] **Step 5: Commit**

```bash
git add miniprogram/components/
git commit -m "feat: add child-selector component"
```

---

## Task 7: Mini-Program — Tasks page

**Files:**
- Create: `miniprogram/pages/tasks/tasks.json`
- Create: `miniprogram/pages/tasks/tasks.wxml`
- Create: `miniprogram/pages/tasks/tasks.wxss`
- Create: `miniprogram/pages/tasks/tasks.js`

- [ ] **Step 1: Create tasks.json**

```json
{
  "navigationBarTitleText": "今日任务",
  "usingComponents": {
    "child-selector": "/components/child-selector/child-selector"
  }
}
```

- [ ] **Step 2: Create tasks.wxml**

```xml
<view class="container">
  <view class="header">
    <child-selector bindchange="onChildChange" />
  </view>

  <view wx:if="{{loading}}" class="loading">
    <text>加载中...</text>
  </view>

  <view wx:elif="{{tasks.length === 0}}" class="empty">
    <text class="empty-text">今天没有任务</text>
    <text class="empty-hint">请家长在模板管理中添加任务</text>
  </view>

  <view wx:else>
    <!-- Required tasks -->
    <view class="section-title">📋 必做任务</view>
    <view
      class="task-card {{item.status === 'done' ? 'done' : ''}}"
      wx:for="{{requiredTasks}}"
      wx:key="id"
      bindtap="onTaskTap"
      data-task="{{item}}"
    >
      <view class="task-status">
        <view class="circle {{item.status === 'done' ? 'circle-done' : ''}}">
          <text wx:if="{{item.status === 'done'}}" class="check">✓</text>
        </view>
      </view>
      <view class="task-info">
        <text class="task-title">{{item.title}}</text>
        <text wx:if="{{item.description}}" class="task-desc">{{item.description}}</text>
        <view class="task-tags">
          <text wx:if="{{item.type === 'written'}}" class="tag tag-photo">📷 拍照</text>
        </view>
      </view>
      <text class="task-points">+{{item.points}}分</text>
    </view>

    <!-- Conditional tasks -->
    <view class="section-title">🌟 条件任务{{hasUncompletedRequired ? '（完成后解锁）' : ''}}</view>
    <view
      class="task-card {{item.status === 'done' ? 'done' : ''}}"
      wx:for="{{conditionalTasks}}"
      wx:key="id"
      bindtap="onTaskTap"
      data-task="{{item}}"
    >
      <view class="task-status">
        <view class="circle {{item.status === 'done' ? 'circle-done' : ''}}">
          <text wx:if="{{item.status === 'done'}}" class="check">✓</text>
        </view>
      </view>
      <view class="task-info">
        <text class="task-title">{{item.title}}</text>
        <text wx:if="{{item.description}}" class="task-desc">{{item.description}}</text>
        <view class="task-tags">
          <text wx:if="{{item.type === 'written'}}" class="tag tag-photo">📷 拍照</text>
        </view>
      </view>
      <text class="task-points">+{{item.points}}分</text>
    </view>
  </view>
</view>
```

- [ ] **Step 3: Create tasks.wxss**

```css
.header {
  display: flex;
  justify-content: center;
  margin-bottom: 24rpx;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 200rpx;
}

.empty-text {
  font-size: 34rpx;
  font-weight: 500;
  color: var(--gray);
}

.empty-hint {
  font-size: 26rpx;
  color: var(--text-secondary);
  margin-top: 12rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 24rpx 0 12rpx;
}

.task-card {
  display: flex;
  align-items: center;
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx 24rpx;
  margin-bottom: 16rpx;
  border: 3rpx solid var(--border);
}

.task-card.done {
  background: var(--success-light);
  border-color: var(--success);
}

.task-status {
  margin-right: 20rpx;
}

.circle {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 4rpx solid var(--gray);
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-done {
  background: var(--success);
  border-color: var(--success);
}

.check {
  color: #fff;
  font-size: 28rpx;
  font-weight: bold;
}

.task-info {
  flex: 1;
}

.task-title {
  font-size: 32rpx;
  font-weight: 600;
  display: block;
}

.task-desc {
  font-size: 24rpx;
  color: var(--gray);
  margin-top: 4rpx;
  display: block;
}

.task-tags {
  margin-top: 8rpx;
}

.tag {
  display: inline-block;
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 16rpx;
}

.tag-photo {
  background: var(--primary-light);
  color: var(--primary);
}

.task-points {
  font-size: 28rpx;
  font-weight: bold;
  color: var(--primary);
}
```

- [ ] **Step 4: Create tasks.js**

```javascript
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
```

- [ ] **Step 5: Commit**

```bash
git add miniprogram/pages/tasks/
git commit -m "feat: add miniprogram tasks page with check-in and photo upload"
```

---

## Task 8: Mini-Program — Progress page

**Files:**
- Create: `miniprogram/pages/progress/progress.json`
- Create: `miniprogram/pages/progress/progress.wxml`
- Create: `miniprogram/pages/progress/progress.wxss`
- Create: `miniprogram/pages/progress/progress.js`

- [ ] **Step 1: Create progress.json**

```json
{
  "navigationBarTitleText": "进度",
  "usingComponents": {
    "child-selector": "/components/child-selector/child-selector"
  }
}
```

- [ ] **Step 2: Create progress.wxml**

```xml
<view class="container">
  <view class="header">
    <child-selector bindchange="onChildChange" />
  </view>

  <!-- Date navigation -->
  <view class="date-nav">
    <view class="nav-btn" bindtap="prevDay">◀</view>
    <text class="date-text">{{displayDate}}</text>
    <view class="nav-btn" bindtap="nextDay">▶</view>
  </view>

  <view wx:if="{{loading}}" class="loading">
    <text>加载中...</text>
  </view>

  <view wx:elif="{{progress}}">
    <!-- Progress bar -->
    <view class="card">
      <view class="progress-header">
        <text class="progress-label">完成进度</text>
        <text class="progress-count">{{progress.completed_tasks}}/{{progress.total_tasks}}</text>
      </view>
      <view class="progress-bar-bg">
        <view class="progress-bar-fill" style="width: {{progressPercent}}%"></view>
      </view>
    </view>

    <!-- Timeline -->
    <view class="section-title">📅 时间线</view>

    <view wx:if="{{progress.tasks.length === 0}}" class="empty">
      <text class="empty-text">当天没有任务</text>
    </view>

    <view wx:else class="timeline">
      <view class="timeline-item" wx:for="{{sortedTasks}}" wx:key="id">
        <view class="timeline-dot {{item.status === 'done' ? 'dot-done' : ''}}"></view>
        <view class="timeline-line" wx:if="{{index < sortedTasks.length - 1}}"></view>
        <view class="timeline-content">
          <text class="timeline-time">{{item.timeText}}</text>
          <text class="timeline-title {{item.status === 'done' ? '' : 'text-gray'}}">{{item.title}}</text>
          <view
            wx:if="{{item.photos.length > 0}}"
            class="photo-chip"
            bindtap="viewPhotos"
            data-photos="{{item.photoUrls}}"
          >
            <text>📷 查看照片</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Points summary -->
    <view class="points-card">
      <view class="points-col">
        <text class="points-label">今日获得</text>
        <text class="points-value">+{{progress.today_points}} 分</text>
      </view>
      <view class="points-col points-right">
        <text class="points-label">累计积分</text>
        <text class="points-value">{{progress.cumulative_points}} 分</text>
      </view>
    </view>
  </view>
</view>
```

- [ ] **Step 3: Create progress.wxss**

```css
.header {
  display: flex;
  justify-content: center;
  margin-bottom: 16rpx;
}

.date-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.nav-btn {
  padding: 12rpx 24rpx;
  font-size: 28rpx;
  color: var(--text-secondary);
}

.date-text {
  font-size: 30rpx;
  font-weight: 600;
  margin: 0 24rpx;
}

.loading, .empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 100rpx;
}

.empty-text {
  font-size: 30rpx;
  color: var(--gray);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.progress-label, .progress-count {
  font-size: 26rpx;
  color: var(--text-secondary);
}

.progress-bar-bg {
  height: 20rpx;
  background: var(--border);
  border-radius: 10rpx;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--primary);
  border-radius: 10rpx;
  transition: width 0.3s;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 24rpx 0 16rpx;
}

.timeline {
  padding-left: 24rpx;
}

.timeline-item {
  display: flex;
  position: relative;
  padding-bottom: 32rpx;
  padding-left: 36rpx;
}

.timeline-dot {
  position: absolute;
  left: 0;
  top: 8rpx;
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  background: var(--gray);
}

.dot-done {
  background: var(--success);
}

.timeline-line {
  position: absolute;
  left: 8rpx;
  top: 32rpx;
  width: 4rpx;
  bottom: 0;
  background: var(--border);
}

.timeline-content {
  flex: 1;
}

.timeline-time {
  font-size: 26rpx;
  color: var(--text-secondary);
  display: block;
}

.timeline-title {
  font-size: 30rpx;
  font-weight: 500;
  display: block;
  margin-top: 4rpx;
}

.text-gray {
  color: var(--gray);
}

.photo-chip {
  display: inline-block;
  margin-top: 8rpx;
  padding: 8rpx 16rpx;
  background: var(--gray-light);
  border-radius: 16rpx;
  font-size: 24rpx;
  color: var(--text-secondary);
}

.points-card {
  display: flex;
  background: linear-gradient(90deg, var(--primary), #FFB74D);
  border-radius: 24rpx;
  padding: 32rpx;
  margin-top: 24rpx;
}

.points-col {
  flex: 1;
}

.points-right {
  text-align: right;
}

.points-label {
  font-size: 26rpx;
  color: rgba(255,255,255,0.85);
  display: block;
}

.points-value {
  font-size: 40rpx;
  font-weight: bold;
  color: #fff;
  display: block;
  margin-top: 8rpx;
}
```

- [ ] **Step 4: Create progress.js**

```javascript
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
```

- [ ] **Step 5: Commit**

```bash
git add miniprogram/pages/progress/
git commit -m "feat: add miniprogram progress page with timeline and photo preview"
```

---

## Task 9: Mini-Program — Tab bar icons and final wiring

**Files:**
- Create: `miniprogram/assets/` (tab icons)

- [ ] **Step 1: Create placeholder tab icons**

Since WeChat tabBar requires icon files, create simple SVG-converted PNGs. For development, create minimal placeholder files:

```bash
mkdir -p miniprogram/assets
```

Create 4 icon files (81x81px PNG recommended for tabBar). For now, use the WeChat DevTools' built-in icon generator or create simple colored squares as placeholders:

Create `miniprogram/assets/create-icons.md` with instructions:

```markdown
# Tab Bar Icons

Required icons (81x81px PNG, transparent background):

- `tab-tasks.png` — clipboard/checklist icon, gray (#999999)
- `tab-tasks-active.png` — clipboard/checklist icon, orange (#FF9800)
- `tab-progress.png` — chart/progress icon, gray (#999999)
- `tab-progress-active.png` — chart/progress icon, orange (#FF9800)

Generate using any icon tool or download from iconfont.cn
```

For WeChat DevTools to work without icons, temporarily update `app.json` to remove iconPath fields (DevTools will use text-only tabs):

Actually, tabBar requires icon files to exist. Create 1x1 pixel placeholder PNGs:

```bash
# Create minimal valid PNG files (1x1 pixel transparent)
python3 -c "
import struct, zlib
def create_png(path):
    sig = b'\\x89PNG\\r\\n\\x1a\\n'
    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 6, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    raw = b'\\x00\\x00\\x00\\x00\\x00'
    compressed = zlib.compress(raw)
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    with open(path, 'wb') as f:
        f.write(sig + ihdr + idat + iend)

for name in ['tab-tasks.png', 'tab-tasks-active.png', 'tab-progress.png', 'tab-progress-active.png']:
    create_png(f'miniprogram/assets/{name}')
print('Icons created')
"
```

- [ ] **Step 2: Verify project structure**

```bash
find miniprogram -type f | sort
```

Expected output should show all files from Tasks 4-9.

- [ ] **Step 3: Commit**

```bash
git add miniprogram/assets/
git commit -m "feat: add placeholder tab bar icons"
```

---

## Task 10: Backend — Deploy migration to production

**Files:**
- No new files

- [ ] **Step 1: Backup production database**

```bash
mkdir -p db_bak
scp admin@47.94.167.238:/opt/kidscheck/backend/kidscheck_dev.db "db_bak/kidscheck_$(date +%Y-%m-%d).db"
ls -la "db_bak/kidscheck_$(date +%Y-%m-%d).db"
```

Verify file size is non-zero.

- [ ] **Step 2: Upload backend code**

```bash
bash scripts/upload.sh <archive.tar.gz> admin@47.94.167.238
```

Or manually sync the backend directory and run migration:

```bash
scp -r backend/app backend/alembic admin@47.94.167.238:/tmp/kidscheck-update/
ssh admin@47.94.167.238 "sudo cp -r /tmp/kidscheck-update/app /opt/kidscheck/backend/ && sudo cp -r /tmp/kidscheck-update/alembic /opt/kidscheck/backend/"
```

- [ ] **Step 3: Run migration on production**

```bash
ssh admin@47.94.167.238 "cd /opt/kidscheck/backend && sudo /opt/kidscheck/venv/bin/python -m alembic upgrade head"
```

Expected: Migration applies successfully.

- [ ] **Step 4: Restart backend service**

```bash
ssh admin@47.94.167.238 "sudo systemctl restart kidscheck && sleep 2 && sudo systemctl is-active kidscheck"
```

Expected: `active`

- [ ] **Step 5: Set WeChat env vars on server**

```bash
ssh admin@47.94.167.238 "sudo tee -a /opt/kidscheck/backend/.env.dev > /dev/null << 'EOF'
WX_APP_ID=your_actual_appid
WX_APP_SECRET=your_actual_secret
EOF"
ssh admin@47.94.167.238 "sudo systemctl restart kidscheck"
```

Replace `your_actual_appid` and `your_actual_secret` with real values from WeChat developer console.

- [ ] **Step 6: Verify endpoints**

```bash
curl -s -X POST http://47.94.167.238/api/auth/wechat-bind \
  -H "Content-Type: application/json" \
  -d '{"openid":"test","username":"baba","password":"123456"}' | python3 -m json.tool
```

Expected: 200 with access_token (or actual credentials).

---

## Task 11: Integration test in WeChat DevTools

- [ ] **Step 1: Open project in WeChat DevTools**

Open WeChat Developer Tools → Import project → Select `miniprogram/` directory → Set AppID (or use test AppID).

- [ ] **Step 2: Disable domain verification**

In DevTools: Settings → Project → Uncheck "是否验证合法域名". This allows HTTP requests during development.

- [ ] **Step 3: Test login flow**

1. App launches → calls wx.login → sends code to backend
2. Backend returns `need_binding: true` (first time)
3. Enter valid username/password → tap "绑定并登录"
4. Should redirect to tasks tab

- [ ] **Step 4: Test tasks page**

1. Verify tasks load for selected child
2. Tap a non-photo task → confirm dialog → check in succeeds
3. Tap a photo task → action sheet → choose photo → upload succeeds
4. Task card updates to "done" state

- [ ] **Step 5: Test progress page**

1. Switch to progress tab
2. Verify progress bar shows correct counts
3. Navigate dates with arrows
4. Tap "查看照片" → native image preview opens
5. Points card shows correct values

- [ ] **Step 6: Test child switching**

1. Tap child selector
2. Switch to different child
3. Both tasks and progress pages reload with new child's data
