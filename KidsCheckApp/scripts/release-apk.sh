#!/usr/bin/env bash
# =============================================================================
# KidsCheck APK 发布脚本
# 用法：
#   bash scripts/release-apk.sh --version 1.1.0
#   bash scripts/release-apk.sh --version 1.1.0 --notes "修复已知问题"
#   bash scripts/release-apk.sh --version 1.1.0 --force --notes "紧急安全更新"
#   bash scripts/release-apk.sh --version 1.1.0 --dry-run
# =============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# 路径
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ANDROID_DIR="${PROJECT_ROOT}/android"
GRADLE_FILE="${ANDROID_DIR}/app/build.gradle.kts"
APK_DIR="${PROJECT_ROOT}/backend/uploads/apk"
VERSION_FILE="${APK_DIR}/version.json"

# ---------------------------------------------------------------------------
# 颜色
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
VERSION_NAME=""
RELEASE_NOTES=""
FORCE_UPDATE=false
DRY_RUN=false

usage() {
    echo "用法: bash scripts/release-apk.sh --version <X.Y.Z> [选项]"
    echo ""
    echo "必填参数:"
    echo "  --version <X.Y.Z>    新版本号"
    echo ""
    echo "可选参数:"
    echo "  --notes <text>       更新说明（默认: 自动生成）"
    echo "  --force              标记为强制更新"
    echo "  --dry-run            仅预览，不执行构建"
    echo "  -h, --help           显示帮助"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --version)  VERSION_NAME="$2"; shift 2 ;;
        --notes)    RELEASE_NOTES="$2"; shift 2 ;;
        --force)    FORCE_UPDATE=true; shift ;;
        --dry-run)  DRY_RUN=true; shift ;;
        -h|--help)  usage ;;
        *)          error "未知参数: $1"; usage ;;
    esac
done

if [[ -z "$VERSION_NAME" ]]; then
    error "必须指定 --version 参数"
    usage
fi

# 校验版本号格式
if ! echo "$VERSION_NAME" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    error "版本号格式错误: ${VERSION_NAME}，应为 X.Y.Z"
    exit 1
fi

# ---------------------------------------------------------------------------
# 计算 version_code = major*10000 + minor*100 + patch
# ---------------------------------------------------------------------------
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION_NAME"
VERSION_CODE=$(( MAJOR * 10000 + MINOR * 100 + PATCH ))

if [[ -z "$RELEASE_NOTES" ]]; then
    RELEASE_NOTES="版本 ${VERSION_NAME} 更新"
fi

APK_FILENAME="kidscheck-${VERSION_NAME}.apk"

# ---------------------------------------------------------------------------
# 摘要
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "  KidsCheck APK 发布"
echo "============================================"
echo "  版本号:     ${VERSION_NAME}"
echo "  版本代码:   ${VERSION_CODE}"
echo "  强制更新:   ${FORCE_UPDATE}"
echo "  APK 文件:   ${APK_FILENAME}"
echo "  更新说明:   ${RELEASE_NOTES}"
echo "============================================"
echo ""

if $DRY_RUN; then
    warn "Dry-run 模式，仅预览不执行"
    exit 0
fi

# ---------------------------------------------------------------------------
# Step 1: 更新 build.gradle.kts 中的 versionCode 和 versionName
# ---------------------------------------------------------------------------
log "更新 build.gradle.kts..."

if [[ ! -f "$GRADLE_FILE" ]]; then
    error "未找到 ${GRADLE_FILE}"
    exit 1
fi

# 备份原文件
cp "$GRADLE_FILE" "${GRADLE_FILE}.bak"

# 替换 versionCode 和 versionName
if [[ "$(uname -s)" == MINGW* ]] || [[ "$(uname -s)" == MSYS* ]]; then
    # Windows (Git Bash)
    sed -i "s/versionCode = [0-9]*/versionCode = ${VERSION_CODE}/" "$GRADLE_FILE"
    sed -i "s/versionName = \"[^\"]*\"/versionName = \"${VERSION_NAME}\"/" "$GRADLE_FILE"
else
    # Linux / macOS
    sed -i "s/versionCode = [0-9]*/versionCode = ${VERSION_CODE}/" "$GRADLE_FILE"
    sed -i "s/versionName = \"[^\"]*\"/versionName = \"${VERSION_NAME}\"/" "$GRADLE_FILE"
fi

log "build.gradle.kts 已更新 (versionCode=${VERSION_CODE}, versionName=${VERSION_NAME})"

# ---------------------------------------------------------------------------
# Step 2: 构建 APK
# ---------------------------------------------------------------------------
log "构建 APK (prodRelease)..."

# 设置 JAVA_HOME（如果未设置）
if [[ -z "${JAVA_HOME:-}" ]]; then
    # 尝试常见的 JDK 路径
    for candidate in \
        "/c/Program Files/Eclipse Adoptium/jdk-17.0.19.10-hotspot" \
        "/c/Program Files/Java/jdk-17" \
        "/c/Program Files/Java/jdk-17.0"*; do
        if [[ -d "$candidate" ]]; then
            export JAVA_HOME="$candidate"
            break
        fi
    done
fi

if [[ -z "${JAVA_HOME:-}" ]]; then
    warn "未找到 JAVA_HOME，Gradle 构建可能失败"
fi

# 执行 Gradle 构建
pushd "$ANDROID_DIR" > /dev/null
if [[ -f "gradlew" ]]; then
    chmod +x gradlew
    ./gradlew :app:assembleProdRelease --no-daemon
else
    error "未找到 gradlew"
    exit 1
fi
popd > /dev/null

# 查找构建产物
APK_OUTPUT="${ANDROID_DIR}/app/build/outputs/apk/prod/release/app-prod-release-unsigned.apk"
if [[ ! -f "$APK_OUTPUT" ]]; then
    # 尝试其他可能的路径
    APK_OUTPUT=$(find "${ANDROID_DIR}/app/build/outputs/apk" -name "*.apk" -type f 2>/dev/null | head -1)
    if [[ -z "$APK_OUTPUT" ]] || [[ ! -f "$APK_OUTPUT" ]]; then
        error "未找到构建产物 APK"
        exit 1
    fi
fi

log "APK 构建完成: ${APK_OUTPUT}"

# ---------------------------------------------------------------------------
# Step 3: 复制 APK 到 backend/uploads/apk/
# ---------------------------------------------------------------------------
log "复制 APK 到 ${APK_DIR}..."
mkdir -p "$APK_DIR"
cp "$APK_OUTPUT" "${APK_DIR}/${APK_FILENAME}"
log "APK 已复制: ${APK_DIR}/${APK_FILENAME}"

# ---------------------------------------------------------------------------
# Step 4: 计算 MD5 和文件大小
# ---------------------------------------------------------------------------
log "计算 MD5 和文件大小..."

if command -v md5sum &>/dev/null; then
    APK_MD5=$(md5sum "${APK_DIR}/${APK_FILENAME}" | cut -d' ' -f1)
elif command -v md5 &>/dev/null; then
    APK_MD5=$(md5 -q "${APK_DIR}/${APK_FILENAME}")
else
    warn "未找到 md5sum 或 md5 命令，跳过 MD5 计算"
    APK_MD5=""
fi

APK_SIZE=$(stat -c%s "${APK_DIR}/${APK_FILENAME}" 2>/dev/null || \
           stat -f%z "${APK_DIR}/${APK_FILENAME}" 2>/dev/null || \
           wc -c < "${APK_DIR}/${APK_FILENAME}" | tr -d ' ')

log "MD5: ${APK_MD5}"
log "大小: ${APK_SIZE} bytes"

# ---------------------------------------------------------------------------
# Step 5: 更新 version.json
# ---------------------------------------------------------------------------
log "更新 version.json..."

CREATED_AT=$(date -u '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null || date -u '+%Y-%m-%dT%H:%M:%S' 2>/dev/null)

# 使用 Python 生成 JSON（比 jq 更可靠）
python3 -c "
import json, sys

data = {
    'version_code': ${VERSION_CODE},
    'version_name': '${VERSION_NAME}',
    'apk_filename': '${APK_FILENAME}',
    'apk_size': ${APK_SIZE},
    'apk_md5': '${APK_MD5}',
    'release_notes': '''${RELEASE_NOTES}''',
    'force_update': $(if $FORCE_UPDATE; then echo 'True'; else echo 'False'; fi),
    'min_supported_version': ${VERSION_CODE},
    'created_at': '${CREATED_AT}'
}

with open('${VERSION_FILE}', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write('\n')
"

log "version.json 已更新"

# ---------------------------------------------------------------------------
# Step 6: 清理旧 APK
# ---------------------------------------------------------------------------
log "清理旧 APK..."
CLEANED=0
for old_apk in "${APK_DIR}"/kidscheck-*.apk; do
    if [[ -f "$old_apk" ]] && [[ "$(basename "$old_apk")" != "$APK_FILENAME" ]]; then
        rm -f "$old_apk"
        CLEANED=$((CLEANED + 1))
        log "已删除: $(basename "$old_apk")"
    fi
done
if [[ $CLEANED -eq 0 ]]; then
    log "无旧 APK 需要清理"
fi

# ---------------------------------------------------------------------------
# Step 7: 清理备份文件
# ---------------------------------------------------------------------------
rm -f "${GRADLE_FILE}.bak"

# ---------------------------------------------------------------------------
# 完成
# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "  APK 发布完成"
echo "============================================"
echo "  版本:     ${VERSION_NAME} (${VERSION_CODE})"
echo "  APK:      ${APK_DIR}/${APK_FILENAME}"
echo "  大小:     $((APK_SIZE / 1024)) KB"
echo "  MD5:      ${APK_MD5}"
echo "  强制更新: ${FORCE_UPDATE}"
echo "============================================"
echo ""
echo "下一步操作："
echo "  1. 提交代码: git add . && git commit -m \"release: v${VERSION_NAME}\""
echo "  2. 打包部署: bash scripts/pack.sh"
echo "  3. 上传服务器: bash scripts/upload.sh <archive> <user@host>"
echo ""
