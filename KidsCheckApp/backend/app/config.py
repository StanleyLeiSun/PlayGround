import os
from pathlib import Path

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/kidscheck")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "kidscheck-secret-key-change-in-production")
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

# Scheduler
SCHEDULER_HOUR = 0
SCHEDULER_MINUTE = 0
