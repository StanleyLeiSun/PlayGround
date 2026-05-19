# Multi-Environment Support Design

> Date: 2026-05-19
> Status: Approved

## Overview

Add environment-based configuration to both backend and Android client, supporting dev (local testing), prod (production server), and a hybrid mode (local client connecting to production server). Each environment has its own database, secrets, and base URL configuration.

## Environments

| Environment | Backend | Client | Use Case |
|-------------|---------|--------|----------|
| dev | `.env.dev`, SQLite local | flavor `dev` + debug | Local development and testing |
| localProd | N/A | flavor `localProd` + debug | Emulator debugging against production API |
| prod | `.env.prod`, SQLite on server | flavor `prod` + release | Production deployment |
| test | `test_kidscheck.db` (auto) | N/A | pytest, created/destroyed per test |

## Backend Design

### Configuration Files

```
backend/
├── .env.dev            # Dev config (committed)
├── .env.prod           # Prod config (git-ignored, created manually on server)
├── .env.prod.example   # Prod template (committed)
└── app/config.py       # Loads env from APP_ENV-selected file
```

### `.env.dev`

```
APP_ENV=dev
DATABASE_URL=sqlite+aiosqlite:///./kidscheck_dev.db
JWT_SECRET=kidscheck-secret-key-dev
UPLOAD_DIR=uploads/photos
LLM_API_KEY=
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_MODEL=qwen-plus
```

### `.env.prod.example`

```
APP_ENV=prod
DATABASE_URL=sqlite+aiosqlite:///./kidscheck_prod.db
JWT_SECRET=<替换为强密钥>
UPLOAD_DIR=uploads/photos
LLM_API_KEY=<替换为API密钥>
LLM_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
LLM_MODEL=qwen-plus
```

### `config.py` Changes

```python
import os
from pathlib import Path
from dotenv import load_dotenv

APP_ENV = os.getenv("APP_ENV", "dev")
env_file = Path(__file__).parent.parent / f".env.{APP_ENV}"
if env_file.exists():
    load_dotenv(env_file)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./kidscheck_dev.db")
JWT_SECRET = os.getenv("JWT_SECRET", "kidscheck-secret-key-dev")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads/photos"))
MAX_PHOTO_SIZE_MB = 1
MAX_PHOTO_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")

SCHEDULER_HOUR = 0
SCHEDULER_MINUTE = 0
```

### Scripts

**`dev.sh` (modified):**
```bash
#!/usr/bin/env bash
set -euo pipefail
export APP_ENV=dev
set -a; source "$(dirname "$0")/../.env.dev"; set +a

PORT="${1:-8000}"
cd "$(dirname "$0")/.."
# ... existing venv/pip/alembic/uvicorn logic with --reload
```

**`prod.sh` (new):**
```bash
#!/usr/bin/env bash
set -euo pipefail
export APP_ENV=prod
set -a; source "$(dirname "$0")/../.env.prod"; set +a

PORT="${1:-8000}"
cd "$(dirname "$0")/.."
# venv, pip install, alembic upgrade head
# uvicorn WITHOUT --reload, with --workers 2
```

Windows `.ps1` / `.cmd` variants follow the same pattern.

### Dependency Addition

Add `python-dotenv` to `requirements.txt`.

## Android Client Design

### Build Flavors

```kotlin
// app/build.gradle.kts
android {
    buildFeatures {
        buildConfig = true
    }

    flavorDimensions += "environment"
    productFlavors {
        create("dev") {
            dimension = "environment"
            buildConfigField("String", "BASE_URL", "\"http://10.0.2.2:8000\"")
        }
        create("localProd") {
            dimension = "environment"
            // URL read from config.properties
            buildConfigField("String", "BASE_URL", "\"${prodBaseUrl}\"")
        }
        create("prod") {
            dimension = "environment"
            buildConfigField("String", "BASE_URL", "\"${prodBaseUrl}\"")
        }
    }
}
```

### Configuration File

```
android/config.properties    # committed
```

```properties
prod.base_url=https://api.kidscheck.example.com
```

`build.gradle.kts` reads this file:
```kotlin
val configProps = java.util.Properties().apply {
    load(rootProject.file("config.properties").inputStream())
}
val prodBaseUrl = configProps.getProperty("prod.base_url", "https://api.kidscheck.example.com")
```

### RetrofitInstance.kt Change

```kotlin
object RetrofitInstance {
    private const val BASE_URL = BuildConfig.BASE_URL
    // ... rest unchanged
}
```

### Build Variants

| Variant | Command | Connects to |
|---------|---------|-------------|
| devDebug | `./gradlew assembleDevDebug` | Local backend (10.0.2.2:8000) |
| localProdDebug | `./gradlew assembleLocalProdDebug` | Production server |
| prodRelease | `./gradlew assembleProdRelease` | Production server |

## Database & Seed Data

### Seed Logic in Migration

```python
# alembic/versions/001_create_tables_and_seed.py
import os

def upgrade():
    # ... table creation unchanged ...

    env = os.getenv("APP_ENV", "dev")
    password = "123456" if env == "dev" else "KidsCheck2026!"

    op.execute(f"""
        INSERT INTO "user" (username, password_hash, role) VALUES
        ('爸爸', '{password}', 'parent'),
        ('妈妈', '{password}', 'parent'),
        ('爷爷', '{password}', 'grandparent'),
        ('奶奶', '{password}', 'grandparent'),
        ('姥姥', '{password}', 'grandparent'),
        ('姥爷', '{password}', 'grandparent')
    """)

    op.execute("""
        INSERT INTO child (name, nickname, age) VALUES
        ('孙北峤', '萝卜', 8),
        ('孙南崧', '蚕豆', 5)
    """)

    op.execute("""
        INSERT INTO point_account (child_id, balance) VALUES
        (1, 0), (2, 0)
    """)
```

### Database Files

| Environment | Database File | Management |
|-------------|--------------|-----------|
| dev | `kidscheck_dev.db` | Auto-created by migration |
| prod | `kidscheck_prod.db` | Created on server via `prod.sh` running migration |
| test | `kidscheck_test.db` | Created/destroyed per pytest run (unchanged) |

## .gitignore Updates

Add to existing `.gitignore`:
```
backend/.env.prod
```

## Files Changed Summary

| File | Action |
|------|--------|
| `backend/.env.dev` | New |
| `backend/.env.prod.example` | New |
| `backend/app/config.py` | Modified (add dotenv loading) |
| `backend/requirements.txt` | Modified (add python-dotenv) |
| `backend/scripts/dev.sh` | Modified (set APP_ENV, source .env.dev) |
| `backend/scripts/dev.ps1` | Modified (same) |
| `backend/scripts/prod.sh` | New |
| `backend/scripts/prod.ps1` | New |
| `backend/alembic/versions/001_create_tables_and_seed.py` | Modified (env-based password, child names) |
| `android/config.properties` | New |
| `android/app/build.gradle.kts` | Modified (flavors, buildConfig) |
| `android/app/src/main/java/.../RetrofitInstance.kt` | Modified (use BuildConfig.BASE_URL) |
| `.gitignore` | Modified (add .env.prod) |
