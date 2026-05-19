param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "未找到 python：请先安装 Python 3.11+ 并确保已加入 PATH。"
  exit 1
}

Set-Location $PSScriptRoot\..

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

$py = Join-Path (Resolve-Path ".venv") "Scripts\\python.exe"

& $py -m pip install -U pip
& $py -m pip install -r requirements.txt
& $py -m alembic upgrade head
& $py -m uvicorn app.main:app --reload --host 0.0.0.0 --port $Port

