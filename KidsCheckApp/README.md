# KidsCheckApp

家庭学习打卡助手 — 父母远程设置任务，祖辈现场打卡，积分奖励激励孩子。

## 本地跑起来（推荐顺序）

1. 启动后端（FastAPI）：看 `backend/README.md`
2. 启动 Android 客户端：看 `android/README.md`

## 部署到云服务器

### 前置条件

- Linux 服务器（Ubuntu/Debian），已安装 Python 3.10+
- root 权限

### 初始部署

```bash
# 1. 上传项目文件到服务器
scp -r KidsCheckApp/ root@your-server:/tmp/

# 2. 运行部署脚本
ssh root@your-server "bash /tmp/KidsCheckApp/scripts/deploy.sh"
```

部署完成后：
- API 地址：`http://your-server/`
- 服务管理：`systemctl status/restart/stop kidscheck`
- 查看日志：`tail -f /opt/kidscheck/logs/uvicorn.log`

### 后续更新

```bash
# 1. 上传更新的代码
scp -r backend/ root@your-server:/opt/kidscheck/backend/

# 2. 运行更新脚本
ssh root@your-server "bash /tmp/KidsCheckApp/scripts/deploy.sh --update"
```

如果有数据库 schema 变更，手动执行迁移：
```bash
ssh root@your-server "cd /opt/kidscheck/backend && /opt/kidscheck/venv/bin/alembic upgrade head"
```

### 数据备份

备份脚本每周一凌晨 3 点自动执行（由 setup-backup.sh 配置的 cron 驱动）。

```bash
# 首次配置备份
sudo bash /opt/kidscheck/scripts/setup-backup.sh

# 本地拉取最新备份
python scripts/pull_backup.py --host your-server --user root --key ~/.ssh/id_rsa

# 列出所有备份
python scripts/pull_backup.py --host your-server --user root --key ~/.ssh/id_rsa --list

# 恢复备份
sudo bash /opt/kidscheck/scripts/restore.sh /var/backups/kidscheck/weekly/2026-05-26_03-00.tar.gz
```

