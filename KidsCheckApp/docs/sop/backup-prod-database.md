# SOP: 线上数据库备份到本地

## 概述

通过 SSH 连接线上服务器，使用 SQLite 热备份（`.backup`）生成一致性快照，再通过 SCP 拉取到本地 `db_bak/` 目录。此方式不锁定数据库、不影响线上服务运行。

## 前置条件

- 本地 SSH 密钥已配置，能免密登录服务器
- 远程服务器已安装 `sqlite3`

## 连接信息

| 项目 | 值 |
|------|-----|
| 服务器 IP | `47.94.167.238` |
| SSH 用户名 | `admin` |
| 数据库路径 | `/opt/kidscheck/backend/kidscheck_dev.db` |
| 本地存放目录 | `db_bak/` |

## 操作步骤

### 1. 远程执行热备份

```bash
ssh admin@47.94.167.238 "sqlite3 /opt/kidscheck/backend/kidscheck_dev.db '.backup /tmp/kidscheck_backup.db'"
```

### 2. 拉取备份到本地

```bash
scp admin@47.94.167.238:/tmp/kidscheck_backup.db db_bak/kidscheck_prod_backup_$(date +%Y%m%d).db
```

### 3. 验证备份完整性

```bash
sqlite3 db_bak/kidscheck_prod_backup_$(date +%Y%m%d).db "PRAGMA integrity_check;"
```

预期输出：`ok`

### 4.（可选）清理远程临时文件

```bash
ssh admin@47.94.167.238 "rm -f /tmp/kidscheck_backup.db"
```

## 一键脚本

```bash
#!/usr/bin/env bash
set -euo pipefail

SERVER="admin@47.94.167.238"
REMOTE_DB="/opt/kidscheck/backend/kidscheck_dev.db"
REMOTE_TMP="/tmp/kidscheck_backup.db"
LOCAL_DIR="db_bak"
LOCAL_FILE="${LOCAL_DIR}/kidscheck_prod_backup_$(date +%Y%m%d).db"

mkdir -p "$LOCAL_DIR"

echo "1. 远程热备份..."
ssh "$SERVER" "sqlite3 ${REMOTE_DB} '.backup ${REMOTE_TMP}'"

echo "2. 拉取到本地..."
scp "$SERVER:${REMOTE_TMP}" "$LOCAL_FILE"

echo "3. 验证完整性..."
result=$(sqlite3 "$LOCAL_FILE" "PRAGMA integrity_check;")
if [[ "$result" == "ok" ]]; then
    echo "备份成功: $LOCAL_FILE ($(du -h "$LOCAL_FILE" | cut -f1))"
else
    echo "错误: 完整性检查失败 - $result" >&2
    exit 1
fi

echo "4. 清理远程临时文件..."
ssh "$SERVER" "rm -f ${REMOTE_TMP}"

echo "完成"
```

## 注意事项

- `sqlite3 .backup` 是在线热备份，利用 SQLite 的 WAL 机制保证一致性
- 备份文件命名格式：`kidscheck_prod_backup_YYYYMMDD.db`
- 项目还配有自动周备份（cron 每周一凌晨 3 点），可用 `scripts/pull_backup.py` 拉取历史备份
