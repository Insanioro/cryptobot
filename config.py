import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "")
CHANNEL_URL: str = os.getenv("CHANNEL_URL", "")

# Admin IDs for statistics access (comma-separated)
ADMIN_IDS_STR: str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip().isdigit()]

# Notification settings
DEFAULT_NOTIFY_NEW_USERS: bool = os.getenv("DEFAULT_NOTIFY_NEW_USERS", "true").lower() == "true"
DEFAULT_NOTIFY_ORDERS: bool = os.getenv("DEFAULT_NOTIFY_ORDERS", "true").lower() == "true"
DEFAULT_NOTIFY_ABANDONED: bool = os.getenv("DEFAULT_NOTIFY_ABANDONED", "true").lower() == "true"
DEFAULT_ABANDONED_THRESHOLD: int = int(os.getenv("DEFAULT_ABANDONED_THRESHOLD", "10"))

# Statistics settings
STATS_CACHE_TTL: int = int(os.getenv("STATS_CACHE_TTL", "300"))  # 5 minutes
STATS_EXPORT_DIR: str = os.getenv("STATS_EXPORT_DIR", "./exports")

PG_USER: str = os.getenv("PG_USER", "postgres")
PG_PASS: str = os.getenv("PG_PASS", "")
PG_HOST: str = os.getenv("PG_HOST", "localhost")
PG_PORT: int = int(os.getenv("PG_PORT", "5432"))
PG_NAME: str = os.getenv("PG_NAME", "valubot")

# DSN without password if not set
if PG_PASS:
    PG_DSN: str = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_NAME}"
else:
    PG_DSN: str = f"postgresql://{PG_USER}@{PG_HOST}:{PG_PORT}/{PG_NAME}"
