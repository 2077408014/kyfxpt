from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ai_service import ai_service
from ..routers.auth import get_current_user
from ..schemas.ai import AIChatRequest, AICommandRequest

router = APIRouter(prefix="/api/ai", tags=["AI问答"])


@router.post("/chat")
def chat(
    data: AIChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ai_service.chat(db, current_user.id, data.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/command")
def command(
    data: AICommandRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ai_service.command(db, current_user.id, data.command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_history(
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ai_service.get_history(db, current_user.id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
def clear_history(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ai_service.clear_history(db, current_user.id)
        return {"message": "聊天记录已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))