"""
Configuration settings for AI Blog Nest.
All secrets are loaded from environment variables (.env file).
Never hard-code API keys or secrets here.
"""

import os
from dotenv import load_dotenv

# Load variables from a .env file if one exists
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Flask secret key, used to sign session cookies.
    # Falls back to a development-only key if not set (change this in production).
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # Path to the SQLite database file
    DATABASE_PATH = os.path.join(BASE_DIR, "instance", "blog_nest.db")

    # AI configuration (OpenAI-compatible API)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
    OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1").strip()
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    # Whether real AI generation is available (no key = demo/offline mode)
    AI_ENABLED = bool(OPENAI_API_KEY)

    # Pagination
    BLOGS_PER_PAGE = 6

    # Default admin bootstrap credentials (only used by create_admin.py)
    DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@blognest.com")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    DEFAULT_ADMIN_NAME = os.environ.get("ADMIN_NAME", "Site Administrator")
