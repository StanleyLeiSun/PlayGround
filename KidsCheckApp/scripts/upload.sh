#!/usr/bin/env bash
# 上传 tar.gz 到服务器并解压部署
# 用法: bash scripts/upload.sh <tar.gz文件> <user@host>
set -euo pipefail

ARCHIVE="${1:?用法: $0 <tar.gz文件> <user@host>}"
REMOTE="${2:?用法: $0 <tar.gz文件> <user@host>}"
APP_DIR="/opt/kidscheck"
REMOTE_TMP="/tmp/kidscheck_deploy.tar.gz"

if [[ ! -f "$ARCHIVE" ]]; then
    echo "错误: 文件不存在 $ARCHIVE" >&2
    exit 1
fi

echo "上传 ${ARCHIVE} -> ${REMOTE}:${REMOTE_TMP}"
scp "$ARCHIVE" "${REMOTE}:${REMOTE_TMP}"

echo "远程解压并重启服务..."
ssh "$REMOTE" bash -s "$APP_DIR" "$REMOTE_TMP" << 'REMOTE_SCRIPT'
set -euo pipefail
APP_DIR="$1"
REMOTE_TMP="$2"

sudo mkdir -p "$APP_DIR"
sudo tar -xzf "$REMOTE_TMP" -C "$APP_DIR" --strip-components=0
rm -f "$REMOTE_TMP"

if [[ -d "${APP_DIR}/venv" ]]; then
    echo "更新 Python 依赖..."
    sudo "${APP_DIR}/venv/bin/pip" install -r "${APP_DIR}/backend/requirements.txt" -q
fi

if sudo systemctl is-active --quiet kidscheck 2>/dev/null; then
    echo "重启服务..."
    sudo systemctl restart kidscheck
    echo "服务状态: $(sudo systemctl is-active kidscheck)"
else
    echo "提示: kidscheck 服务未运行，如需首次部署请执行 deploy_prod.sh"
fi

echo "部署完成"
REMOTE_SCRIPT

echo "全部完成"
