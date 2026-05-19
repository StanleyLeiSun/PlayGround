# Deployment Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a single `scripts/deploy.sh` that deploys the KidsCheck backend to a Linux server with systemd + Nginx, and supports `--update` mode for subsequent code updates.

**Architecture:** One shell script with two modes: initial deploy (install deps, create venv, copy code, generate configs, start services) and update deploy (copy code, reinstall deps, restart service). Configs are generated inline, not from templates.

**Tech Stack:** Bash, systemd, Nginx, Python venv, uvicorn

---

### Task 1: Create deploy.sh with initial deployment mode

**Files:**
- Create: `scripts/deploy.sh`

- [ ] **Step 1: Write the complete deploy script**

Create `scripts/deploy.sh` with the following content:

```bash
#!/usr/bin/env bash
# =============================================================================
# KidsCheck 后端部署脚本
# 用法：
#   bash deploy.sh           # 初始部署
#   bash deploy.sh --update  # 更新代码并重启服务
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# 可配置参数
# ---------------------------------------------------------------------------
APP_DIR="${APP_DIR:-/opt/kidscheck}"
APP_PORT="${APP_PORT:-8000}"
NGINX_SERVER_NAME="${NGINX_SERVER_NAME:-_}"

# ---------------------------------------------------------------------------
# 内部路径
# ---------------------------------------------------------------------------
BACKEND_DIR="${APP_DIR}/backend"
VENV_DIR="${APP_DIR}/venv"
DB_FILE="${APP_DIR}/kidscheck.db"
PHOTOS_DIR="${APP_DIR}/uploads/photos"
LOG_DIR="${APP_DIR}/logs"
SERVICE_FILE="/etc/systemd/system/kidscheck.service"
NGINX_CONF="/etc/nginx/sites-available/kidscheck"
NGINX_ENABLED="/etc/nginx/sites-enabled/kidscheck"

# 源目录（脚本所在目录的上级，即项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_BACKEND="${PROJECT_ROOT}/backend"
SOURCE_DB="${PROJECT_ROOT}/backend/kidscheck.db"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# ---------------------------------------------------------------------------
# 前置检查
# ---------------------------------------------------------------------------
preflight_checks() {
    if [[ $EUID -ne 0 ]]; then
        echo "错误：请以 root 权限运行此脚本" >&2
        exit 1
    fi

    if ! command -v python3 &>/dev/null; then
        echo "错误：未找到 python3，请先安装 Python 3.10+" >&2
        exit 1
    fi

    local py_version
    py_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local py_major py_minor
    py_major=$(echo "$py_version" | cut -d. -f1)
    py_minor=$(echo "$py_version" | cut -d. -f2)
    if [[ "$py_major" -lt 3 ]] || { [[ "$py_major" -eq 3 ]] && [[ "$py_minor" -lt 10 ]]; }; then
        echo "错误：需要 Python 3.10+，当前版本 $py_version" >&2
        exit 1
    fi

    if [[ ! -d "$SOURCE_BACKEND" ]]; then
        echo "错误：未找到后端代码目录 $SOURCE_BACKEND" >&2
        exit 1
    fi

    log "前置检查通过 (Python $py_version)"
}

# ---------------------------------------------------------------------------
# 安装系统依赖
# ---------------------------------------------------------------------------
install_system_deps() {
    log "安装系统依赖..."
    apt-get update -qq
    apt-get install -y -qq sqlite3 nginx
    log "系统依赖安装完成"
}

# ---------------------------------------------------------------------------
# 创建目录结构
# ---------------------------------------------------------------------------
create_directories() {
    log "创建目录结构..."
    mkdir -p "${BACKEND_DIR}" "${VENV_DIR}" "${PHOTOS_DIR}" "${LOG_DIR}"
    log "目录结构: ${APP_DIR}/"
}

# ---------------------------------------------------------------------------
# 拷贝后端代码
# ---------------------------------------------------------------------------
copy_backend_code() {
    log "拷贝后端代码到 ${BACKEND_DIR}..."
    rsync -a --delete \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='kidscheck.db' \
        "${SOURCE_BACKEND}/" "${BACKEND_DIR}/"
    log "代码拷贝完成"
}

# ---------------------------------------------------------------------------
# 创建 Python 虚拟环境 + 安装依赖
# ---------------------------------------------------------------------------
setup_python_venv() {
    log "创建 Python 虚拟环境..."
    python3 -m venv "${VENV_DIR}"

    log "安装 Python 依赖..."
    "${VENV_DIR}/bin/pip" install --upgrade pip -q
    "${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt" -q
    log "Python 依赖安装完成"
}

# ---------------------------------------------------------------------------
# 初始化数据库
# ---------------------------------------------------------------------------
init_database() {
    if [[ -f "$DB_FILE" ]]; then
        log "数据库文件已存在，跳过初始化"
        return 0
    fi

    if [[ -f "$SOURCE_DB" ]]; then
        log "拷贝数据库文件（含 seed 数据）..."
        cp "$SOURCE_DB" "$DB_FILE"
        log "数据库初始化完成"
    else
        log "警告：未找到数据库文件 ${SOURCE_DB}，跳过数据库初始化"
    fi
}

# ---------------------------------------------------------------------------
# 生成 systemd 服务文件
# ---------------------------------------------------------------------------
generate_systemd_service() {
    log "生成 systemd 服务文件..."
    cat > "$SERVICE_FILE" << 'UNIT'
[Unit]
Description=KidsCheck API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=APP_DIR_PLACEHOLDER/backend
Environment="PATH=APP_DIR_PLACEHOLDER/venv/bin"
ExecStart=APP_DIR_PLACEHOLDER/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port APP_PORT_PLACEHOLDER
Restart=always
RestartSec=5
StandardOutput=append:APP_DIR_PLACEHOLDER/logs/uvicorn.log
StandardError=append:APP_DIR_PLACEHOLDER/logs/uvicorn.log

[Install]
WantedBy=multi-user.target
UNIT

    # 替换占位符
    sed -i "s|APP_DIR_PLACEHOLDER|${APP_DIR}|g" "$SERVICE_FILE"
    sed -i "s|APP_PORT_PLACEHOLDER|${APP_PORT}|g" "$SERVICE_FILE"

    systemctl daemon-reload
    log "systemd 服务文件已生成: ${SERVICE_FILE}"
}

# ---------------------------------------------------------------------------
# 生成 Nginx 配置
# ---------------------------------------------------------------------------
generate_nginx_config() {
    log "生成 Nginx 配置..."
    cat > "$NGINX_CONF" << 'NGINX'
server {
    listen 80;
    server_name SERVER_NAME_PLACEHOLDER;

    # 照片静态文件
    location /photos/ {
        alias APP_DIR_PLACEHOLDER/uploads/photos/;
    }

    # API 反向代理
    location / {
        proxy_pass http://127.0.0.1:APP_PORT_PLACEHOLDER;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 备份文件下载（需先配置 Basic Auth）
    # include /etc/nginx/snippets/nginx-backup.conf;
}
NGINX

    # 替换占位符
    sed -i "s|SERVER_NAME_PLACEHOLDER|${NGINX_SERVER_NAME}|g" "$NGINX_CONF"
    sed -i "s|APP_DIR_PLACEHOLDER|${APP_DIR}|g" "$NGINX_CONF"
    sed -i "s|APP_PORT_PLACEHOLDER|${APP_PORT}|g" "$NGINX_CONF"

    # 启用站点
    ln -sf "$NGINX_CONF" "$NGINX_ENABLED"

    # 移除默认站点（如果存在）
    rm -f /etc/nginx/sites-enabled/default

    # 测试 Nginx 配置
    nginx -t
    log "Nginx 配置已生成: ${NGINX_CONF}"
}

# ---------------------------------------------------------------------------
# 启动服务
# ---------------------------------------------------------------------------
start_services() {
    log "启动服务..."
    systemctl enable kidscheck
    systemctl restart kidscheck
    systemctl reload nginx
    log "服务已启动"
}

# ---------------------------------------------------------------------------
# 打印部署结果
# ---------------------------------------------------------------------------
print_result() {
    local status
    status=$(systemctl is-active kidscheck 2>/dev/null || echo "inactive")

    echo ""
    echo "============================================"
    echo "  KidsCheck 部署完成"
    echo "============================================"
    echo "  应用目录:  ${APP_DIR}"
    echo "  服务状态:  ${status}"
    echo "  监听端口:  ${APP_PORT}"
    echo "  API 地址:  http://$(hostname -I | awk '{print $1}')/"
    echo "  日志文件:  ${LOG_DIR}/uvicorn.log"
    echo "  数据库:    ${DB_FILE}"
    echo "============================================"
    echo ""
    echo "管理命令："
    echo "  查看状态:  systemctl status kidscheck"
    echo "  查看日志:  tail -f ${LOG_DIR}/uvicorn.log"
    echo "  重启服务:  systemctl restart kidscheck"
    echo "  停止服务:  systemctl stop kidscheck"
    echo ""
}

# ---------------------------------------------------------------------------
# 初始部署
# ---------------------------------------------------------------------------
deploy_fresh() {
    log "========== 初始部署开始 =========="
    preflight_checks
    install_system_deps
    create_directories
    copy_backend_code
    setup_python_venv
    init_database
    generate_systemd_service
    generate_nginx_config
    start_services
    print_result
    log "========== 初始部署完成 =========="
}

# ---------------------------------------------------------------------------
# 更新部署
# ---------------------------------------------------------------------------
deploy_update() {
    log "========== 更新部署开始 =========="

    if [[ ! -d "$BACKEND_DIR" ]]; then
        echo "错误：未找到已部署的应用，请先执行初始部署" >&2
        exit 1
    fi

    copy_backend_code

    log "更新 Python 依赖..."
    "${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt" -q
    log "Python 依赖更新完成"

    log "重启服务..."
    systemctl restart kidscheck
    local status
    status=$(systemctl is-active kidscheck 2>/dev/null || echo "inactive")

    echo ""
    echo "============================================"
    echo "  KidsCheck 更新完成"
    echo "============================================"
    echo "  服务状态:  ${status}"
    echo "============================================"
    echo ""
    log "========== 更新部署完成 =========="
}

# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
main() {
    if [[ "${1:-}" == "--update" ]]; then
        deploy_update
    else
        deploy_fresh
    fi
}

main "$@"
```

- [ ] **Step 2: Make the script executable**

```bash
chmod +x scripts/deploy.sh
```

- [ ] **Step 3: Verify the script syntax**

```bash
bash -n scripts/deploy.sh
```

Expected: no output (syntax valid).

- [ ] **Step 4: Commit**

```bash
git add scripts/deploy.sh
git commit -m "feat: add deployment script for Linux server with systemd + Nginx"
```
