#!/usr/bin/env bash
set -euo pipefail

export APP_ENV=prod

if ! command -v python3 >/dev/null 2>&1; then
  echo "未找到 python3：请先安装 Python 3.11+ 并确保已加入 PATH。" >&2
  exit 1
fi

cd "$(dirname "$0")/.."

if [ ! -f .env.prod ]; then
  echo "❌ .env.prod 不存在。请从 .env.prod.example 复制并填写配置。" >&2
  exit 1
fi

set -a; source .env.prod; set +a

PORT="${1:-8000}"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

PY="./.venv/bin/python"

"$PY" -m pip install -U pip -q
"$PY" -m pip install -r requirements.txt -q
"$PY" -m alembic upgrade head
"$PY" -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 2
