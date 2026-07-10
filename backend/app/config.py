from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./kaoyan_xt.db"
    SECRET_KEY: str = "kaoyan_xt_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    UPLOAD_DIR: str = "./uploads"
    INDEX_DIR: str = "./indexes"

    class Config:
        env_file = ".env"

settings = Settings()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_PATH = BASE_DIR / settings.UPLOAD_DIR
INDEX_PATH = BASE_DIR / settings.INDEX_DIR

UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
INDEX_PATH.mkdir(parents=True, exist_ok=True)