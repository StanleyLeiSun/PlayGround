#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-8000}"

if ! command -v python >/dev/null 2>&1; then
  echo "未找到 python：请先安装 Python 3.11+ 并确保已加入 PATH。" >&2
  exit 1
fi

cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

PY="./.venv/bin/python"

"$PY" -m pip install -U pip
"$PY" -m pip install -r requirements.txt
"$PY" -m alembic upgrade head
"$PY" -m uvicorn app.main:app --reload --host 0.0.0.0 --port "$PORT"

