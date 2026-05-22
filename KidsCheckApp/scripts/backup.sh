#!/usr/bin/env bash
# =============================================================================
# KidsCheck 自动化备份脚本
# 功能：SQLite 热备份 + 当月照片归档，生成周备份包，按月留存
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 可配置参数（支持环境变量覆盖）
# ---------------------------------------------------------------------------
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/kidscheck}"
APP_DIR="${APP_DIR:-/opt/kidscheck}"
LOG_FILE="${LOG_FILE:-/var/log/kidscheck-backup.log}"
WEEKLY_RETENTION_DAYS="${WEEKLY_RETENTION_DAYS:-84}"

# ---------------------------------------------------------------------------
# 内部路径
# ---------------------------------------------------------------------------
DB_FILE="${APP_DIR}/backend/kidscheck_dev.db"
PHOTOS_DIR="${APP_DIR}/backend/uploads/photos"

TIMESTAMP="$(date +%Y-%m-%d_%H-%M)"
CURRENT_YEAR_MONTH="$(date +%Y-%m)"
CURRENT_DAY="$(date +%d)"

WEEKLY_DIR="${BACKUP_ROOT}/weekly"
MONTHLY_DIR="${BACKUP_ROOT}/monthly"
STAGING_DIR=""   # 将在 main 中初始化，用于 trap 清理

# ---------------------------------------------------------------------------
# 日志函数
# ---------------------------------------------------------------------------
log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
    echo "${msg}" | tee -a "${LOG_FILE}"
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
# 前置检查
# ---------------------------------------------------------------------------
preflight_checks() {
    # 确保日志目录存在
    mkdir -p "$(dirname "${LOG_FILE}")"

    log_info "========== 备份任务开始 =========="
    log_info "APP_DIR=${APP_DIR}  BACKUP_ROOT=${BACKUP_ROOT}"

    # 检查数据库文件
    if [[ ! -f "${DB_FILE}" ]]; then
        log_error "数据库文件不存在: ${DB_FILE}"
        exit 1
    fi

    # 检查 sqlite3 命令
    if ! command -v sqlite3 &>/dev/null; then
        log_error "sqlite3 命令不可用，请先安装"
        exit 1
    fi

    # 创建必要目录
    mkdir -p "${WEEKLY_DIR}" "${MONTHLY_DIR}"
}

# ---------------------------------------------------------------------------
# 1. SQLite 在线热备份（不阻塞应用）
# ---------------------------------------------------------------------------
backup_database() {
    local dest_db="$1"
    log_info "开始 SQLite 热备份: ${DB_FILE} -> ${dest_db}"

    sqlite3 "${DB_FILE}" ".backup '${dest_db}'"

    # 验证备份完整性
    local integrity
    integrity="$(sqlite3 "${dest_db}" "PRAGMA integrity_check;")"
    if [[ "${integrity}" != "ok" ]]; then
        log_error "备份数据库完整性检查失败: ${integrity}"
        exit 1
    fi

    log_info "数据库备份完成，完整性校验通过"
}

# ---------------------------------------------------------------------------
# 2. 复制当月照片（按目录名 YYYY-MM-* 匹配，保留完整结构）
# ---------------------------------------------------------------------------
backup_photos() {
    local dest_dir="$1"
    log_info "开始备份当月照片: ${PHOTOS_DIR}/${CURRENT_YEAR_MONTH}-*/"

    if [[ ! -d "${PHOTOS_DIR}" ]]; then
        log_warn "照片目录不存在: ${PHOTOS_DIR}，跳过照片备份"
        return 0
    fi

    # 查找当月所有日期子目录
    local found=0
    local child_dir
    for child_dir in "${PHOTOS_DIR}"/*/; do
        [[ -d "${child_dir}" ]] || continue
        local child_id
        child_id="$(basename "${child_dir}")"

        local date_dir
        for date_dir in "${child_dir}${CURRENT_YEAR_MONTH}"-*/; do
            [[ -d "${date_dir}" ]] || continue
            local date_name
            date_name="$(basename "${date_dir}")"

            # 只处理当前月份的目录 (YYYY-MM-DD 格式，前缀匹配当前年月)
            if [[ "${date_name}" == "${CURRENT_YEAR_MONTH}"-* ]]; then
                local target="${dest_dir}/uploads/photos/${child_id}/${date_name}"
                mkdir -p "${target}"
                cp -a "${date_dir}"* "${target}/" 2>/dev/null || true
                found=1
                log_info "已复制照片: ${child_id}/${date_name}"
            fi
        done
    done

    if [[ "${found}" -eq 0 ]]; then
        log_warn "未找到当月 (${CURRENT_YEAR_MONTH}) 照片目录，照片备份为空"
    else
        log_info "当月照片备份完成"
    fi
}

# ---------------------------------------------------------------------------
# 3. 打包为 tar.gz 并存入 weekly/ 目录
# 4. 更新 latest 软链接
# ---------------------------------------------------------------------------
package_and_link() {
    local staging_dir="$1"
    local archive_name="${TIMESTAMP}.tar.gz"
    local archive_path="${WEEKLY_DIR}/${archive_name}"

    log_info "正在打包: ${archive_name}"
    tar -czf "${archive_path}" -C "${staging_dir}" .

    local size
    size="$(du -sh "${archive_path}" | cut -f1)"
    log_info "打包完成: ${archive_path} (${size})"

    # 更新 latest 软链接
    local latest_link="${WEEKLY_DIR}/latest"
    rm -f "${latest_link}"
    ln -s "${archive_name}" "${latest_link}"
    log_info "已更新 latest 软链接 -> ${archive_name}"
}

# ---------------------------------------------------------------------------
# 5. 清理超过保留期限的周备份
# ---------------------------------------------------------------------------
cleanup_old_weeklies() {
    log_info "清理 ${WEEKLY_RETENTION_DAYS} 天前的周备份..."
    local count=0

    while IFS= read -r -d '' old_file; do
        rm -f "${old_file}"
        log_info "已删除过期备份: $(basename "${old_file}")"
        ((count++)) || true
    done < <(find "${WEEKLY_DIR}" -name "*.tar.gz" -type f -mtime "+${WEEKLY_RETENTION_DAYS}" -print0 2>/dev/null)

    if [[ "${count}" -eq 0 ]]; then
        log_info "没有需要清理的过期周备份"
    else
        log_info "共清理 ${count} 个过期周备份"
    fi
}

# ---------------------------------------------------------------------------
# 6. 每月 1 号，将最新周备份复制为月度备份
# ---------------------------------------------------------------------------
promote_monthly() {
    if [[ "${CURRENT_DAY}" != "01" ]]; then
        return 0
    fi

    local latest_link="${WEEKLY_DIR}/latest"
    if [[ ! -L "${latest_link}" ]]; then
        log_warn "latest 软链接不存在，跳过月度备份"
        return 0
    fi

    local latest_file
    latest_file="$(readlink -f "${latest_link}")"
    if [[ ! -f "${latest_file}" ]]; then
        log_warn "latest 指向的文件不存在: ${latest_file}，跳过月度备份"
        return 0
    fi

    local monthly_name="${CURRENT_YEAR_MONTH}.tar.gz"
    local monthly_path="${MONTHLY_DIR}/${monthly_name}"

    cp "${latest_file}" "${monthly_path}"
    log_info "月度备份已生成: ${monthly_path}"
}

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
main() {
    preflight_checks

    # 创建临时暂存目录，退出时自动清理
    STAGING_DIR="$(mktemp -d)"
    trap cleanup EXIT
    log_info "临时暂存目录: ${STAGING_DIR}"

    # 步骤 1：SQLite 热备份
    backup_database "${STAGING_DIR}/kidscheck.db"

    # 步骤 2：当月照片备份
    backup_photos "${STAGING_DIR}"

    # 步骤 3 & 4：打包 + 更新 latest 链接
    package_and_link "${STAGING_DIR}"

    # 步骤 5：清理过期周备份
    cleanup_old_weeklies

    # 步骤 6：每月 1 号生成月度备份
    promote_monthly

    log_info "========== 备份任务完成 =========="
}

main "$@"
