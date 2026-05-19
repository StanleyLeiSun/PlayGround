#!/usr/bin/env bash
# =============================================================================
# KidsCheck 数据恢复脚本
# 功能：从备份包恢复数据库和照片，支持合并模式和完整回滚模式
# 用法：restore.sh <backup-archive.tar.gz> [--full]
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 可配置参数（支持环境变量覆盖）
# ---------------------------------------------------------------------------
APP_DIR="${APP_DIR:-/opt/kidscheck}"

# ---------------------------------------------------------------------------
# 内部路径
# ---------------------------------------------------------------------------
DB_FILE="${APP_DIR}/kidscheck.db"
PHOTOS_DIR="${APP_DIR}/uploads/photos"

STAGING_DIR=""   # 将在 main 中初始化，用于 trap 清理

# ---------------------------------------------------------------------------
# 日志函数
# ---------------------------------------------------------------------------
log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
    echo "${msg}"
}

log_info()  { log "INFO"  "$@"; }
log_warn()  { log "WARN"  "$@"; }
log_error() { log "ERROR" "$@"; }

# ---------------------------------------------------------------------------
# 清理临时目录
# ---------------------------------------------------------------------------
cleanup() {
    if [[ -n "${STAGING_DIR}" && -d "${STAGING_DIR}" ]]; then
        rm -rf "${STAGING_DIR}"
        log_info "已清理临时目录: ${STAGING_DIR}"
    fi
}

# ---------------------------------------------------------------------------
# 用法说明
# ---------------------------------------------------------------------------
usage() {
    echo "用法: $0 <backup-archive.tar.gz> [--full]"
    echo ""
    echo "  <backup-archive.tar.gz>  备份压缩包路径"
    echo "  --full                   完整回滚模式（先清空照片目录再恢复）"
    echo ""
    echo "  默认为合并模式：覆盖数据库，合并照片（不删除备份后新增的文件）"
    echo ""
    echo "环境变量:"
    echo "  APP_DIR                  应用根目录（默认: /opt/kidscheck）"
    exit 1
}

# ---------------------------------------------------------------------------
# 前置检查
# ---------------------------------------------------------------------------
preflight_checks() {
    local archive="$1"

    # 检查备份包是否存在
    if [[ ! -f "${archive}" ]]; then
        log_error "备份文件不存在: ${archive}"
        exit 1
    fi

    log_info "========== 恢复任务开始 =========="
    log_info "APP_DIR=${APP_DIR}  备份包=${archive}"

    # 确保应用目录存在
    if [[ ! -d "${APP_DIR}" ]]; then
        log_error "应用目录不存在: ${APP_DIR}"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# 解析参数
# ---------------------------------------------------------------------------
parse_args() {
    if [[ $# -lt 1 ]]; then
        usage
    fi

    ARCHIVE=""
    RESTORE_MODE="merge"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --full)
                RESTORE_MODE="full"
                shift
                ;;
            --help|-h)
                usage
                ;;
            -*)
                log_error "未知选项: $1"
                usage
                ;;
            *)
                if [[ -z "${ARCHIVE}" ]]; then
                    ARCHIVE="$1"
                else
                    log_error "多余参数: $1"
                    usage
                fi
                shift
                ;;
        esac
    done

    if [[ -z "${ARCHIVE}" ]]; then
        log_error "请指定备份文件路径"
        usage
    fi

    # 转为绝对路径
    ARCHIVE="$(cd "$(dirname "${ARCHIVE}")" && pwd)/$(basename "${ARCHIVE}")"
}

# ---------------------------------------------------------------------------
# 确认提示
# ---------------------------------------------------------------------------
confirm_restore() {
    local mode_label="合并模式（覆盖数据库，合并照片）"
    if [[ "${RESTORE_MODE}" == "full" ]]; then
        mode_label="完整回滚模式（清空照片目录后恢复）"
    fi

    echo ""
    echo "============================================"
    echo "  KidsCheck 数据恢复确认"
    echo "============================================"
    echo "  备份包:   ${ARCHIVE}"
    echo "  目标目录: ${APP_DIR}"
    echo "  恢复模式: ${mode_label}"
    echo "============================================"
    echo ""

    read -rp "确认执行恢复操作？(y/N): " answer
    case "${answer}" in
        [yY]|[yY][eE][sS])
            log_info "用户确认，开始恢复..."
            ;;
        *)
            log_info "用户取消，退出恢复"
            exit 0
            ;;
    esac
}

# ---------------------------------------------------------------------------
# 1. 解压备份包到临时目录
# ---------------------------------------------------------------------------
extract_archive() {
    log_info "正在解压备份包到临时目录..."
    tar -xzf "${ARCHIVE}" -C "${STAGING_DIR}"

    # 验证解压内容
    if [[ ! -f "${STAGING_DIR}/kidscheck.db" ]]; then
        log_error "备份包中未找到 kidscheck.db，备份可能已损坏"
        exit 1
    fi

    log_info "解压完成，备份包内容:"
    ls -la "${STAGING_DIR}/"
}

# ---------------------------------------------------------------------------
# 2. 停止 KidsCheck 服务
# ---------------------------------------------------------------------------
stop_service() {
    log_info "正在停止 kidscheck 服务..."
    if systemctl is-active --quiet kidscheck 2>/dev/null; then
        systemctl stop kidscheck
        log_info "kidscheck 服务已停止"
    else
        log_warn "kidscheck 服务未运行或不可用，跳过停止操作"
    fi
}

# ---------------------------------------------------------------------------
# 3. 恢复数据库
# ---------------------------------------------------------------------------
restore_database() {
    log_info "正在恢复数据库: ${STAGING_DIR}/kidscheck.db -> ${DB_FILE}"
    cp -f "${STAGING_DIR}/kidscheck.db" "${DB_FILE}"
    log_info "数据库恢复完成"
}

# ---------------------------------------------------------------------------
# 4. 恢复照片
# ---------------------------------------------------------------------------
restore_photos() {
    local src_photos="${STAGING_DIR}/uploads/photos"

    # 检查备份中是否有照片
    if [[ ! -d "${src_photos}" ]]; then
        log_warn "备份包中未包含照片目录，跳过照片恢复"
        return 0
    fi

    # 确保目标照片目录存在
    mkdir -p "${PHOTOS_DIR}"

    if [[ "${RESTORE_MODE}" == "full" ]]; then
        # 完整回滚：先清空现有照片目录
        log_info "完整回滚模式：清空现有照片目录..."
        rm -rf "${PHOTOS_DIR:?}"/*
        log_info "照片目录已清空"
    else
        log_info "合并模式：保留现有照片，合并备份照片"
    fi

    # 恢复照片（cp -a 保留目录结构，合并时覆盖同名文件）
    cp -a "${src_photos}/." "${PHOTOS_DIR}/"
    log_info "照片恢复完成（${RESTORE_MODE} 模式）"
}

# ---------------------------------------------------------------------------
# 5. 启动 KidsCheck 服务
# ---------------------------------------------------------------------------
start_service() {
    log_info "正在启动 kidscheck 服务..."
    if systemctl is-enabled --quiet kidscheck 2>/dev/null; then
        systemctl start kidscheck
        log_info "kidscheck 服务已启动"
    else
        log_warn "kidscheck 服务未注册或不可用，跳过启动操作"
    fi
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"
    preflight_checks "${ARCHIVE}"
    confirm_restore

    # 创建临时目录，退出时自动清理
    STAGING_DIR="$(mktemp -d)"
    trap cleanup EXIT
    log_info "临时目录: ${STAGING_DIR}"

    # 步骤 1：解压备份包
    extract_archive

    # 步骤 2：停止服务
    stop_service

    # 步骤 3：恢复数据库
    restore_database

    # 步骤 4：恢复照片
    restore_photos

    # 步骤 5：启动服务
    start_service

    log_info "========== 恢复任务完成 =========="
}

main "$@"
