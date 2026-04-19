"""
Configuration settings for Bayaan API
"""

import os
from pathlib import Path

from dotenv import load_dotenv

_REPO = Path(__file__).resolve().parent.parent
# Repo-root run `python -m uvicorn ...` loads app/.env reliably (before cwd-dependent `.env`).
load_dotenv(_REPO / "app" / ".env")
load_dotenv(_REPO / ".env")
load_dotenv()

# -------------------------
# Database Configuration
# -------------------------

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "database": os.getenv("DB_NAME", "bayaan"),
}

_db_port = os.getenv("DB_PORT", "").strip()
if _db_port:
    DATABASE_CONFIG["port"] = int(_db_port)

# -------------------------
# API Configuration
# -------------------------

API_TITLE = "Bayaan API"
API_DESCRIPTION = "API for Quran word retrieval and translation segment alignment"
API_VERSION = "1.0.0"

# -------------------------
# Server Configuration
# -------------------------

# These can be overridden via command line when running uvicorn
# e.g., uvicorn app.app:app --host 0.0.0.0 --port 8001 --reload
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
