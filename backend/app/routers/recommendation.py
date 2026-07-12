from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.recommendation_service import recommendation_service
from ..schemas.recommendation import RecommendationCreate, RecommendationComplete, RecommendationReport
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/recommend", tags=["推荐系统"])


@router.get("/analysis", response_model=list)
def analyze_weak_points(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = recommendation_service.analyze_weak_points(db, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate", response_model=list)
def generate_recommendations(
    count: int = Query(5, ge=1, le=20),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = recommendation_service.generate_recommendations(db, current_user.id, count)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=list)
def get_recommendations(
    completed: bool = Query(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = recommendation_service.get_recommendations(db, current_user.id, completed)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{id}/complete")
def complete_recommendation(
    id: int,
    data: RecommendationComplete,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = recommendation_service.complete_recommendation(db, current_user.id, id, data.result)
        if not result:
            raise HTTPException(status_code=404, detail="推荐题目不存在")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report", response_model=RecommendationReport)
def get_recommendation_report(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        result = recommendation_service.get_recommendation_report(db, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))