from sqlalchemy.orm import Session
from datetime import date, timedelta
from sqlalchemy import or_
from ..models.word import Word, UserWord
from ..models.user import User
from ..schemas.word import WordStudyRequest, StudyPlanRequest
from ..utils.memory_curve import calculate_word_next_review
from ..utils.ocr_parse import ocr_parser
from ..utils.wordbook_parser import parse_wordbook_text


class WordService:
    def _has_wordbook(self, db: Session, user_id: int) -> bool:
        return db.query(Word.id).filter(Word.user_id == user_id).first() is not None

    def _get_source_filter(self, user_id: int, category: str = None):
        """构建单词来源过滤条件。

        category 为空或"全部" → 系统词 + 词书词都包含
        category == "我的词书" → 仅词书词
        其他分类（CET-4 等）→ 仅系统词
        """
        if not category or category == "全部":
            return or_(Word.user_id.is_(None), Word.user_id == user_id)
        elif category == "我的词书":
            return Word.user_id == user_id
        else:
            return Word.user_id.is_(None)

    def _apply_category_filter(self, query, user_id: int, category: str = None):
        """在 query（已包含 Word）上附加分类过滤。"""
        source_filter = self._get_source_filter(user_id, category)
        query = query.filter(source_filter)
        if category and category not in ("全部", "我的词书"):
            query = query.filter(Word.category == category)
        return query

    def get_word_stats(self, db: Session, user_id: int, category: str = None) -> dict:
        has_wordbook = self._has_wordbook(db, user_id)

        total_query = db.query(Word)
        total_query = self._apply_category_filter(total_query, user_id, category)
        total = total_query.count()

        studied_query = db.query(UserWord).join(Word)
        studied_query = self._apply_category_filter(studied_query, user_id, category)
        studied = studied_query.filter(UserWord.user_id == user_id).count()

        mastered_query = db.query(UserWord).join(Word)
        mastered_query = self._apply_category_filter(mastered_query, user_id, category)
        mastered = mastered_query.filter(
            UserWord.user_id == user_id,
            UserWord.mastery_level == "掌握"
        ).count()

        today = date.today()
        today_query = db.query(UserWord).join(Word)
        today_query = self._apply_category_filter(today_query, user_id, category)
        today_studied = today_query.filter(
            UserWord.user_id == user_id,
            UserWord.last_study_date >= today
        ).count()

        return {
            "total": total,
            "studied": studied,
            "mastered": mastered,
            "today": today_studied,
            "has_wordbook": has_wordbook
        }

    def get_daily_review_words(self, db: Session, user_id: int, category: str = None) -> list:
        query = db.query(Word).join(UserWord).filter(
            UserWord.user_id == user_id,
            UserWord.next_review_date <= date.today()
        )
        query = self._apply_category_filter(query, user_id, category)
        return query.order_by(UserWord.next_review_date).all()

    def get_new_words(self, db: Session, user_id: int, count: int = 20, category: str = None) -> list:
        studied_word_ids = [
            uw.word_id for uw in
            db.query(UserWord).filter(UserWord.user_id == user_id).all()
        ]

        query = db.query(Word)
        query = self._apply_category_filter(query, user_id, category)

        if studied_word_ids:
            query = query.filter(~Word.id.in_(studied_word_ids))

        words = query.order_by(Word.frequency.desc()).limit(count).all()

        if len(words) < count and category and category not in ("全部", "我的词书"):
            additional_query = db.query(Word)
            additional_query = self._apply_category_filter(additional_query, user_id, "全部")
            additional_query = additional_query.filter(Word.category != category)
            if studied_word_ids:
                additional_query = additional_query.filter(~Word.id.in_(studied_word_ids))
            additional_words = additional_query.order_by(Word.frequency.desc()).limit(count - len(words)).all()
            words.extend(additional_words)

        return words

    def get_today_words(self, db: Session, user_id: int, count: int = 20, category: str = None) -> dict:
        review_words = self.get_daily_review_words(db, user_id, category)
        remaining_count = max(count - len(review_words), 0)
        new_words = self.get_new_words(db, user_id, remaining_count, category)

        return {
            "review": review_words,
            "new": new_words,
            "review_count": len(review_words),
            "new_count": len(new_words),
            "total_today": len(review_words) + len(new_words)
        }

    def get_word_categories(self, db: Session, user_id: int) -> list:
        system_cats = db.query(Word.category).filter(Word.user_id.is_(None)).distinct().all()
        categories = ["全部"]
        categories.extend([cat[0] for cat in system_cats if cat[0] and cat[0] != "我的词书"])

        if self._has_wordbook(db, user_id):
            categories.append("我的词书")

        return categories

    def get_review_words(self, db: Session, user_id: int) -> list:
        return db.query(UserWord).join(Word).filter(
            UserWord.user_id == user_id
        ).order_by(UserWord.next_review_date).all()

    def get_word_list(self, db: Session, user_id: int, page: int = 1, page_size: int = 20,
                      mastery_level: str = None, keyword: str = None, category: str = None) -> dict:
        query = db.query(Word)
        query = self._apply_category_filter(query, user_id, category)
        if keyword:
            query = query.filter(Word.word.like(f"%{keyword}%"))

        all_words = query.order_by(Word.frequency.desc()).all()

        user_words_map = {}
        user_words = db.query(UserWord).filter(UserWord.user_id == user_id).all()
        for uw in user_words:
            user_words_map[uw.word_id] = uw

        filtered_items = []
        for word in all_words:
            user_word = user_words_map.get(word.id)
            item_mastery_level = user_word.mastery_level if user_word else "未学习"

            if mastery_level and item_mastery_level != mastery_level:
                continue

            filtered_items.append({
                "id": user_word.id if user_word else None,
                "word_id": word.id,
                "word": word.word,
                "phonetic": word.phonetic,
                "meaning": word.meaning,
                "example_sentence": word.example_sentence,
                "mastery_level": item_mastery_level,
                "next_review_date": user_word.next_review_date if user_word else None,
                "review_count": user_word.review_count if user_word else 0,
                "correct_count": user_word.correct_count if user_word else 0,
                "last_study_date": user_word.last_study_date if user_word else None
            })

        total = len(filtered_items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = filtered_items[start:end]

        return {"total": total, "items": paginated_items}

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
            "daily_word_count": getattr(user, 'daily_word_count', 20),
            "word_category": getattr(user, 'selected_word_category', None)
        }

    def save_study_plan(self, db: Session, user_id: int, data: StudyPlanRequest) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.daily_word_count = data.daily_word_count
            if data.word_category is not None:
                user.selected_word_category = data.word_category
            db.commit()
        return {
            "daily_word_count": data.daily_word_count,
            "word_category": data.word_category
        }

    def upload_wordbook(self, db: Session, user_id: int, file_content: bytes, filename: str,
                        category: str = "我的词书") -> dict:
        import os
        import tempfile

        file_ext = os.path.splitext(filename)[1].lower()
        supported = ['.pdf', '.txt', '.doc', '.docx', '.png', '.jpg', '.jpeg']
        if file_ext not in supported:
            return {"success": False, "message": f"不支持的文件类型: {file_ext}"}

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            text = ocr_parser.parse_file(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        if not text or len(text.strip()) < 10:
            return {"success": False, "message": "未能从文件中解析出文本内容"}

        words = parse_wordbook_text(text)
        if not words:
            return {"success": False, "message": "未识别到有效单词，请检查词书格式（每行：单词 [音标] 释义）"}

        old_words = db.query(Word).filter(
            Word.user_id == user_id,
            Word.category == category
        ).all()
        old_word_ids = [w.id for w in old_words]
        if old_word_ids:
            db.query(UserWord).filter(
                UserWord.user_id == user_id,
                UserWord.word_id.in_(old_word_ids)
            ).delete(synchronize_session=False)
            db.query(Word).filter(Word.id.in_(old_word_ids)).delete(synchronize_session=False)
            db.commit()

        imported = 0
        for idx, w in enumerate(words):
            new_word = Word(
                word=w['word'],
                phonetic=w['phonetic'] or None,
                meaning=w['meaning'],
                example_sentence=w['example_sentence'] or None,
                difficulty=1,
                frequency=len(words) - idx,
                exam_requirement="词书",
                category=category,
                user_id=user_id
            )
            db.add(new_word)
            imported += 1

        db.commit()

        return {
            "success": True,
            "message": f"词书导入成功，共识别 {imported} 个单词",
            "imported_count": imported,
            "category": category
        }


word_service = WordService()
