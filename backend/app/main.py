from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routers import auth, mistakes
from .config import UPLOAD_PATH

Base.metadata.create_all(bind=engine)

app = FastAPI(title="考研复习平台", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_PATH), name="uploads")

app.include_router(auth.router)
app.include_router(mistakes.router)

@app.get("/")
async def root():
    return {"message": "考研复习平台 API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}