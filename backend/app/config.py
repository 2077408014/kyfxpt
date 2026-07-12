from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./kaoyan_xt.db"
    SECRET_KEY: str = "kaoyan_xt_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "./uploads"
    INDEX_DIR: str = "./indexes"
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "https://api.deepseek.com/v1"
    AI_MODEL: str = "deepseek-chat"
    AI_MAX_TOKENS: int = 2048
    AI_TIMEOUT: int = 60

    class Config:
        env_file = ".env"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_PATH = BASE_DIR / "backend" / "uploads"
INDEX_PATH = BASE_DIR / "backend" / "indexes"

DATABASE_PATH = BASE_DIR / "kaoyan_xt.db"

UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
INDEX_PATH.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.DATABASE_URL = f"sqlite:///{DATABASE_PATH}"