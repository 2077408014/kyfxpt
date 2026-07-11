from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def migrate_database():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(mistakes)"))
        columns = [row[1] for row in result]
        if "image_path" not in columns:
            conn.execute(text("ALTER TABLE mistakes ADD COLUMN image_path VARCHAR(500)"))
            conn.commit()