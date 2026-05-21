# Android客户端自动更新功能设计

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为KidsCheck Android客户端实现自动检测新版本并自动升级的功能，确保用户始终使用最新版本。

**Architecture:** 采用自建服务器方案，后端提供版本检查API和APK文件下载服务，客户端启动时检查版本并支持应用内下载和自动安装。

**Tech Stack:** FastAPI + SQLAlchemy (后端), Kotlin + Coroutines + Retrofit + DownloadManager (Android)

---

## 1. 整体架构

### 1.1 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Android App   │    │   FastAPI       │    │   File Storage  │
│   (Client)      │◄──►│   Backend       │◄──►│   (APK Files)   │
│                 │    │                 │    │                 │
│ - Version Check │    │ - Version API   │    │ - uploads/apk/  │
│ - APK Download  │    │ - File Serving  │    │ - version.json  │
│ - Auto Install  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 数据流

1. 应用启动 → 调用版本检查API
2. API返回最新版本信息（版本号、下载链接、更新日志、是否强制更新）
3. 客户端比较版本号，如果有新版本则显示对话框
4. 用户确认后，下载APK文件
5. 下载完成后，触发系统安装器

### 1.3 关键组件

- **后端**：版本检查API + APK文件服务
- **客户端**：版本检查器 + 下载管理器 + 安装器
- **存储**：APK文件目录 + 版本配置文件

---

## 2. 后端API设计

### 2.1 版本检查接口

**接口:** `GET /api/app/version`

**响应格式:**
```json
{
  "version_code": 2,
  "version_name": "1.1.0",
  "apk_url": "/api/app/download/1.1.0",
  "apk_size": 15728640,
  "apk_md5": "abc123def456...",
  "release_notes": "1. 修复了打卡bug\n2. 优化了界面",
  "force_update": false,
  "min_supported_version": 1
}
```

**字段说明:**
- `version_code`: 版本号（整数），用于版本比较
- `version_name`: 版本名称（字符串），用于显示
- `apk_url`: APK下载路径（相对路径）
- `apk_size`: APK文件大小（字节）
- `apk_md5`: APK文件MD5校验码
- `release_notes`: 更新日志（支持换行）
- `force_update`: 是否强制更新
- `min_supported_version`: 最低支持版本号，低于此版本强制更新

### 2.2 APK下载接口

**接口:** `GET /api/app/download/{version_name}`

**功能:**
- 返回APK文件流
- 支持断点续传（Range请求头）
- Content-Type: `application/vnd.android.package-archive`
- Content-Disposition: `attachment; filename="kidscheck-{version}.apk"`

### 2.3 版本信息存储

**方案:** 使用配置文件 `uploads/apk/version.json`

**结构:**
```json
{
  "version_code": 2,
  "version_name": "1.1.0",
  "apk_filename": "kidscheck-1.1.0.apk",
  "release_notes": "1. 修复了打卡bug\n2. 优化了界面",
  "force_update": false,
  "min_supported_version": 1,
  "created_at": "2026-05-21T10:00:00Z"
}
```

### 2.4 版本比较逻辑

```python
def need_update(server_version_code: int, client_version_code: int, 
                force_update: bool, min_supported_version: int) -> bool:
    if client_version_code >= server_version_code:
        return False  # 已是最新版本
    if force_update:
        return True  # 强制更新
    if client_version_code < min_supported_version:
        return True  # 低于最低支持版本
    return True  # 有新版本可选更新
```

---

## 3. Android客户端设计

### 3.1 核心组件

#### 3.1.1 AppVersionChecker - 版本检查器

**职责:**
- 启动时调用版本检查API
- 比较版本号，判断是否需要更新
- 处理网络异常和API错误

**接口:**
```kotlin
data class AppVersion(
    val versionCode: Int,
    val versionName: String,
    val apkUrl: String,
    val apkSize: Long,
    val apkMd5: String,
    val releaseNotes: String,
    val forceUpdate: Boolean,
    val minSupportedVersion: Int
)

interface VersionChecker {
    suspend fun checkForUpdate(): AppVersion?
    fun needUpdate(serverVersion: AppVersion): Boolean
}
```

#### 3.1.2 UpdateDialog - 更新对话框

**职责:**
- 显示版本号、更新日志、文件大小
- 强制更新：只能点击"立即更新"
- 可选更新：可以点击"稍后再说"
- 显示下载进度条

**Compose组件:**
```kotlin
@Composable
fun UpdateDialog(
    version: AppVersion,
    onUpdateClick: () -> Unit,
    onSkipClick: (() -> Unit)?,  // null表示强制更新
    onDismiss: () -> Unit
)
```

#### 3.1.3 ApkDownloader - APK下载器

**职责:**
- 使用Android DownloadManager（系统服务）
- 支持后台下载
- 显示通知栏进度
- 下载完成后触发安装

**接口:**
```kotlin
interface ApkDownloader {
    fun startDownload(apkUrl: String, versionName: String): Long
    fun getDownloadStatus(downloadId: Long): DownloadStatus
    fun registerReceiver(onComplete: (String) -> Unit, onProgress: (Int) -> Unit)
    fun unregisterReceiver()
}

data class DownloadStatus(
    val status: Int,  // DownloadManager.STATUS_RUNNING, STATUS_SUCCESSFUL, STATUS_FAILED
    val progress: Int,  // 0-100
    val localUri: String?
)
```

#### 3.1.4 ApkInstaller - APK安装器

**职责:**
- 请求安装未知来源应用的权限
- 调用系统PackageInstaller
- 处理安装成功/失败

**接口:**
```kotlin
interface ApkInstaller {
    fun installApk(context: Context, apkFile: File)
    fun canRequestPackageInstalls(context: Context): Boolean
    fun requestInstallPermission(activity: Activity)
}
```

### 3.2 MineScreen显示版本信息

**功能:**
- 在MineScreen（我的页面）底部显示当前应用版本
- 显示版本号（version_name）和版本代码（version_code）
- 提供"检查更新"按钮，手动触发版本检查

**UI设计:**
```
┌─────────────────────────────────┐
│ 🏠 萝卜蚕豆之家                 │
│ ┌──────┐ ┌──────┐              │
│ │ 萝卜 │ │ 蚕豆 │              │
│ │ 120分│ │ 85分 │              │
│ └──────┘ └──────┘              │
├─────────────────────────────────┤
│ 积分兑换                    >   │
│ 任务模板管理                >   │
│ 奖励库管理                  >   │
│ 设置                        >   │
├─────────────────────────────────┤
│ 退出登录 (爸爸)                 │
├─────────────────────────────────┤
│ 关于                            │
│ ┌─────────────────────────────┐ │
│ │ 版本：1.0.0 (1)            │ │
│ │ 检查更新                    │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

**实现:**
- 从`BuildConfig.VERSION_NAME`和`BuildConfig.VERSION_CODE`获取版本信息
- "检查更新"按钮复用版本检查逻辑
- 检查结果：已是最新 / 有新版本（弹出更新对话框）
- 位置：在"退出登录"按钮下方，作为独立的"关于"区域

### 3.3 权限需求

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
```

### 3.3 用户流程

```
应用启动
  ↓
调用版本检查API
  ↓
有新版本？ ──否──→ 正常启动
  ↓是
显示更新对话框
  ↓
强制更新？ ──是──→ 只能点击"立即更新"
  ↓否
用户选择"立即更新"或"稍后再说"
  ↓
开始下载（显示进度）
  ↓
下载完成 → 触发安装
  ↓
安装成功 → 重启应用
```

---

## 4. 错误处理和边界情况

### 4.1 网络错误处理

- **版本检查失败**: 静默失败，不影响正常启动
- **下载失败**: 提示用户重试，支持断点续传
- **超时处理**: 连接超时30秒，读取超时60秒

### 4.2 权限处理

- **首次安装未知来源应用**: 引导用户开启权限
- **权限被拒绝**: 提示用户手动开启
- **Android 8.0+**: 需要请求`REQUEST_INSTALL_PACKAGES`权限

### 4.3 存储空间不足

- 下载前检查存储空间
- 空间不足时提示用户清理
- 下载失败时清理临时文件

### 4.4 版本回退

- 如果本地版本比服务器版本新（开发调试场景），不提示更新
- 如果服务器版本低于最低支持版本，强制更新

### 4.5 并发处理

- 防止重复检查：应用启动时只检查一次
- 防止重复下载：如果正在下载，不触发新的下载
- **下载状态持久化**:
  - 使用DownloadManager（系统服务），下载状态由系统管理
  - 应用重启后，通过DownloadManager查询下载状态
  - 如果下载完成但未安装，触发安装
  - 如果下载失败，清理并提示用户重新下载
  - 下载ID存储在SharedPreferences中，用于状态查询

### 4.6 通知和后台

- 下载过程中显示通知栏进度
- 应用进入后台后继续下载
- 下载完成后发送通知提醒用户安装

---

## 5. 测试策略

### 5.1 后端测试

- 版本检查API单元测试
- APK文件下载测试（断点续传）
- 版本比较逻辑测试
- 并发下载测试

### 5.2 Android客户端测试

- 版本检查器单元测试
- 版本比较逻辑测试
- 下载管理器集成测试
- 安装权限处理测试

### 5.3 端到端测试

- 完整更新流程测试
- 网络异常场景测试
- 存储空间不足测试
- 权限拒绝场景测试

### 5.4 测试环境

- **开发环境**: 使用dev flavor，BASE_URL指向本地
- **测试环境**: 使用localProd flavor，测试版本检查
- **生产环境**: 使用prod flavor，正式发布

---

## 6. 部署和发布流程

### 6.1 APK发布流程

1. 构建新版本APK：`./gradlew assembleProdRelease`
2. 计算APK文件MD5
3. 更新 `uploads/apk/version.json`
4. 将APK文件复制到 `uploads/apk/` 目录
5. 提交版本信息到Git

### 6.2 版本号管理

- `version_code`: 每次发布递增（整数）
- `version_name`: 语义化版本（主版本.次版本.修订版本）
- **映射公式**: `version_code = 主版本 * 10000 + 次版本 * 100 + 修订版本`
  - 例如：1.1.0 → 10100, 1.2.3 → 10203, 2.0.0 → 20000
- **注意**: 主版本、次版本、修订版本各占2位数字，最大支持99

### 6.3 自动化发布（可选）

- GitHub Actions自动构建
- 自动上传到服务器
- 自动更新version.json

---

## 7. 安全考虑

### 7.1 传输安全

- 使用HTTPS传输APK文件
- 验证服务器证书

### 7.2 文件完整性验证

**验证流程:**
1. 下载完成后，读取APK文件
2. 计算文件的MD5哈希值（使用`java.security.MessageDigest`）
3. 与服务器返回的`apk_md5`比较
4. 如果不匹配，删除文件并提示用户重新下载
5. 如果匹配，触发安装

**实现代码示例:**
```kotlin
fun calculateMd5(file: File): String {
    val md = MessageDigest.getInstance("MD5")
    file.inputStream().buffered().use { input ->
        val buffer = ByteArray(8192)
        var read = input.read(buffer)
        while (read != -1) {
            md.update(buffer, 0, read)
            read = input.read(buffer)
        }
    }
    return md.digest().joinToString("") { "%02x".format(it) }
}

fun verifyApkIntegrity(apkFile: File, expectedMd5: String): Boolean {
    val actualMd5 = calculateMd5(apkFile)
    return actualMd5.equals(expectedMd5, ignoreCase = true)
}
```

### 7.3 权限最小化

- 只请求必要的权限
- 动态请求权限，不预先声明

---

## 8. 性能优化

### 8.1 版本检查优化

- 版本检查结果缓存（避免重复检查）
- 异步检查，不阻塞UI线程

### 8.2 下载优化

- 支持断点续传
- 后台下载，不阻塞应用使用
- 下载完成后通知用户

### 8.3 存储优化

- 下载完成后删除旧版本APK
- 清理下载失败的临时文件

---

## 9. 未来扩展

### 9.1 增量更新

- 使用bsdiff/bspatch生成增量包
- 减少下载文件大小

### 9.2 静默更新

- 后台下载并安装
- 用户无感知更新

### 9.3 灰度发布

- 按用户ID灰度发布
- 收集更新反馈

---

## 10. 总结

本设计方案采用自建服务器方案，实现简单、可控性强，适合KidsCheck这样的内部家庭应用。通过版本检查API、应用内下载和自动安装，确保用户始终使用最新版本，同时提供良好的用户体验。

**关键特性:**
- 应用启动时自动检查版本
- 支持强制更新和可选更新
- 应用内下载，显示进度
- 自动触发安装
- 支持断点续传
- 完善的错误处理

**技术栈:**
- 后端：FastAPI + SQLAlchemy
- Android：Kotlin + Coroutines + Retrofit + DownloadManager
- 存储：文件系统 + JSON配置

**预计工作量:**
- 后端：2-3天
- Android客户端：3-4天
- 测试：1-2天
- 总计：6-9天
