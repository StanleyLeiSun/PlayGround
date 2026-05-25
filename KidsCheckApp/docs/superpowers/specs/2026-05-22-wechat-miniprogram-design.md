# WeChat Mini-Program Design Spec

## Overview

Develop a WeChat mini-program that replicates the "Today's Tasks" and "Progress" screens from the Android client. Both grandparent (task check-in with photo) and parent (progress monitoring) roles are supported. Authentication uses WeChat login with first-time account binding.

## Target Users

- **Grandparent role**: Supervise and check in tasks (including photo upload)
- **Parent role**: View progress, review photos

Both roles see "Today's Tasks" and "Progress" tabs; the check-in action is available to both (matching existing Android behavior).

## Tech Stack

- Native WeChat Mini-Program (WXML + WXSS + JS)
- No additional framework (uni-app, Taro, etc.)
- Backend: Existing FastAPI server with 2 new endpoints added

## Backend Changes

### New Endpoints

#### `POST /api/auth/wechat-login`

Handles WeChat mini-program login flow.

**Request:**
```json
{ "code": "string (from wx.login())" }
```

**Logic:**
1. Call WeChat `jscode2session` API with appid + secret + code to get `openid`
2. Query User table for matching `wechat_openid`
3. If found: issue JWT, return token + user info
4. If not found: return binding prompt

**Response (bound user):**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer",
  "user": { "id": 1, "username": "grandpa", "role": "grandparent" }
}
```

**Response (unbound):**
```json
{ "need_binding": true, "openid": "wx_openid_string" }
```

#### `POST /api/auth/wechat-bind`

Binds a WeChat openid to an existing account.

**Request:**
```json
{
  "openid": "string",
  "username": "string",
  "password": "string"
}
```

**Logic:**
1. Verify username + password against existing user
2. Store openid in `user.wechat_openid`
3. Issue JWT

**Response:** Same as successful wechat-login.

### Database Migration

Add column to `user` table:
- `wechat_openid`: String(128), nullable, unique index

### Configuration

New environment variables in `app/config.py`:
- `WX_APP_ID`: WeChat mini-program App ID
- `WX_APP_SECRET`: WeChat mini-program App Secret

## Mini-Program Architecture

### Project Structure

```
miniprogram/
├── app.js              # Global: silent login attempt on launch
├── app.json            # Page registration, tabBar config
├── app.wxss            # Global styles (colors match Android)
├── utils/
│   ├── api.js          # wx.request wrapper with auth header, 401 handling
│   └── auth.js         # Login/bind/token storage logic
├── pages/
│   ├── login/          # Login & account binding page
│   │   ├── login.wxml
│   │   ├── login.wxss
│   │   └── login.js
│   ├── tasks/          # Today's tasks page
│   │   ├── tasks.wxml
│   │   ├── tasks.wxss
│   │   └── tasks.js
│   └── progress/       # Progress page
│       ├── progress.wxml
│       ├── progress.wxss
│       └── progress.js
└── components/
    └── child-selector/ # Child switching component
        ├── child-selector.wxml
        ├── child-selector.wxss
        ├── child-selector.js
        └── child-selector.json
```

### Pages

#### Login Page (`pages/login/login`)

- On load: call `wx.login()` → send code to `/api/auth/wechat-login`
- If already bound: auto-navigate to tasks page
- If needs binding: show username/password form, call `/api/auth/wechat-bind`
- Token stored via `wx.setStorageSync('token', ...)`

#### Tasks Page (`pages/tasks/tasks`)

- Top: child-selector component (if multiple children)
- List divided into two sections: required tasks and conditional tasks
- Each task card shows: title, description, type badge (photo required), points, completion status
- Tap incomplete task → show `wx.showActionSheet`:
  - Photo-required tasks: options "Take Photo" / "Choose from Album"
  - Non-photo tasks: direct confirm dialog
- Photo flow: `wx.chooseMedia` → `wx.compressImage` (if > 1MB) → `wx.uploadFile` to check-in endpoint
- After successful check-in: celebration animation, refresh task list

#### Progress Page (`pages/progress/progress`)

- Top: child-selector component
- Date navigation: left/right arrows to browse days
- Progress bar: completed/total with percentage
- Timeline: sorted tasks with completion time, submitter name
- Photo chips: tap to call `wx.previewImage` for native full-screen preview
- Bottom card: today's points earned + cumulative points (gradient background)

### Components

#### Child Selector (`components/child-selector`)

- Fetches children list from `/api/children` on mount
- Displays current child name; tap to show picker
- Emits `bindchange` event with selected `childId`
- Stores last selected child in local storage

### Utilities

#### `utils/api.js`

```javascript
// Wraps wx.request with:
// - Base URL configuration
// - Automatic Authorization header injection
// - 401 response → clear token → redirect to login
// - Promise-based interface
```

#### `utils/auth.js`

```javascript
// Exports:
// - silentLogin(): wx.login → wechat-login API → store token or redirect
// - bind(openid, username, password): call wechat-bind → store token
// - getToken(): read from storage
// - clearToken(): remove from storage
// - isLoggedIn(): check token exists
```

## API Endpoints Used

| Feature | Endpoint | Method |
|---------|----------|--------|
| WeChat login | `/api/auth/wechat-login` | POST |
| Bind account | `/api/auth/wechat-bind` | POST |
| Get children | `/api/children` | GET |
| Get daily tasks | `/api/daily-tasks/{childId}/{date}` | GET |
| Check in (with photo) | `/api/daily-tasks/{taskId}/check-in` | POST |
| Get progress | `/api/progress/{childId}/{date}` | GET |

## Styling

Match Android client's color scheme:
- Primary: `#FF9800` (orange)
- Success: `#4CAF50` (green)
- Warning: `#FF5722`
- Text Primary: `#1a1a1a`
- Text Secondary: `#666666`
- Border: `#E0E0E0`
- Background: `#F5F5F5`

## Deployment Notes

- Mini-program directory `miniprogram/` sits at project root alongside `android/` and `backend/`
- Backend needs WX_APP_ID and WX_APP_SECRET environment variables on production server
- **HTTPS required**: WeChat mini-programs only allow HTTPS request domains. The current production server (`http://47.94.167.238`) needs either:
  - A domain name with SSL certificate (e.g., Let's Encrypt via nginx)
  - Or use WeChat developer tools' "Do not verify domain" option during development only
- Register the server domain in WeChat developer console under "Server Domain" (must be a domain, not IP)
- During development, use WeChat DevTools with domain verification disabled to test against HTTP backend

## Out of Scope (for this iteration)

- Template management (parent-only, stays in Android)
- Rewards system
- Push notifications
- Offline caching
- Ad-hoc task creation (stays in Android for now)
