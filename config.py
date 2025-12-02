import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))

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
