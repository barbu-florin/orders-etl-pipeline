import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


SQL_DIR = Path.cwd() / "sql"

ORDERS_URL = os.getenv("ORDERS_URL")

FX_URL = os.getenv("FX_URL")

API_KEY = os.getenv("API_KEY")

TARGET_DB_URL = os.getenv("TARGET_DB_URL")

ORDERS_HEADER = {
    "Content-Type": "application/json",
    "apikey": API_KEY or "",
}

FX_HEADER = {
    "Content-Type": "application/json",
}
