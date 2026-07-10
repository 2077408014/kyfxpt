from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import date
from ..models.mistake import Mistake, MistakeReview
from ..schemas.mistake import MistakeCreate, MistakeUpdate, MistakeReviewCreate
from ..utils.memory_curve import calculate_next_review_date

class MistakeService:
    def create_mistake(self, db: Session, user_id: int, data: MistakeCreate) -> Mistake:
        next_review_date, _ = calculate_next_review_date(
            current_level="生疏",
            difficulty=data.difficulty,
            review_count=0,
            correct_count=0
        )
        
        mistake = Mistake(
            user_id=user_id,
            subject=data.subject,
            knowledge_point=data.knowledge_point,
            error_type=data.error_type,
            difficulty=data.difficulty,
            mastery_level="生疏",
            question_text=data.question_text,
            answer=data.answer,
            analysis=data.analysis,
            error_reason=data.error_reason,
            next_review_date=next_review_date
        )
        db.add(mistake)
        db.commit()
        db.refresh(mistake)
        return mistake

    def get_mistakes(self, db: Session, user_id: int, filters: Optional[dict] = None) -> list:
        query = db.query(Mistake).filter(Mistake.user_id == user_id)
        
        if filters:
            if filters.get("subject"):
                query = query.filter(Mistake.subject == filters["subject"])
            if filters.get("knowledge_point"):
                query = query.filter(Mistake.knowledge_point == filters["knowledge_point"])
            if filters.get("error_type"):
                query = query.filter(Mistake.error_type == filters["error_type"])
            if filters.get("difficulty"):
                query = query.filter(Mistake.difficulty == filters["difficulty"])
            if filters.get("mastery_level"):
                query = query.filter(Mistake.mastery_level == filters["mastery_level"])
        
        return query.order_by(Mistake.created_at.desc()).all()

    def get_mistake_by_id(self, db: Session, user_id: int, mistake_id: int) -> Optional[Mistake]:
        return db.query(Mistake).filter(
            and_(Mistake.id == mistake_id, Mistake.user_id == user_id)
        ).first()

    def update_mistake(self, db: Session, user_id: int, mistake_id: int, data: MistakeUpdate) -> Optional[Mistake]:
        mistake = self.get_mistake_by_id(db, user_id, mistake_id)
        if not mistake:
            return None
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(mistake, key, value)
        
        db.commit()
        db.refresh(mistake)
        return mistake

    def delete_mistake(self, db: Session, user_id: int, mistake_id: int) -> bool:
        mistake = self.get_mistake_by_id(db, user_id, mistake_id)
        if not mistake:
            return False
        
        db.delete(mistake)
        db.commit()
        return True

    def review_mistake(self, db: Session, user_id: int, mistake_id: int, data: MistakeReviewCreate) -> MistakeReview:
        mistake = self.get_mistake_by_id(db, user_id, mistake_id)
        if not mistake:
            raise ValueError("错题不存在")
        
        review = MistakeReview(
            mistake_id=mistake_id,
            user_id=user_id,
            result=data.result,
            notes=data.notes
        )
        db.add(review)
        
        mistake.review_count += 1
        if data.result == "正确":
            mistake.correct_count += 1
        
        next_date, new_level = calculate_next_review_date(
            current_level=mistake.mastery_level,
            difficulty=mistake.difficulty,
            review_count=mistake.review_count,
            correct_count=mistake.correct_count
        )
        
        mistake.next_review_date = next_date
        mistake.mastery_level = new_level
        
        db.commit()
        db.refresh(review)
        return review

    def get_today_reviews(self, db: Session, user_id: int) -> list:
        today = date.today()
        return db.query(Mistake).filter(
            and_(
                Mistake.user_id == user_id,
                Mistake.next_review_date <= today
            )
        ).all()

mistake_service = MistakeService()