import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

from dotenv import load_dotenv

load_dotenv()
class Config:
    """Base configuration shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "CITS5505")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'trackmint.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    RECEIPT_UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "uploads" / "receipts")
    PROFILE_UPLOAD_FOLDER = str(BASE_DIR / "app" / "static" / "uploads" / "profiles")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB upload limit

    # Session / cookie security
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # CSRF protection
    WTF_CSRF_TIME_LIMIT = None

    # Flask general settings
    TEMPLATES_AUTO_RELOAD = True
    
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com").strip()
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").strip().lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "").strip()
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "").strip()
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME).strip()

class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}