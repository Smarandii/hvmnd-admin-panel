from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")          # already silently continues if file missing


class Config:
    SECRET_KEY      = os.getenv("FLASK_SECRET_KEY", "dev-only-secret")
    DEBUG           = os.getenv("IS_DEBUG", "False").lower() == "true"
    DB_DSN          = os.getenv("POSTGRES_URL")
    TEMPLATE_FOLDER = BASE_DIR / "templates"
    STATIC_FOLDER   = BASE_DIR / "static"
