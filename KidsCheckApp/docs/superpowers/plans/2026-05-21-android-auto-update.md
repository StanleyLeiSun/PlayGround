# Android客户端自动更新功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为KidsCheck Android客户端实现自动检测新版本并自动升级的功能，确保用户始终使用最新版本。

**Architecture:** 采用自建服务器方案，后端提供版本检查API和APK文件下载服务，客户端启动时检查版本并支持应用内下载和自动安装。

**Tech Stack:** FastAPI + SQLAlchemy (后端), Kotlin + Coroutines + Retrofit + DownloadManager (Android)

---

## 文件结构

### 后端文件
- Create: `backend/app/routers/app_version.py` - 版本检查和APK下载API
- Create: `backend/uploads/apk/version.json` - 版本信息配置文件
- Create: `backend/uploads/apk/` - APK文件存储目录

### Android文件
- Create: `android/app/src/main/java/com/kidscheck/app/data/model/AppVersion.kt` - 版本信息数据类
- Create: `android/app/src/main/java/com/kidscheck/app/util/VersionChecker.kt` - 版本检查器
- Create: `android/app/src/main/java/com/kidscheck/app/util/ApkDownloader.kt` - APK下载器
- Create: `android/app/src/main/java/com/kidscheck/app/util/ApkInstaller.kt` - APK安装器
- Create: `android/app/src/main/java/com/kidscheck/app/ui/screens/update/UpdateDialog.kt` - 更新对话框
- Modify: `android/app/src/main/java/com/kidscheck/app/ui/screens/mine/MineScreen.kt` - 添加版本信息显示
- Modify: `android/app/src/main/java/com/kidscheck/app/MainActivity.kt` - 集成版本检查
- Modify: `android/app/src/main/java/com/kidscheck/app/data/api/ApiService.kt` - 添加版本检查API
- Modify: `android/app/src/main/AndroidManifest.xml` - 添加权限声明

---

## Task 1: 后端 - 创建版本检查API

**Files:**
- Create: `backend/app/routers/app_version.py`
- Create: `backend/uploads/apk/version.json`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建uploads/apk目录和version.json**

```bash
mkdir -p backend/uploads/apk
```

创建 `backend/uploads/apk/version.json`:
```json
{
  "version_code": 1,
  "version_name": "1.0.0",
  "apk_filename": "kidscheck-1.0.0.apk",
  "release_notes": "1. 初始版本\n2. 基础打卡功能",
  "force_update": false,
  "min_supported_version": 1,
  "created_at": "2026-05-21T10:00:00Z"
}
```

- [ ] **Step 2: 创建版本检查API router**

创建 `backend/app/routers/app_version.py`:
```python
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
import json

router = APIRouter(prefix="/api/app", tags=["app"])

VERSION_FILE = Path("uploads/apk/version.json")


@router.get("/version")
async def check_version():
    """检查应用版本"""
    if not VERSION_FILE.exists():
        raise HTTPException(status_code=404, detail="Version info not found")

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        version_data = json.load(f)

    return {
        "version_code": version_data["version_code"],
        "version_name": version_data["version_name"],
        "apk_url": f"/api/app/download/{version_data['version_name']}",
        "apk_size": version_data.get("apk_size", 0),
        "apk_md5": version_data.get("apk_md5", ""),
        "release_notes": version_data["release_notes"],
        "force_update": version_data["force_update"],
        "min_supported_version": version_data["min_supported_version"]
    }


@router.get("/download/{version_name}")
async def download_apk(version_name: str, request: Request):
    """下载APK文件"""
    if not VERSION_FILE.exists():
        raise HTTPException(status_code=404, detail="Version info not found")

    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        version_data = json.load(f)

    if version_data["version_name"] != version_name:
        raise HTTPException(status_code=404, detail="Version not found")

    apk_path = Path("uploads/apk") / version_data["apk_filename"]
    if not apk_path.exists():
        raise HTTPException(status_code=404, detail="APK file not found")

    return FileResponse(
        path=str(apk_path),
        filename=version_data["apk_filename"],
        media_type="application/vnd.android.package-archive"
    )
```

- [ ] **Step 3: 注册router到main.py**

修改 `backend/app/main.py`，在现有router注册后添加：
```python
from app.routers import auth, children, templates, conditional_tasks, daily_tasks, progress, points, rewards, action_logs, insights, app_version

# ... 现有代码 ...

app.include_router(app_version.router)
```

- [ ] **Step 4: 测试版本检查API**

启动后端服务：
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

测试API：
```bash
curl http://localhost:8000/api/app/version
```

预期响应：
```json
{
  "version_code": 1,
  "version_name": "1.0.0",
  "apk_url": "/api/app/download/1.0.0",
  "apk_size": 0,
  "apk_md5": "",
  "release_notes": "1. 初始版本\n2. 基础打卡功能",
  "force_update": false,
  "min_supported_version": 1
}
```

- [ ] **Step 5: 提交后端代码**

```bash
git add backend/app/routers/app_version.py backend/app/main.py backend/uploads/apk/
git commit -m "feat: add app version check API"
```

---

## Task 2: Android - 创建版本信息数据类

**Files:**
- Create: `android/app/src/main/java/com/kidscheck/app/data/model/AppVersion.kt`

- [ ] **Step 1: 创建AppVersion数据类**

创建 `android/app/src/main/java/com/kidscheck/app/data/model/AppVersion.kt`:
```kotlin
package com.kidscheck.app.data.model

import com.google.gson.annotations.SerializedName

data class AppVersion(
    @SerializedName("version_code")
    val versionCode: Int,
    @SerializedName("version_name")
    val versionName: String,
    @SerializedName("apk_url")
    val apkUrl: String,
    @SerializedName("apk_size")
    val apkSize: Long,
    @SerializedName("apk_md5")
    val apkMd5: String,
    @SerializedName("release_notes")
    val releaseNotes: String,
    @SerializedName("force_update")
    val forceUpdate: Boolean,
    @SerializedName("min_supported_version")
    val minSupportedVersion: Int
)
```

- [ ] **Step 2: 提交数据类**

```bash
git add android/app/src/main/java/com/kidscheck/app/data/model/AppVersion.kt
git commit -m "feat: add AppVersion data model"
```

---

## Task 3: Android - 添加版本检查API到ApiService

**Files:**
- Modify: `android/app/src/main/java/com/kidscheck/app/data/api/ApiService.kt`

- [ ] **Step 1: 添加版本检查接口**

在 `android/app/src/main/java/com/kidscheck/app/data/api/ApiService.kt` 的 `ApiService` 接口中添加：
```kotlin
@GET("/api/app/version")
suspend fun checkVersion(): Response<AppVersion>
```

- [ ] **Step 2: 提交API接口**

```bash
git add android/app/src/main/java/com/kidscheck/app/data/api/ApiService.kt
git commit -m "feat: add version check API to ApiService"
```

---

## Task 4: Android - 创建版本检查器

**Files:**
- Create: `android/app/src/main/java/com/kidscheck/app/util/VersionChecker.kt`

- [ ] **Step 1: 创建VersionChecker**

创建 `android/app/src/main/java/com/kidscheck/app/util/VersionChecker.kt`:
```kotlin
package com.kidscheck.app.util

import android.content.Context
import com.kidscheck.app.BuildConfig
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.AppVersion

object VersionChecker {

    suspend fun checkForUpdate(context: Context): AppVersion? {
        return try {
            val api = RetrofitInstance.getApi(context)
            val response = api.checkVersion()
            if (response.isSuccessful) {
                val serverVersion = response.body()
                if (serverVersion != null && needUpdate(serverVersion)) {
                    serverVersion
                } else {
                    null
                }
            } else {
                null
            }
        } catch (e: Exception) {
            null
        }
    }

    fun needUpdate(serverVersion: AppVersion): Boolean {
        val clientVersionCode = BuildConfig.VERSION_CODE

        // 如果本地版本比服务器版本新，不提示更新
        if (clientVersionCode >= serverVersion.versionCode) {
            return false
        }

        // 如果强制更新，必须更新
        if (serverVersion.forceUpdate) {
            return true
        }

        // 如果本地版本低于最低支持版本，强制更新
        if (clientVersionCode < serverVersion.minSupportedVersion) {
            return true
        }

        // 有新版本可选更新
        return true
    }

    fun isForceUpdate(serverVersion: AppVersion): Boolean {
        val clientVersionCode = BuildConfig.VERSION_CODE

        // 如果本地版本比服务器版本新，不强制更新
        if (clientVersionCode >= serverVersion.versionCode) {
            return false
        }

        // 如果强制更新标志为true，强制更新
        if (serverVersion.forceUpdate) {
            return true
        }

        // 如果本地版本低于最低支持版本，强制更新
        if (clientVersionCode < serverVersion.minSupportedVersion) {
            return true
        }

        return false
    }
}
```

- [ ] **Step 2: 提交VersionChecker**

```bash
git add android/app/src/main/java/com/kidscheck/app/util/VersionChecker.kt
git commit -m "feat: add VersionChecker utility"
```

---

## Task 5: Android - 创建APK下载器

**Files:**
- Create: `android/app/src/main/java/com/kidscheck/app/util/ApkDownloader.kt`

- [ ] **Step 1: 创建ApkDownloader**

创建 `android/app/src/main/java/com/kidscheck/app/util/ApkDownloader.kt`:
```kotlin
package com.kidscheck.app.util

import android.app.DownloadManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.Uri
import android.os.Environment
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.AppVersion
import java.io.File

data class DownloadStatus(
    val status: Int,
    val progress: Int,
    val localUri: String?
)

object ApkDownloader {

    private var downloadId: Long = -1
    private var onComplete: ((String) -> Unit)? = null
    private var onProgress: ((Int) -> Unit)? = null

    private val downloadReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val id = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1)
            if (id == downloadId) {
                val query = DownloadManager.Query().setFilterById(downloadId)
                val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                val cursor = manager.query(query)

                if (cursor.moveToFirst()) {
                    val statusIndex = cursor.getColumnIndex(DownloadManager.COLUMN_STATUS)
                    val status = cursor.getInt(statusIndex)

                    when (status) {
                        DownloadManager.STATUS_SUCCESSFUL -> {
                            val localUriIndex = cursor.getColumnIndex(DownloadManager.COLUMN_LOCAL_URI)
                            val localUri = cursor.getString(localUriIndex)
                            onComplete?.invoke(localUri)
                        }
                        DownloadManager.STATUS_FAILED -> {
                            onComplete?.invoke("")
                        }
                    }
                }
                cursor.close()
            }
        }
    }

    fun startDownload(context: Context, version: AppVersion): Long {
        val baseUrl = RetrofitInstance.BASE_URL
        val apkUrl = "$baseUrl${version.apkUrl}"

        val request = DownloadManager.Request(Uri.parse(apkUrl))
            .setTitle("KidsCheck 更新")
            .setDescription("正在下载版本 ${version.versionName}")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setDestinationInExternalPublicDir(
                Environment.DIRECTORY_DOWNLOADS,
                "kidscheck-${version.versionName}.apk"
            )
            .setAllowedOverMetered(true)
            .setAllowedOverRoaming(true)

        val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        downloadId = manager.enqueue(request)

        // 保存下载ID到SharedPreferences
        val prefs = context.getSharedPreferences("update_prefs", Context.MODE_PRIVATE)
        prefs.edit().putLong("download_id", downloadId).apply()

        return downloadId
    }

    fun getDownloadStatus(context: Context): DownloadStatus {
        if (downloadId == -1L) {
            return DownloadStatus(DownloadManager.STATUS_FAILED, 0, null)
        }

        val query = DownloadManager.Query().setFilterById(downloadId)
        val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        val cursor = manager.query(query)

        if (cursor.moveToFirst()) {
            val statusIndex = cursor.getColumnIndex(DownloadManager.COLUMN_STATUS)
            val progressIndex = cursor.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)
            val totalIndex = cursor.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)
            val localUriIndex = cursor.getColumnIndex(DownloadManager.COLUMN_LOCAL_URI)

            val status = cursor.getInt(statusIndex)
            val progress = cursor.getInt(progressIndex)
            val total = cursor.getInt(totalIndex)
            val localUri = cursor.getString(localUriIndex)

            val progressPercent = if (total > 0) (progress * 100 / total) else 0

            cursor.close()
            return DownloadStatus(status, progressPercent, localUri)
        }

        cursor.close()
        return DownloadStatus(DownloadManager.STATUS_FAILED, 0, null)
    }

    fun registerReceiver(context: Context, onComplete: (String) -> Unit, onProgress: (Int) -> Unit) {
        this.onComplete = onComplete
        this.onProgress = onProgress

        val filter = IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE)
        context.registerReceiver(downloadReceiver, filter)
    }

    fun unregisterReceiver(context: Context) {
        try {
            context.unregisterReceiver(downloadReceiver)
        } catch (e: Exception) {
            // Receiver not registered
        }
        onComplete = null
        onProgress = null
    }

    fun getDownloadId(): Long = downloadId

    fun setDownloadId(id: Long) {
        downloadId = id
    }
}
```

- [ ] **Step 2: 提交ApkDownloader**

```bash
git add android/app/src/main/java/com/kidscheck/app/util/ApkDownloader.kt
git commit -m "feat: add ApkDownloader utility"
```

---

## Task 6: Android - 创建APK安装器

**Files:**
- Create: `android/app/src/main/java/com/kidscheck/app/util/ApkInstaller.kt`

- [ ] **Step 1: 创建ApkInstaller**

创建 `android/app/src/main/java/com/kidscheck/app/util/ApkInstaller.kt`:
```kotlin
package com.kidscheck.app.util

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import androidx.core.content.FileProvider
import java.io.File
import java.security.MessageDigest

object ApkInstaller {

    fun installApk(context: Context, apkFile: File) {
        val uri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                apkFile
            )
        } else {
            Uri.fromFile(apkFile)
        }

        val intent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
        }

        context.startActivity(intent)
    }

    fun canRequestPackageInstalls(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.packageManager.canRequestPackageInstalls()
        } else {
            true
        }
    }

    fun requestInstallPermission(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val intent = Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES).apply {
                data = Uri.parse("package:${context.packageName}")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK
            }
            context.startActivity(intent)
        }
    }

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
        if (expectedMd5.isEmpty()) {
            return true // 如果没有MD5校验码，跳过验证
        }
        val actualMd5 = calculateMd5(apkFile)
        return actualMd5.equals(expectedMd5, ignoreCase = true)
    }
}
```

- [ ] **Step 2: 提交ApkInstaller**

```bash
git add android/app/src/main/java/com/kidscheck/app/util/ApkInstaller.kt
git commit -m "feat: add ApkInstaller utility"
```

---

## Task 7: Android - 创建更新对话框

**Files:**
- Create: `android/app/src/main/java/com/kidscheck/app/ui/screens/update/UpdateDialog.kt`

- [ ] **Step 1: 创建UpdateDialog**

创建 `android/app/src/main/java/com/kidscheck/app/ui/screens/update/UpdateDialog.kt`:
```kotlin
package com.kidscheck.app.ui.screens.update

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.model.AppVersion
import com.kidscheck.app.ui.theme.*

@Composable
fun UpdateDialog(
    version: AppVersion,
    isDownloading: Boolean,
    downloadProgress: Int,
    onUpdateClick: () -> Unit,
    onSkipClick: (() -> Unit)?,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = { if (!isDownloading && onSkipClick != null) onDismiss() },
        title = {
            Text(
                text = "发现新版本",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column {
                Text(
                    text = "版本 ${version.versionName}",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium,
                    color = Primary
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "更新内容：",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = version.releaseNotes,
                    fontSize = 14.sp,
                    color = TextSecondary
                )

                if (version.apkSize > 0) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "大小：${formatFileSize(version.apkSize)}",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )
                }

                if (isDownloading) {
                    Spacer(modifier = Modifier.height(16.dp))
                    LinearProgressIndicator(
                        progress = downloadProgress / 100f,
                        modifier = Modifier.fillMaxWidth(),
                        color = Primary
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "下载中... $downloadProgress%",
                        fontSize = 12.sp,
                        color = TextSecondary,
                        modifier = Modifier.align(Alignment.CenterHorizontally)
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onUpdateClick,
                enabled = !isDownloading,
                colors = ButtonDefaults.buttonColors(containerColor = Primary)
            ) {
                Text(
                    text = if (isDownloading) "下载中..." else "立即更新",
                    fontWeight = FontWeight.SemiBold
                )
            }
        },
        dismissButton = {
            if (onSkipClick != null && !isDownloading) {
                TextButton(onClick = onSkipClick) {
                    Text(
                        text = "稍后再说",
                        color = TextSecondary
                    )
                }
            }
        },
        shape = RoundedCornerShape(16.dp)
    )
}

private fun formatFileSize(bytes: Long): String {
    return when {
        bytes >= 1024 * 1024 -> "${bytes / (1024 * 1024)} MB"
        bytes >= 1024 -> "${bytes / 1024} KB"
        else -> "$bytes B"
    }
}
```

- [ ] **Step 2: 提交UpdateDialog**

```bash
git add android/app/src/main/java/com/kidscheck/app/ui/screens/update/UpdateDialog.kt
git commit -m "feat: add UpdateDialog composable"
```

---

## Task 8: Android - 更新MineScreen显示版本信息

**Files:**
- Modify: `android/app/src/main/java/com/kidscheck/app/ui/screens/mine/MineScreen.kt`

- [ ] **Step 1: 添加版本信息显示**

在 `MineScreen.kt` 的 `LazyColumn` 中，在"退出登录"按钮后添加：
```kotlin
// 关于区域
item {
    Spacer(modifier = Modifier.height(8.dp))
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(14.dp),
        color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(2.dp, Border)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "关于",
                fontSize = 16.sp,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.padding(bottom = 12.dp)
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "版本：${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})",
                    fontSize = 14.sp,
                    color = TextSecondary
                )
                TextButton(
                    onClick = { /* 检查更新逻辑 */ }
                ) {
                    Text(
                        text = "检查更新",
                        fontSize = 14.sp,
                        color = Primary
                    )
                }
            }
        }
    }
}
```

- [ ] **Step 2: 提交MineScreen更新**

```bash
git add android/app/src/main/java/com/kidscheck/app/ui/screens/mine/MineScreen.kt
git commit -m "feat: add version info to MineScreen"
```

---

## Task 9: Android - 集成版本检查到MainActivity

**Files:**
- Modify: `android/app/src/main/java/com/kidscheck/app/MainActivity.kt`

- [ ] **Step 1: 添加版本检查逻辑**

在 `MainActivity.kt` 中添加版本检查：
```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            KidsCheckNavHost()
        }

        // 检查更新
        checkForUpdate()
    }

    private fun checkForUpdate() {
        lifecycleScope.launch {
            val version = VersionChecker.checkForUpdate(this@MainActivity)
            if (version != null) {
                // 显示更新对话框
                showUpdateDialog(version)
            }
        }
    }

    private fun showUpdateDialog(version: AppVersion) {
        // 在Compose中显示对话框
    }
}
```

- [ ] **Step 2: 提交MainActivity更新**

```bash
git add android/app/src/main/java/com/kidscheck/app/MainActivity.kt
git commit -m "feat: integrate version check in MainActivity"
```

---

## Task 10: Android - 添加权限声明

**Files:**
- Modify: `android/app/src/main/AndroidManifest.xml`

- [ ] **Step 1: 添加权限声明**

在 `AndroidManifest.xml` 中添加：
```xml
<uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />
```

- [ ] **Step 2: 提交权限声明**

```bash
git add android/app/src/main/AndroidManifest.xml
git commit -m "feat: add install packages permission"
```

---

## Task 11: 端到端测试

- [ ] **Step 1: 启动后端服务**

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: 构建并安装Android应用**

```bash
cd android
./gradlew :app:installDevDebug
```

- [ ] **Step 3: 测试版本检查功能**

1. 打开应用
2. 检查是否显示更新对话框
3. 测试"立即更新"按钮
4. 测试"稍后再说"按钮
5. 测试下载进度显示
6. 测试安装流程

- [ ] **Step 4: 测试MineScreen版本显示**

1. 导航到"我的"页面
2. 检查版本信息是否正确显示
3. 测试"检查更新"按钮

- [ ] **Step 5: 提交测试结果**

```bash
git add .
git commit -m "test: add end-to-end testing for auto-update feature"
```

---

## 预计工作量

- **后端**: 1天
- **Android客户端**: 2-3天
- **测试**: 1天
- **总计**: 4-5天

---

## 注意事项

1. **版本号管理**: 确保 `version_code` 和 `version_name` 保持一致
2. **APK文件**: 需要先构建APK文件并放到 `uploads/apk/` 目录
3. **MD5校验**: 需要计算APK文件的MD5并更新到 `version.json`
4. **权限处理**: Android 8.0+ 需要处理安装未知来源应用的权限
5. **断点续传**: 使用DownloadManager自动支持断点续传
6. **错误处理**: 版本检查失败时静默处理，不影响正常使用
