#!/usr/bin/env bash
# 本地打包脚本：将后端代码打包为 tar.gz
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
ARCHIVE_NAME="kidscheck_${TIMESTAMP}.tar.gz"
OUTPUT_DIR="${PROJECT_ROOT}/dist"

mkdir -p "$OUTPUT_DIR"

echo "打包中..."
tar -czf "${OUTPUT_DIR}/${ARCHIVE_NAME}" \
    -C "$PROJECT_ROOT" \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.venv' \
    --exclude='*.db' \
    --exclude='uploads' \
    --exclude='.env.prod' \
    --exclude='test_*.db' \
    backend/ scripts/

echo "打包完成: ${OUTPUT_DIR}/${ARCHIVE_NAME}"
ls -lh "${OUTPUT_DIR}/${ARCHIVE_NAME}"
