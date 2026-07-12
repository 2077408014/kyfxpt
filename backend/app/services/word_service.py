from sqlalchemy.orm import Session
from datetime import date, timedelta
from ..models.word import Word, UserWord
from ..models.user import User
from ..schemas.word import WordStudyRequest, StudyPlanRequest
from ..utils.memory_curve import calculate_word_next_review
import random


class WordService:
    def get_word_stats(self, db: Session, user_id: int) -> dict:
        total = db.query(Word).count()
        studied = db.query(UserWord).filter(UserWord.user_id == user_id).count()
        mastered = db.query(UserWord).filter(
            UserWord.user_id == user_id,
            UserWord.mastery_level == "掌握"
        ).count()
        today = date.today().isoformat()
        today_studied = db.query(UserWord).filter(
            UserWord.user_id == user_id,
            UserWord.last_study_date >= today
        ).count()
        return {
            "total": total,
            "studied": studied,
            "mastered": mastered,
            "today": today_studied
        }

    def get_today_words(self, db: Session, user_id: int, count: int = 20) -> list:
        studied_word_ids = [
            uw.word_id for uw in
            db.query(UserWord).filter(UserWord.user_id == user_id).all()
        ]
        new_words = db.query(Word).filter(
            ~Word.id.in_(studied_word_ids) if studied_word_ids else True
        ).order_by(Word.frequency.desc()).limit(count).all()

        if len(new_words) < count:
            review_words = db.query(Word).join(UserWord).filter(
                UserWord.user_id == user_id,
                UserWord.next_review_date <= date.today()
            ).limit(count - len(new_words)).all()
            new_words.extend(review_words)

        return new_words

    def get_review_words(self, db: Session, user_id: int) -> list:
        return db.query(UserWord).filter(
            UserWord.user_id == user_id
        ).order_by(UserWord.next_review_date).all()

    def get_word_list(self, db: Session, user_id: int, page: int = 1, page_size: int = 20,
                      mastery_level: str = None, keyword: str = None) -> dict:
        query = db.query(UserWord).filter(UserWord.user_id == user_id)
        if mastery_level:
            query = query.filter(UserWord.mastery_level == mastery_level)
        if keyword:
            query = query.join(Word).filter(Word.word.like(f"%{keyword}%"))

        total = query.count()
        items = query.order_by(UserWord.last_study_date.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return {"total": total, "items": items}

    def study_word(self, db: Session, user_id: int, data: WordStudyRequest) -> UserWord:
        user_word = db.query(UserWord).filter(
            UserWord.user_id == user_id,
            UserWord.word_id == data.word_id
        ).first()

        if not user_word:
            user_word = UserWord(
                user_id=user_id,
                word_id=data.word_id,
                mastery_level="陌生",
                review_count=0,
                correct_count=0
            )
            db.add(user_word)

        user_word.review_count += 1
        if data.result == "认识":
            user_word.correct_count += 1
            if user_word.mastery_level == "陌生":
                user_word.mastery_level = "认识"
            elif user_word.mastery_level == "认识":
                user_word.mastery_level = "熟悉"
            elif user_word.mastery_level == "熟悉":
                user_word.mastery_level = "掌握"
        elif data.result == "模糊":
            if user_word.mastery_level == "掌握":
                user_word.mastery_level = "熟悉"
            elif user_word.mastery_level == "熟悉":
                user_word.mastery_level = "认识"
        elif data.result == "错误":
            user_word.mastery_level = "陌生"

        next_date, new_level = calculate_word_next_review(
            user_word.mastery_level, user_word.review_count, user_word.correct_count
        )
        user_word.next_review_date = next_date
        user_word.last_study_date = date.today()

        db.commit()
        db.refresh(user_word)
        return user_word

    def get_study_plan(self, db: Session, user_id: int) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        return {
            "daily_word_count": getattr(user, 'daily_word_count', 20)
        }

    def save_study_plan(self, db: Session, user_id: int, data: StudyPlanRequest) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.daily_word_count = data.daily_word_count
            db.commit()
        return {"daily_word_count": data.daily_word_count}


word_service = WordService()
