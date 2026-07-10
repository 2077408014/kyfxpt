from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..schemas.mistake import MistakeCreate, MistakeUpdate, MistakeResponse, MistakeReviewCreate, MistakeReviewResponse
from ..services.mistake_service import mistake_service
from ..routers.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/mistakes", tags=["mistakes"])

@router.post("", response_model=MistakeResponse)
async def create_mistake(
    data: MistakeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistake = mistake_service.create_mistake(db, current_user.id, data)
    return mistake

@router.get("", response_model=list[MistakeResponse])
async def get_mistakes(
    subject: Optional[str] = Query(None),
    knowledge_point: Optional[str] = Query(None),
    error_type: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    mastery_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filters = {k: v for k, v in locals().items() if v is not None and k != "db" and k != "current_user"}
    mistakes = mistake_service.get_mistakes(db, current_user.id, filters)
    return mistakes

@router.get("/{mistake_id}", response_model=MistakeResponse)
async def get_mistake(
    mistake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistake = mistake_service.get_mistake_by_id(db, current_user.id, mistake_id)
    if not mistake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return mistake

@router.put("/{mistake_id}", response_model=MistakeResponse)
async def update_mistake(
    mistake_id: int,
    data: MistakeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistake = mistake_service.update_mistake(db, current_user.id, mistake_id, data)
    if not mistake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return mistake

@router.delete("/{mistake_id}")
async def delete_mistake(
    mistake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = mistake_service.delete_mistake(db, current_user.id, mistake_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return {"message": "删除成功"}

@router.post("/{mistake_id}/review", response_model=MistakeReviewResponse)
async def review_mistake(
    mistake_id: int,
    data: MistakeReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        review = mistake_service.review_mistake(db, current_user.id, mistake_id, data)
        return review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/review/today", response_model=list[MistakeResponse])
async def get_today_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistakes = mistake_service.get_today_reviews(db, current_user.id)
    return mistakes