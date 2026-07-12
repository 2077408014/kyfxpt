from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..schemas.word import WordResponse, WordStudyRequest, StudyPlanRequest
from ..services.word_service import word_service
from ..routers.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/words", tags=["words"])


@router.get("/stats")
async def get_word_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return word_service.get_word_stats(db, current_user.id)


@router.get("/today", response_model=list[WordResponse])
async def get_today_words(
    count: int = Query(20, ge=5, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return word_service.get_today_words(db, current_user.id, count)


@router.get("/review")
async def get_review_words(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    items = word_service.get_review_words(db, current_user.id)
    return [
        {
            "id": item.id,
            "word_id": item.word_id,
            "word": item.word.word if hasattr(item, 'word') else "",
            "mastery_level": item.mastery_level,
            "next_review_date": item.next_review_date.isoformat() if item.next_review_date else None,
            "review_count": item.review_count,
            "correct_count": item.correct_count
        }
        for item in items
    ]


@router.get("/list")
async def get_word_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=10, le=100),
    mastery_level: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = word_service.get_word_list(db, current_user.id, page, page_size, mastery_level, keyword)
    items = [
        {
            "id": item.id,
            "word_id": item.word_id,
            "word": item.word.word if hasattr(item, 'word') else "",
            "phonetic": item.word.phonetic if hasattr(item, 'word') else "",
            "meaning": item.word.meaning if hasattr(item, 'word') else "",
            "example_sentence": item.word.example_sentence if hasattr(item, 'word') else "",
            "mastery_level": item.mastery_level,
            "next_review_date": item.next_review_date.isoformat() if item.next_review_date else None,
            "review_count": item.review_count,
            "correct_count": item.correct_count,
            "last_study_date": item.last_study_date.isoformat() if item.last_study_date else None
        }
        for item in result["items"]
    ]
    return {"total": result["total"], "items": items}


@router.post("/study")
async def study_word(
    data: WordStudyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = word_service.study_word(db, current_user.id, data)
    return {
        "id": result.id,
        "mastery_level": result.mastery_level,
        "next_review_date": result.next_review_date.isoformat() if result.next_review_date else None,
        "review_count": result.review_count,
        "correct_count": result.correct_count
    }


@router.get("/plan")
async def get_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return word_service.get_study_plan(db, current_user.id)


@router.post("/plan")
async def save_study_plan(
    data: StudyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return word_service.save_study_plan(db, current_user.id, data)
