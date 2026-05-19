#!/usr/bin/env bash
# =============================================================================
# KidsCheck 备份基础设施一次性部署脚本
# 功能：创建目录、安装依赖、配置 cron 定时任务、部署脚本文件
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 可配置参数（支持环境变量覆盖）
# ---------------------------------------------------------------------------
APP_DIR="${APP_DIR:-/opt/kidscheck}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/kidscheck}"

# cron 表达式：每周一凌晨 3 点执行备份
CRON_SCHEDULE="0 3 * * 1"
CRON_COMMAND="${APP_DIR}/scripts/backup.sh >> /var/log/kidscheck-backup.log 2>&1"
CRON_JOB="${CRON_SCHEDULE} ${CRON_COMMAND}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# 日志函数
# ---------------------------------------------------------------------------
log_info()  { echo "[INFO]  $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*"; }

# ---------------------------------------------------------------------------
# 1. 创建备份目录结构
# ---------------------------------------------------------------------------
create_backup_dirs() {
    log_info "创建备份目录: ${BACKUP_ROOT}/weekly, ${BACKUP_ROOT}/monthly"
    mkdir -p "${BACKUP_ROOT}/weekly"
    mkdir -p "${BACKUP_ROOT}/monthly"
    log_info "备份目录创建完成"
}

# ---------------------------------------------------------------------------
# 2. 安装 sqlite3（如果不存在）
# ---------------------------------------------------------------------------
install_sqlite3() {
    if command -v sqlite3 &>/dev/null; then
        log_info "sqlite3 已安装: $(sqlite3 --version)"
        return 0
    fi

    log_info "sqlite3 未检测到，正在安装..."
    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y -qq sqlite3
        log_info "sqlite3 安装完成: $(sqlite3 --version)"
    else
        log_error "apt-get 不可用，请手动安装 sqlite3"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# 3. 安装 cron（如果不存在）
# ---------------------------------------------------------------------------
install_cron() {
    if command -v crontab &>/dev/null; then
        log_info "cron 已可用"
        return 0
    fi

    log_info "cron 未检测到，正在安装..."
    if command -v apt-get &>/dev/null; then
        apt-get update -qq
        apt-get install -y -qq cron
        systemctl enable cron 2>/dev/null || service cron start 2>/dev/null || true
        log_info "cron 安装完成"
    else
        log_error "apt-get 不可用，请手动安装 cron"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# 4. 配置 cron 定时任务（幂等：避免重复添加）
# ---------------------------------------------------------------------------
setup_cron_job() {
    log_info "配置 cron 定时任务..."

    # 确保 crontab 可用
    if ! command -v crontab &>/dev/null; then
        log_error "crontab 命令不可用，无法配置定时任务"
        exit 1
    fi

    # 获取当前 crontab 内容（可能为空）
    local current_crontab
    current_crontab="$(crontab -l 2>/dev/null || true)"

    # 检查是否已存在相同的备份任务
    if echo "${current_crontab}" | grep -Fq "${CRON_COMMAND}"; then
        log_info "cron 任务已存在，跳过添加"
        return 0
    fi

    # 追加备份任务
    local new_crontab
    new_crontab="${current_crontab}

# KidsCheck 自动备份 - 每周一凌晨 3 点
${CRON_JOB}"

    echo "${new_crontab}" | crontab -
    log_info "cron 任务已添加: ${CRON_JOB}"
}

# ---------------------------------------------------------------------------
# 5. 部署脚本文件到应用目录
# ---------------------------------------------------------------------------
deploy_scripts() {
    log_info "部署脚本到 ${APP_DIR}/scripts/"

    mkdir -p "${APP_DIR}/scripts"

    # 复制 backup.sh 和 restore.sh（如果存在）
    local script
    for script in backup.sh restore.sh; do
        local src="${SCRIPT_DIR}/${script}"
        local dst="${APP_DIR}/scripts/${script}"

        if [[ -f "${src}" ]]; then
            cp "${src}" "${dst}"
            chmod +x "${dst}"
            log_info "已部署: ${dst}"
        else
            log_warn "源文件不存在，跳过: ${src}"
        fi
    done
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
main() {
    log_info "=========================================="
    log_info "KidsCheck 备份基础设施部署开始"
    log_info "=========================================="
    log_info "APP_DIR=${APP_DIR}"
    log_info "BACKUP_ROOT=${BACKUP_ROOT}"
    echo ""

    create_backup_dirs
    echo ""

    install_sqlite3
    install_cron
    echo ""

    setup_cron_job
    echo ""

    deploy_scripts
    echo ""

    log_info "=========================================="
    log_info "部署完成！"
    log_info "=========================================="
    echo ""
    log_info "后续步骤："
    log_info "  1. 配置 Nginx 反向代理，将 /backups/ 映射到 ${BACKUP_ROOT}/"
    log_info "  2. 设置 htpasswd 基本认证保护备份下载端点"
    log_info "  3. 重载 Nginx 配置: nginx -t && systemctl reload nginx"
    log_info "  4. 手动测试备份: ${APP_DIR}/scripts/backup.sh"
    log_info "  5. 从本地拉取备份: python3 ${SCRIPT_DIR}/pull_backup.py"
    echo ""
    log_info "备份计划: ${CRON_SCHEDULE} (每周一凌晨 3:00)"
    log_info "备份日志: /var/log/kidscheck-backup.log"
}

main "$@"
