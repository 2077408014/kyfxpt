from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base, migrate_database
from .models import User, Mistake, Word, Resource, Recommendation, AIChatHistory, UserStudyStat, PoliticsRecitation, KnowledgeDocument
from .routers import auth, mistakes, words, politics, recommendation, resources, ai, report, rag, supervision, study_tracker, ai_config, feature_agent
from .config import UPLOAD_PATH

Base.metadata.create_all(bind=engine)
migrate_database()

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
app.include_router(words.router)
app.include_router(politics.router)
app.include_router(recommendation.router)
app.include_router(resources.router)
app.include_router(ai.router)
app.include_router(rag.router)
app.include_router(report.router)
app.include_router(supervision.router)
app.include_router(study_tracker.router)
app.include_router(ai_config.router)
app.include_router(feature_agent.router)

@app.get("/")
async def root():
    return {"message": "考研复习平台 API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}