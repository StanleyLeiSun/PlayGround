# KidsCheck 部署脚本设计

## 概述

一个 `scripts/deploy.sh` 脚本，用于在全新 Linux 服务器上一键完成 KidsCheck 后端部署，以及后续代码更新。

- **目标环境**：Linux 服务器（Ubuntu/Debian），已安装 Python 3.10+
- **应用目录**：`/opt/kidscheck`
- **运行方式**：systemd 服务 + Nginx 反向代理
- **代码交付**：文件上传（scp/rsync），非 git

## 目录结构

```
/opt/kidscheck/
├── backend/              # 应用代码（从上传目录拷贝）
│   ├── app/
│   ├── alembic/
│   ├── main.py
│   └── requirements.txt
├── venv/                 # Python 虚拟环境
├── uploads/photos/       # 照片存储
├── kidscheck.db          # SQLite 数据库
└── logs/                 # 应用日志（uvicorn access/error log）
```

## 部署模式

### 初始部署 (`bash deploy.sh`)

1. 安装系统依赖：`sqlite3`、`nginx`（通过 apt-get）
2. 创建 `/opt/kidscheck/` 目录结构
3. 将当前目录的 backend 代码拷贝到 `/opt/kidscheck/backend/`
4. 创建 Python venv + 安装 `requirements.txt`
5. 直接使用仓库中的 `kidscheck.db`（已含 seed 数据）作为数据库
6. 创建 `uploads/photos/` 目录
7. 生成 systemd 服务文件
8. 生成 Nginx 配置文件
9. 启动 systemd 服务 + 重载 Nginx
10. 打印部署结果（访问地址、状态）

### 更新部署 (`bash deploy.sh --update`)

1. 将当前目录的 backend 代码拷贝到 `/opt/kidscheck/backend/`（覆盖）
2. 在 venv 中重新安装依赖（`pip install -r requirements.txt`，处理新增依赖）
3. 重启 systemd 服务
4. 打印更新结果

如果后续有 schema 变更，需手动执行：`cd /opt/kidscheck/backend && /opt/kidscheck/venv/bin/alembic upgrade head`

## systemd 服务

服务文件：`/etc/systemd/system/kidscheck.service`

```ini
[Unit]
Description=KidsCheck API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kidscheck/backend
Environment="PATH=/opt/kidscheck/venv/bin"
ExecStart=/opt/kidscheck/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=append:/opt/kidscheck/logs/uvicorn.log
StandardError=append:/opt/kidscheck/logs/uvicorn.log

[Install]
WantedBy=multi-user.target
```

- 开机自启（`WantedBy=multi-user.target`）
- 崩溃自动重启（`Restart=always`，5 秒后重启）
- 日志输出到 `/opt/kidscheck/logs/uvicorn.log`

## Nginx 配置

配置文件：`/etc/nginx/sites-available/kidscheck`

```nginx
server {
    listen 80;
    server_name _;

    # 照片静态文件
    location /photos/ {
        alias /opt/kidscheck/uploads/photos/;
    }

    # API 反向代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 备份文件下载（需先配置 Basic Auth）
    # include /etc/nginx/snippets/nginx-backup.conf;
}
```

- 照片由 Nginx 直接服务，不经过 Python
- API 请求代理到 uvicorn
- 备份下载路径可选启用（需先配置 htpasswd）

## 配置项

脚本顶部可配置的变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_DIR` | `/opt/kidscheck` | 应用根目录 |
| `APP_PORT` | `8000` | uvicorn 监听端口 |
| `NGINX_SERVER_NAME` | `_` | Nginx server_name |

## 前置条件

- Python 3.10+ 已安装
- 脚本以 root 权限运行
- 代码文件已上传到服务器某个目录

## 文件清单

| 文件 | 用途 |
|------|------|
| `scripts/deploy.sh` | 部署脚本（初始 + 更新） |
| `/etc/systemd/system/kidscheck.service` | systemd 服务文件（脚本生成） |
| `/etc/nginx/sites-available/kidscheck` | Nginx 配置（脚本生成） |
