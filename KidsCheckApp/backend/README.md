# KidsCheck Backend（FastAPI）

## 先决条件

- Windows / macOS / Linux
- Python 3.11+（建议 3.11 或 3.12）

## 一键启动（Windows PowerShell）

在 `backend` 目录下执行：

```powershell
.\scripts\dev.ps1
```

如果提示“禁止运行脚本”（ExecutionPolicy），用下面方式启动一次即可：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

也可以用 `cmd` 方式启动（不受 PowerShell ExecutionPolicy 影响）：

```bat
.\scripts\dev.cmd
```

启动后访问：

- API Root：`http://127.0.0.1:8000/`
- Swagger：`http://127.0.0.1:8000/docs`

## 手动启动（通用）

在 `backend` 目录下执行：

```bash
python -m venv .venv
```

Windows：

```powershell
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

macOS / Linux：

```bash
./.venv/bin/python -m pip install -U pip
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m alembic upgrade head
./.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 数据库说明

默认使用 SQLite（`backend/kidscheck.db`），开箱即用。

如需切换到 Postgres，设置环境变量 `DATABASE_URL`（示例见 `.env.example`），然后重新执行：

```bash
python -m pip install -r requirements-postgres.txt
python -m alembic upgrade head
```
