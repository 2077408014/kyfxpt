from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./kaoyan_xt.db"
    SECRET_KEY: str = "kaoyan_xt_secret_key_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = "./uploads"
    INDEX_DIR: str = "./indexes"
    SERVER_PORT: int = 8080
    AI_API_KEY: str = ""
    AI_BASE_URL: str = "http://localhost:8081/v1"
    AI_MODEL: str = "local-llm-model"
    AI_MAX_TOKENS: int = 4096
    AI_TIMEOUT: int = 120
    USE_LOCAL_LLM: bool = False
    LLM_MODEL_NAME: str = "Qwen/Qwen2-7B-Instruct"
    LLM_DEVICE: str = "auto"
    LLM_MAX_CONTEXT: int = 4096
    LLM_TEMPERATURE: float = 0.7
    LLM_PORT: int = 8081

    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    class Config:
        env_file = ".env"

def get_settings():
    env_file = ".env"
    if os.getenv("ENVIRONMENT") == "test":
        env_file = ".env.test"
    elif os.getenv("ENVIRONMENT") == "llm":
        env_file = ".env.llm"
    
    return Settings(_env_file=env_file)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

UPLOAD_PATH = BASE_DIR / "backend" / "uploads"
INDEX_PATH = BASE_DIR / "backend" / "indexes"

DATABASE_PATH = BASE_DIR / "kaoyan_xt.db"

UPLOAD_PATH.mkdir(parents=True, exist_ok=True)
INDEX_PATH.mkdir(parents=True, exist_ok=True)

settings = get_settings()
settings.DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
