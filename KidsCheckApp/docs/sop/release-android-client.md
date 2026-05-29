# SOP: Android 客户端发布

## 概述

构建 prodRelease APK，上传到线上服务器的 `/opt/kidscheck/backend/uploads/apk/` 目录，更新 `version.json`，客户端打开后自动检测到新版本并提示更新。

## 前置条件

- 本地已配置 Android SDK 和 JDK 17+
- 代码已提交，`git status` 干净
- SSH 可免密登录线上服务器

## 版本号规则

| 字段 | 规则 | 示例 |
|------|------|------|
| versionName | 语义化版本 X.Y.Z | `1.1.5` |
| versionCode | major×10000 + minor×100 + patch | `10105` |

版本号定义在 `android/app/build.gradle.kts` 中。

## 操作步骤

### 1. 更新版本号

编辑 `android/app/build.gradle.kts`：

```kotlin
versionCode = 10106        // 新版本代码
versionName = "1.1.6"      // 新版本名
```

### 2. 确认代码编译通过

```bash
cd android
./gradlew :app:compileProdReleaseKotlin --no-daemon
```

常见编译问题：缺少 import（如 `Unresolved reference: clip` → 添加 `import androidx.compose.ui.draw.clip`）。

### 3. 构建 prodRelease APK

```bash
cd android
./gradlew :app:assembleProdRelease --no-daemon
```

构建产物路径：`android/app/build/outputs/apk/prod/release/app-prod-release.apk`

### 4. 准备本地发布文件

```bash
VERSION="1.1.6"
APK_SRC="android/app/build/outputs/apk/prod/release/app-prod-release.apk"
APK_DIR="backend/uploads/apk"
APK_DEST="${APK_DIR}/kidscheck-${VERSION}.apk"

# 复制 APK
cp "$APK_SRC" "$APK_DEST"

# 获取 MD5 和文件大小
APK_MD5=$(md5 -q "$APK_DEST")
APK_SIZE=$(stat -f%z "$APK_DEST")

# 更新 version.json
cat > "${APK_DIR}/version.json" << EOF
{
  "version_code": 10106,
  "version_name": "${VERSION}",
  "apk_filename": "kidscheck-${VERSION}.apk",
  "apk_size": ${APK_SIZE},
  "apk_md5": "${APK_MD5}",
  "release_notes": "更新说明",
  "force_update": false,
  "min_supported_version": 1,
  "created_at": "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
}
EOF
```

### 5. 上传到线上服务器

```bash
VERSION="1.1.6"
SERVER="admin@47.94.167.238"
REMOTE_APK_DIR="/opt/kidscheck/backend/uploads/apk"

# 上传到 /tmp（绕过目录权限）
scp backend/uploads/apk/kidscheck-${VERSION}.apk ${SERVER}:/tmp/
scp backend/uploads/apk/version.json ${SERVER}:/tmp/

# 远程移动到目标目录并清理旧版本
ssh ${SERVER} << EOF
sudo mv /tmp/kidscheck-${VERSION}.apk ${REMOTE_APK_DIR}/
sudo mv /tmp/version.json ${REMOTE_APK_DIR}/
# 清理旧版本 APK（保留当前版本）
sudo find ${REMOTE_APK_DIR} -name "kidscheck-*.apk" ! -name "kidscheck-${VERSION}.apk" -delete
ls -lh ${REMOTE_APK_DIR}/
EOF
```

### 6. 验证发布

```bash
# 检查版本接口
curl -s http://47.94.167.238/api/app/version | python3 -m json.tool

# 预期返回新版本号和正确的下载链接
```

预期响应：
```json
{
  "version_code": 10106,
  "version_name": "1.1.6",
  "apk_url": "/api/app/download/1.1.6",
  "apk_size": ...,
  "apk_md5": "...",
  "release_notes": "...",
  "force_update": false,
  "min_supported_version": 1
}
```

### 7. 提交代码

```bash
git add android/app/build.gradle.kts backend/uploads/apk/version.json
git commit -m "release: v1.1.6"
git push
```

## 一键脚本

项目提供了 `scripts/release-apk.sh`：

```bash
bash scripts/release-apk.sh --version 1.1.6 --notes "更新说明"
bash scripts/release-apk.sh --version 1.1.6 --force --notes "紧急安全更新"
bash scripts/release-apk.sh --version 1.1.6 --dry-run  # 仅预览
```

该脚本自动完成：版本号更新 → 构建 → 复制 APK → 计算 MD5 → 更新 version.json → 清理旧版本。执行后仍需手动上传到服务器（步骤 5）。

## 连接信息

| 项目 | 值 |
|------|-----|
| 服务器 IP | `47.94.167.238` |
| SSH 用户名 | `admin` |
| APK 远程目录 | `/opt/kidscheck/backend/uploads/apk/` |
| 版本检查接口 | `GET /api/app/version` |
| APK 下载接口 | `GET /api/app/download/{version_name}` |

## 注意事项

- 远程 `/opt/kidscheck/backend/uploads/apk/` 目录需要 sudo 权限写入，先 scp 到 `/tmp` 再 sudo mv
- `force_update: true` 会强制用户更新，仅用于安全修复等紧急情况
- `min_supported_version` 设为 1 表示不强制淘汰任何旧版本，如需强制淘汰旧版本可设为对应 versionCode
- macOS 上 `md5` 命令用 `-q` 参数，Linux 上用 `md5sum | cut -d' ' -f1`
