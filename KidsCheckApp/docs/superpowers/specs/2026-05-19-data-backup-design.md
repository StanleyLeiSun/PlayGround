# KidsCheck 数据备份设计

## 概述

为 KidsCheck 云服务器部署提供自动化数据备份方案，保护 SQLite 数据库和用户上传的照片文件。

- **部署方式**：云服务器（阿里云/腾讯云 VPS）
- **备份范围**：SQLite 数据库（全量）+ 当月照片（增量）
- **备份频率**：每周一凌晨 3 点，每月 1 号额外归档
- **保留策略**：周备份保留 12 周，月备份永久保留
- **恢复方式**：按备份点恢复

## 备份目录结构

```
/var/backups/kidscheck/
├── weekly/
│   ├── 2026-05-26_03-00.tar.gz
│   ├── 2026-06-02_03-00.tar.gz
│   └── ...
├── monthly/
│   ├── 2026-05.tar.gz
│   ├── 2026-06.tar.gz
│   └── ...
└── latest -> weekly/2026-06-02_03-00.tar.gz
```

每个 `.tar.gz` 包含：
- `kidscheck.db` — SQLite 数据库完整副本
- `uploads/photos/` — 最近 30 天的照片文件

`latest` 符号链接始终指向最新的周备份，方便快速下载。

## 备份脚本

文件：`scripts/backup.sh`

核心逻辑：

1. 使用 `sqlite3 .backup` 进行在线热备份（不影响应用运行）
2. 按目录名匹配当月照片，保留 `uploads/photos/{child_id}/{YYYY-MM-DD}/` 完整目录结构
3. 打包压缩为 `YYYY-MM-DD_HH-MM.tar.gz` 存入 `weekly/`
4. 更新 `latest` 符号链接
5. 清理超过 84 天（12 周）的周备份文件
6. 每月 1 号将 latest 拷贝到 `monthly/YYYY-MM.tar.gz`

照片实际存储路径：`uploads/photos/{child_id}/{YYYY-MM-DD}/{uuid}.jpg`

## 远程拉取脚本

文件：`scripts/pull_backup.py`

通过 SSH/SCP 从云服务器拉取备份文件到本地。

用法：
- `python pull_backup.py --host <server> --user <user> --key <key>` — 拉取最新备份
- `python pull_backup.py --host <server> --user <user> --name <filename>` — 拉取指定备份
- `python pull_backup.py --host <server> --user <user> --list` — 列出所有可用备份

依赖：`paramiko`（Python SSH 库）

## Nginx 配置

备份目录通过 Nginx 提供 HTTP 访问，使用 Basic Auth 保护：

```nginx
location /backups/ {
    auth_basic "KidsCheck Backup";
    auth_basic_user_file /etc/nginx/.backup_htpasswd;
    autoindex on;
    alias /var/backups/kidscheck/;
}
```

密码文件生成：`htpasswd -c /etc/nginx/.backup_htpasswd backup-user`

## Cron 调度

```cron
# 每周一凌晨 3 点执行备份
0 3 * * 1 /opt/kidscheck/scripts/backup.sh >> /var/log/kidscheck-backup.log 2>&1
```

## 恢复流程

```bash
# 1. 解压备份到临时目录
tar xzf 2026-05-26_03-00.tar.gz -C /tmp/restore

# 2. 停止应用
systemctl stop kidscheck

# 3. 恢复数据库（覆盖现有文件）
cp /tmp/restore/kidscheck.db /opt/kidscheck/kidscheck.db

# 4. 恢复照片（合并到现有目录，不删除已有文件）
cp -r /tmp/restore/photos/* /opt/kidscheck/uploads/photos/

# 5. 重启应用
systemctl start kidscheck
```

恢复注意事项：
- 数据库直接覆盖即可（SQLite 单文件）
- 照片使用合并拷贝，不会丢失备份之后新上传的照片
- 如果需要完整回滚，先清空 `uploads/photos/` 再恢复

## 文件清单

| 文件 | 用途 |
|------|------|
| `scripts/backup.sh` | 备份脚本，由 cron 调用 |
| `scripts/pull_backup.py` | 远程拉取脚本，在本地机器运行 |
| `/var/backups/kidscheck/` | 备份文件存储目录 |
| `/var/log/kidscheck-backup.log` | 备份执行日志 |
| `/etc/nginx/.backup_htpasswd` | Nginx Basic Auth 密码文件 |
