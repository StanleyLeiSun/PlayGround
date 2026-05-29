# SOP: 后台服务发布到线上

## 概述

将本地 backend 代码打包上传到线上服务器，更新依赖并重启服务。全程排除数据库、照片、环境变量等运行时数据，确保不破坏线上状态。

## 前置条件

- 本地代码已提交（`git status` 干净）
- SSH 密钥可免密登录服务器
- 建议发布前先备份线上数据库（参考 `backup-prod-database.md`）

## 连接信息

| 项目 | 值 |
|------|-----|
| 服务器 IP | `47.94.167.238` |
| SSH 用户名 | `admin` |
| 应用目录 | `/opt/kidscheck` |
| 后端代码目录 | `/opt/kidscheck/backend` |
| Python 虚拟环境 | `/opt/kidscheck/venv` |
| 数据库文件 | `/opt/kidscheck/backend/kidscheck_dev.db` |
| 服务名 | `kidscheck`（systemd） |

## 操作步骤

### 1. 确认本地代码状态

```bash
cd KidsCheckApp
git status
git log --oneline -3 -- backend/
```

### 2. 打包后端代码（排除运行时数据）

```bash
tar -czf /tmp/kidscheck_backend_deploy.tar.gz \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='.pytest_cache' \
  --exclude='*.db' \
  --exclude='uploads/photos' \
  --exclude='.venv' \
  --exclude='.env*' \
  --exclude='tests' \
  -C backend .
```

排除项说明：
- `*.db` — 不覆盖线上数据库
- `uploads/photos` — 不覆盖线上照片
- `.env*` — 不覆盖线上环境变量配置
- `.venv` — 不上传本地虚拟环境
- `tests` — 测试代码无需部署

### 3. 上传到服务器

```bash
scp /tmp/kidscheck_backend_deploy.tar.gz admin@47.94.167.238:/tmp/
```

### 4. 远程部署

```bash
ssh admin@47.94.167.238 << 'EOF'
set -euo pipefail

APP_DIR="/opt/kidscheck"
BACKEND_DIR="${APP_DIR}/backend"
VENV_DIR="${APP_DIR}/venv"

# 备份当前代码（便于回滚）
sudo cp -a "${BACKEND_DIR}" "${BACKEND_DIR}.bak_$(date +%Y%m%d%H%M)"

# 解压新代码（覆盖代码文件，不影响 db/photos/.env）
sudo tar -xzf /tmp/kidscheck_backend_deploy.tar.gz -C "${BACKEND_DIR}" --overwrite

# 验证数据库未被破坏
result=$(sqlite3 "${BACKEND_DIR}/kidscheck_dev.db" "PRAGMA integrity_check;")
echo "数据库完整性: $result"
[ "$result" = "ok" ] || exit 1

# 更新依赖
sudo "${VENV_DIR}/bin/pip" install -r "${BACKEND_DIR}/requirements.txt" -q

# 执行迁移（如有）
cd "${BACKEND_DIR}"
sudo "${VENV_DIR}/bin/python" -m alembic upgrade head || echo "迁移跳过（可能已是最新）"

# 重启服务
sudo systemctl restart kidscheck
sleep 2
echo "服务状态: $(sudo systemctl is-active kidscheck)"

# 清理
rm -f /tmp/kidscheck_backend_deploy.tar.gz
EOF
```

### 5. 验证部署

```bash
# 检查服务状态
ssh admin@47.94.167.238 "sudo systemctl is-active kidscheck"

# API 健康检查
curl -s -o /dev/null -w "%{http_code}" http://47.94.167.238/docs
# 预期: 200
```

### 6. 清理本地临时文件

```bash
rm -f /tmp/kidscheck_backend_deploy.tar.gz
```

## 回滚方案

如果发布后出现问题：

```bash
ssh admin@47.94.167.238 << 'EOF'
# 找到最近的备份
ls -lt /opt/kidscheck/backend.bak_* | head -1

# 回滚（替换 YYYYMMDDHHMM 为实际备份时间戳）
sudo rm -rf /opt/kidscheck/backend
sudo mv /opt/kidscheck/backend.bak_YYYYMMDDHHMM /opt/kidscheck/backend
sudo systemctl restart kidscheck
EOF
```

## 注意事项

- 远程服务器未安装 `rsync`，使用 tar + scp 方式部署
- macOS 打包的 tar 在 Linux 解压时会有 `LIBARCHIVE.xattr` 警告，不影响功能
- alembic 迁移如遇多 head 报错，先用 `alembic current` 确认线上版本是否已是最新，如果已是最新可忽略
- 每次部署前会自动备份当前代码到 `backend.bak_时间戳`，定期清理旧备份
