# Data Backup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automated weekly backup of SQLite database and photos, with remote pull capability and Nginx-protected download.

**Architecture:** Shell script for backup (cron-driven), Python script for remote pull via SSH/SCP, Nginx Basic Auth for download access. Backup files stored as timestamped `.tar.gz` archives.

**Tech Stack:** Bash, SQLite3, Python 3, paramiko, Nginx

---

### Task 1: Create backup shell script

**Files:**
- Create: `scripts/backup.sh`

- [ ] **Step 1: Create the scripts directory**

```bash
mkdir -p scripts
```

- [ ] **Step 2: Write the backup script**

Create `scripts/backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

# --- Configuration (override via environment variables) ---
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/kidscheck}"
APP_DIR="${APP_DIR:-/opt/kidscheck}"
DB_PATH="${APP_DIR}/kidscheck.db"
PHOTOS_PATH="${APP_DIR}/uploads/photos"
LOG_FILE="${LOG_FILE:-/var/log/kidscheck-backup.log}"
WEEKLY_RETENTION_DAYS="${WEEKLY_RETENTION_DAYS:-84}"

# --- Derived paths ---
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
MONTH_PREFIX=$(date +%Y-%m)
WEEKLY_DIR="${BACKUP_ROOT}/weekly"
MONTHLY_DIR="${BACKUP_ROOT}/monthly"
TMPDIR=$(mktemp -d)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

cleanup() {
    rm -rf "$TMPDIR"
}
trap cleanup EXIT

# --- Ensure directories exist ---
mkdir -p "$WEEKLY_DIR" "$MONTHLY_DIR"

log "Starting backup: ${TIMESTAMP}"

# --- 1. SQLite online backup ---
log "Backing up database..."
if [ ! -f "$DB_PATH" ]; then
    log "ERROR: Database file not found: $DB_PATH"
    exit 1
fi
sqlite3 "$DB_PATH" ".backup '${TMPDIR}/kidscheck.db'"
log "Database backup complete."

# --- 2. Copy current month photos ---
log "Copying photos for ${MONTH_PREFIX}..."
PHOTO_COUNT=0
if [ -d "$PHOTOS_PATH" ]; then
    for child_dir in "$PHOTOS_PATH"/*/; do
        [ -d "$child_dir" ] || continue
        child_id=$(basename "$child_dir")
        for date_dir in "$child_dir"${MONTH_PREFIX}-*/; do
            [ -d "$date_dir" ] || continue
            date_name=$(basename "$date_dir")
            dest="${TMPDIR}/uploads/photos/${child_id}/${date_name}"
            mkdir -p "$dest"
            cp -r "$date_dir"/* "$dest/" 2>/dev/null || true
            count=$(find "$dest" -type f | wc -l)
            PHOTO_COUNT=$((PHOTO_COUNT + count))
        done
    done
fi
log "Photos copied: ${PHOTO_COUNT} files."

# --- 3. Create archive ---
ARCHIVE_NAME="${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${WEEKLY_DIR}/${ARCHIVE_NAME}"
log "Creating archive: ${ARCHIVE_NAME}..."
tar czf "$ARCHIVE_PATH" -C "$TMPDIR" .
ARCHIVE_SIZE=$(du -h "$ARCHIVE_PATH" | cut -f1)
log "Archive created: ${ARCHIVE_SIZE}"

# --- 4. Update latest symlink ---
ln -sf "weekly/${ARCHIVE_NAME}" "${BACKUP_ROOT}/latest"
log "Updated latest symlink."

# --- 5. Clean old weekly backups ---
DELETED=$(find "$WEEKLY_DIR" -name "*.tar.gz" -mtime +${WEEKLY_RETENTION_DAYS} -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    log "Cleaned ${DELETED} old weekly backups (>${WEEKLY_RETENTION_DAYS} days)."
fi

# --- 6. Monthly archive on the 1st ---
if [ "$(date +%d)" = "01" ]; then
    MONTHLY_NAME="${MONTH_PREFIX}.tar.gz"
    cp "$ARCHIVE_PATH" "${MONTHLY_DIR}/${MONTHLY_NAME}"
    log "Monthly archive created: ${MONTHLY_NAME}"
fi

log "Backup complete: ${ARCHIVE_PATH}"
```

- [ ] **Step 3: Make the script executable**

```bash
chmod +x scripts/backup.sh
```

- [ ] **Step 4: Test the script locally (dry run)**

Set environment variables to use local paths and run:

```bash
APP_DIR=. BACKUP_ROOT=/tmp/kidscheck-backup LOG_FILE=/tmp/backup.log bash scripts/backup.sh
```

Expected output should show backup steps completing. Check `/tmp/kidscheck-backup/weekly/` for the archive.

- [ ] **Step 5: Verify archive contents**

```bash
tar tzf /tmp/kidscheck-backup/weekly/*.tar.gz | head -20
```

Should list `kidscheck.db` and any photo files.

- [ ] **Step 6: Commit**

```bash
git add scripts/backup.sh
git commit -m "feat: add automated backup script for database and photos"
```

---

### Task 2: Create remote pull script

**Files:**
- Create: `scripts/pull_backup.py`

- [ ] **Step 1: Write the pull script**

Create `scripts/pull_backup.py`:

```python
#!/usr/bin/env python3
"""Pull backup files from KidsCheck cloud server via SSH/SCP."""
import argparse
import sys
from pathlib import Path

import paramiko


def create_client(host: str, user: str, key_path: str | None = None, password: str | None = None) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs = {"hostname": host, "username": user}
    if key_path:
        kwargs["key_filename"] = key_path
    elif password:
        kwargs["password"] = password
    client.connect(**kwargs)
    return client


def list_backups(client: paramiko.SSHClient, remote_dir: str) -> list[str]:
    """List available backup files in weekly/ directory."""
    stdin, stdout, stderr = client.exec_command(f"ls -1 {remote_dir}/weekly/*.tar.gz 2>/dev/null")
    files = stdout.read().decode().strip().split("\n")
    return [Path(f).name for f in files if f]


def pull_file(client: paramiko.SSHClient, remote_path: str, local_path: str) -> None:
    """Download a file via SFTP."""
    sftp = client.open_sftp()
    try:
        remote_size = sftp.stat(remote_path).st_size
        print(f"Downloading {Path(remote_path).name} ({remote_size / 1024 / 1024:.1f} MB)...")
        sftp.get(remote_path, local_path)
        print(f"Saved to {local_path}")
    finally:
        sftp.close()


def main():
    parser = argparse.ArgumentParser(description="Pull KidsCheck backup from cloud server")
    parser.add_argument("--host", required=True, help="Server hostname or IP")
    parser.add_argument("--user", default="root", help="SSH username (default: root)")
    parser.add_argument("--key", help="Path to SSH private key")
    parser.add_argument("--password", help="SSH password (use --key instead)")
    parser.add_argument("--remote-dir", default="/var/backups/kidscheck", help="Remote backup directory")
    parser.add_argument("--local-dir", default=".", help="Local directory to save backup")
    parser.add_argument("--name", help="Specific backup filename to pull")
    parser.add_argument("--list", action="store_true", help="List available backups and exit")
    args = parser.parse_args()

    if not args.key and not args.password:
        print("Error: provide --key or --password", file=sys.stderr)
        sys.exit(1)

    client = create_client(args.host, args.user, args.key, args.password)
    try:
        if args.list:
            backups = list_backups(client, args.remote_dir)
            if not backups:
                print("No backups found.")
            else:
                print("Available backups:")
                for b in sorted(backups, reverse=True):
                    print(f"  {b}")
            return

        if args.name:
            remote_path = f"{args.remote_dir}/weekly/{args.name}"
            local_path = str(Path(args.local_dir) / args.name)
        else:
            # Pull latest
            stdin, stdout, stderr = client.exec_command(f"readlink {args.remote_dir}/latest")
            latest_rel = stdout.read().decode().strip()
            if not latest_rel:
                print("Error: no latest symlink found", file=sys.stderr)
                sys.exit(1)
            remote_path = f"{args.remote_dir}/{latest_rel}"
            local_path = str(Path(args.local_dir) / Path(latest_rel).name)

        pull_file(client, remote_path, local_path)
    finally:
        client.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Install dependency**

Add `paramiko` to `requirements.txt` or install directly:

```bash
pip install paramiko
```

- [ ] **Step 3: Test --help output**

```bash
python scripts/pull_backup.py --help
```

Expected: shows usage with `--host`, `--user`, `--key`, `--list`, `--name` options.

- [ ] **Step 4: Commit**

```bash
git add scripts/pull_backup.py
git commit -m "feat: add remote backup pull script via SSH/SCP"
```

---

### Task 3: Create restore script

**Files:**
- Create: `scripts/restore.sh`

- [ ] **Step 1: Write the restore script**

Create `scripts/restore.sh`:

```bash
#!/bin/bash
set -euo pipefail

# --- Configuration ---
APP_DIR="${APP_DIR:-/opt/kidscheck}"
DB_PATH="${APP_DIR}/kidscheck.db"
PHOTOS_PATH="${APP_DIR}/uploads/photos"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup-archive.tar.gz> [--full]"
    echo ""
    echo "Options:"
    echo "  --full    Clear existing photos before restoring (full rollback)"
    echo ""
    echo "Examples:"
    echo "  $0 /var/backups/kidscheck/weekly/2026-05-26_03-00.tar.gz"
    echo "  $0 /var/backups/kidscheck/latest --full"
    exit 1
fi

ARCHIVE="$1"
FULL_RESTORE=false
[ "${2:-}" = "--full" ] && FULL_RESTORE=true

if [ ! -f "$ARCHIVE" ]; then
    echo "ERROR: Archive not found: $ARCHIVE"
    exit 1
fi

TMPDIR=$(mktemp -d)
cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

echo "=== KidsCheck Restore ==="
echo "Archive: $ARCHIVE"
echo "Target:  $APP_DIR"
echo "Mode:    $([ "$FULL_RESTORE" = true ] && echo 'FULL (clears existing photos)' || echo 'MERGE (keeps existing photos)')"
echo ""
read -p "Proceed? (y/N) " -n 1 -r
echo
[[ $REPLY =~ ^[Yy]$ ]] || exit 0

# --- 1. Stop application ---
echo "Stopping kidscheck service..."
systemctl stop kidscheck 2>/dev/null || echo "Warning: could not stop kidscheck service (may not be running)"

# --- 2. Extract ---
echo "Extracting archive..."
tar xzf "$ARCHIVE" -C "$TMPDIR"

# --- 3. Restore database ---
echo "Restoring database..."
cp "$TMPDIR/kidscheck.db" "$DB_PATH"
echo "Database restored."

# --- 4. Restore photos ---
echo "Restoring photos..."
if [ "$FULL_RESTORE" = true ]; then
    rm -rf "$PHOTOS_PATH"
fi
if [ -d "$TMPDIR/uploads/photos" ]; then
    mkdir -p "$PHOTOS_PATH"
    cp -r "$TMPDIR/uploads/photos"/* "$PHOTOS_PATH/" 2>/dev/null || true
    echo "Photos restored."
else
    echo "No photos in backup."
fi

# --- 5. Restart application ---
echo "Starting kidscheck service..."
systemctl start kidscheck 2>/dev/null || echo "Warning: could not start kidscheck service"

echo ""
echo "=== Restore complete ==="
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/restore.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/restore.sh
git commit -m "feat: add restore script with merge and full-rollback modes"
```

---

### Task 4: Create Nginx configuration snippet

**Files:**
- Create: `scripts/nginx-backup.conf`

- [ ] **Step 1: Write Nginx config**

Create `scripts/nginx-backup.conf`:

```nginx
# KidsCheck backup file download
# Add this to your server {} block in nginx.conf
#
# Before use, create the password file:
#   htpasswd -c /etc/nginx/.backup_htpasswd backup-user

location /backups/ {
    auth_basic "KidsCheck Backup";
    auth_basic_user_file /etc/nginx/.backup_htpasswd;
    autoindex on;
    alias /var/backups/kidscheck/;
}
```

- [ ] **Step 2: Commit**

```bash
git add scripts/nginx-backup.conf
git commit -m "feat: add Nginx config for backup download with Basic Auth"
```

---

### Task 5: Create deployment setup script

**Files:**
- Create: `scripts/setup-backup.sh`

- [ ] **Step 1: Write setup script**

Create `scripts/setup-backup.sh`:

```bash
#!/bin/bash
set -euo pipefail

# One-time setup for backup infrastructure on the server.
# Run as root after deploying the KidsCheck application.

APP_DIR="${APP_DIR:-/opt/kidscheck}"
BACKUP_ROOT="${BACKUP_ROOT:-/var/backups/kidscheck}"

echo "=== KidsCheck Backup Setup ==="

# --- 1. Create backup directories ---
echo "Creating backup directories..."
mkdir -p "${BACKUP_ROOT}/weekly" "${BACKUP_ROOT}/monthly"
echo "  ${BACKUP_ROOT}/weekly"
echo "  ${BACKUP_ROOT}/monthly"

# --- 2. Install sqlite3 if missing ---
if ! command -v sqlite3 &> /dev/null; then
    echo "Installing sqlite3..."
    apt-get update -qq && apt-get install -y -qq sqlite3
else
    echo "sqlite3 already installed."
fi

# --- 3. Install cron if missing ---
if ! command -v crontab &> /dev/null; then
    echo "Installing cron..."
    apt-get update -qq && apt-get install -y -qq cron
fi

# --- 4. Add cron job ---
CRON_LINE="0 3 * * 1 ${APP_DIR}/scripts/backup.sh >> /var/log/kidscheck-backup.log 2>&1"
if crontab -l 2>/dev/null | grep -qF "backup.sh"; then
    echo "Cron job already exists."
else
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "Cron job added: every Monday 3:00 AM"
fi

# --- 5. Copy scripts to app directory ---
echo "Copying scripts..."
cp "$(dirname "$0")/backup.sh" "${APP_DIR}/scripts/"
cp "$(dirname "$0")/restore.sh" "${APP_DIR}/scripts/"
chmod +x "${APP_DIR}/scripts/backup.sh" "${APP_DIR}/scripts/restore.sh"

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Add Nginx config: copy scripts/nginx-backup.conf into your server block"
echo "  2. Create backup user: htpasswd -c /etc/nginx/.backup_htpasswd backup-user"
echo "  3. Reload Nginx: nginx -s reload"
echo "  4. Test backup: bash ${APP_DIR}/scripts/backup.sh"
echo "  5. Pull from local: python scripts/pull_backup.py --host <server> --key <key>"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x scripts/setup-backup.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/setup-backup.sh
git commit -m "feat: add one-time server setup script for backup infrastructure"
```

---

### Task 6: Add paramiko dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add paramiko to requirements.txt**

Append to `requirements.txt`:

```
paramiko>=3.0.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt
git commit -m "chore: add paramiko dependency for backup pull script"
```
