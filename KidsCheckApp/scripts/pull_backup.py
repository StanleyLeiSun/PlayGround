#!/usr/bin/env python3
"""从远程服务器拉取 KidsCheck 备份文件。

支持三种模式：
  1. --list          列出远程 weekly/ 目录下所有 .tar.gz 备份
  2. 默认（无 --name）  拉取 latest 符号链接指向的最新备份
  3. --name <文件名>   拉取指定备份文件

依赖：pip install paramiko
"""

import argparse
import os
import sys
from typing import List, Optional

try:
    import paramiko
except ImportError:
    print("错误：paramiko 未安装，请执行 'pip install paramiko' 后重试。")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="从远程服务器拉取 KidsCheck 周备份文件。"
    )
    parser.add_argument(
        "--host", required=True, help="服务器主机名或 IP 地址"
    )
    parser.add_argument(
        "--user", default="root", help="SSH 用户名（默认 root）"
    )
    parser.add_argument(
        "--key", help="SSH 私钥文件路径"
    )
    parser.add_argument(
        "--password", help="SSH 密码（与 --key 二选一）"
    )
    parser.add_argument(
        "--remote-dir",
        default="/var/backups/kidscheck",
        help="远程备份根目录（默认 /var/backups/kidscheck）",
    )
    parser.add_argument(
        "--local-dir",
        default=".",
        help="本地保存目录（默认当前目录）",
    )
    parser.add_argument(
        "--name", help="要拉取的备份文件名（与 --list 互斥）"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_backups",
        help="列出可用备份并退出（与 --name 互斥）",
    )

    args = parser.parse_args()

    # 至少需要提供 --key 或 --password 之一
    if not args.key and not args.password:
        parser.error("必须提供 --key 或 --password 之一用于认证。")

    # --list 与 --name 互斥
    if args.list_backups and args.name:
        parser.error("--list 与 --name 互斥，请只使用其中一个。")

    return args


def create_ssh_client(
    host: str, user: str, key_path: Optional[str], password: Optional[str]
) -> paramiko.SSHClient:
    """创建并返回已连接的 SSH 客户端。"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs: dict = {"hostname": host, "username": user}
    if key_path:
        connect_kwargs["key_filename"] = key_path
    else:
        connect_kwargs["password"] = password

    try:
        client.connect(**connect_kwargs)
    except paramiko.AuthenticationException:
        print(f"错误：认证失败，请检查用户名/密码或密钥。")
        sys.exit(1)
    except paramiko.SSHException as exc:
        print(f"错误：SSH 连接异常 - {exc}")
        sys.exit(1)
    except OSError as exc:
        print(f"错误：无法连接到 {host} - {exc}")
        sys.exit(1)

    return client


def list_remote_backups(sftp: paramiko.SFTPClient, weekly_dir: str) -> List[str]:
    """列出远程 weekly/ 目录下所有 .tar.gz 文件。"""
    try:
        entries = sftp.listdir(weekly_dir)
    except FileNotFoundError:
        print(f"错误：远程目录不存在 - {weekly_dir}")
        sys.exit(1)

    backups = sorted(f for f in entries if f.endswith(".tar.gz"))
    return backups


def resolve_latest_link(sftp: paramiko.SFTPClient, weekly_dir: str) -> str:
    """解析 latest 符号链接，返回实际文件名。"""
    latest_path = f"{weekly_dir}/latest"
    try:
        real_path = sftp.normalize(latest_path)
        # 从绝对路径中提取文件名
        filename = os.path.basename(real_path)
        return filename
    except FileNotFoundError:
        print("错误：远程 latest 符号链接不存在，请先执行备份。")
        sys.exit(1)
    except OSError as exc:
        print(f"错误：无法解析 latest 链接 - {exc}")
        sys.exit(1)


def download_file(
    sftp: paramiko.SFTPClient,
    remote_path: str,
    local_path: str,
) -> None:
    """通过 SFTP 下载文件并显示大小信息。"""
    try:
        stat = sftp.stat(remote_path)
    except FileNotFoundError:
        print(f"错误：远程文件不存在 - {remote_path}")
        sys.exit(1)

    file_size = stat.st_size
    size_mb = file_size / (1024 * 1024)
    print(f"正在下载：{os.path.basename(remote_path)}（{size_mb:.2f} MB）")

    try:
        sftp.get(remote_path, local_path, callback=_make_progress(file_size))
    except OSError as exc:
        print(f"错误：下载失败 - {exc}")
        sys.exit(1)

    # 打印换行（进度回调结束后）
    print()
    local_size = os.path.getsize(local_path)
    print(f"下载完成：{local_path}（{local_size / (1024 * 1024):.2f} MB）")


def _make_progress(total_size: int):
    """返回一个 SFTP 回调函数，用于打印下载进度。"""
    last_percent = [-1]

    def callback(bytes_transferred: int, _total: int) -> None:
        percent = int(bytes_transferred * 100 / total_size) if total_size else 0
        if percent != last_percent[0]:
            last_percent[0] = percent
            downloaded_mb = bytes_transferred / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            print(
                f"\r  进度：{percent:3d}%  "
                f"({downloaded_mb:.2f} / {total_mb:.2f} MB)",
                end="",
                flush=True,
            )

    return callback


def main() -> None:
    args = parse_args()
    weekly_dir = f"{args.remote_dir.rstrip('/')}/weekly"

    # 确保本地目录存在
    os.makedirs(args.local_dir, exist_ok=True)

    ssh = create_ssh_client(args.host, args.user, args.key, args.password)
    sftp = None

    try:
        sftp = ssh.open_sftp()

        # 模式 1：列出备份
        if args.list_backups:
            backups = list_remote_backups(sftp, weekly_dir)
            if not backups:
                print("未找到任何备份文件。")
                sys.exit(0)
            print(f"在 {weekly_dir} 中找到 {len(backups)} 个备份：")
            for name in backups:
                print(f"  - {name}")
            return

        # 模式 2/3：拉取文件
        if args.name:
            filename = args.name
        else:
            filename = resolve_latest_link(sftp, weekly_dir)
            print(f"最新备份：{filename}")

        remote_path = f"{weekly_dir}/{filename}"
        local_path = os.path.join(args.local_dir, filename)

        download_file(sftp, remote_path, local_path)

    finally:
        if sftp is not None:
            sftp.close()
        ssh.close()


if __name__ == "__main__":
    main()
