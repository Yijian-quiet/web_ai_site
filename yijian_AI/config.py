# config.py
import os
from pathlib import Path

DB_PATH = Path("chat_app_history.db")
DEFAULT_MODEL = "gemma3:4b"
PERSONA_FILE = Path("persona/zhangyijian_persona.txt")

# MySQL 配置（支持环境变量覆盖）
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": "webai",
    "password": os.getenv("MYSQL_PASSWORD", "test123"),
    "database": "web_ai",
    "charset": "utf8mb4",
}

# 登录限流配置
LOGIN_MAX_ATTEMPTS = 3
LOGIN_LOCK_MINUTES = 15
