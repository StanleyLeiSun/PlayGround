import os
from pathlib import Path

from dotenv import load_dotenv

APP_ENV = os.getenv("APP_ENV", "dev")
env_file = Path(__file__).parent.parent / f".env.{APP_ENV}"
if env_file.exists():
    load_dotenv(env_file, override=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./kidscheck_dev.db")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "kidscheck-secret-key-dev")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

# File upload
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads/photos"))
MAX_PHOTO_SIZE_MB = 1
MAX_PHOTO_BYTES = MAX_PHOTO_SIZE_MB * 1024 * 1024

# LLM (for voice intent parsing)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_URL = os.getenv("LLM_API_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")

# WeChat Mini-Program
WX_APP_ID = os.getenv("WX_APP_ID", "")
WX_APP_SECRET = os.getenv("WX_APP_SECRET", "")

# Scheduler
SCHEDULER_HOUR = 0
SCHEDULER_MINUTE = 0
