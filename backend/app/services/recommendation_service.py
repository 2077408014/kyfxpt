from sqlalchemy.orm import Session
from datetime import datetime
from ..models.recommendation import Recommendation, UserWeakPoint
from ..models.mistake import Mistake
from ..schemas.recommendation import RecommendationCreate, RecommendationComplete

PRESET_QUESTIONS = {
    "马原": {
        "唯物辩证法": [
            {
                "question_text": "矛盾的普遍性和特殊性的关系是什么？",
                "answer": "矛盾的普遍性和特殊性的关系是辩证统一的。普遍性寓于特殊性之中，并通过特殊性表现出来，没有特殊性就没有普遍性；特殊性也离不开普遍性，不包含普遍性的事物是没有的。",
                "analysis": "这是唯物辩证法的核心原理，普遍性和特殊性的关系就是共性与个性、一般与个别的关系。",
                "difficulty": "中等",
                "source": "真题"
            },
            {
                "question_text": "量变和质变的辩证关系是什么？",
                "answer": "量变是质变的必要准备，质变是量变的必然结果；质变又为新的量变开辟道路，使事物在新质的基础上开始新的量变。",
                "analysis": "量变和质变是事物发展的两种状态，二者相互转化、相互渗透。",
                "difficulty": "中等",
                "source": "真题"
            }
        ],
        "认识论": [
            {
                "question_text": "实践是检验真理的唯一标准的原因是什么？",
                "answer": "实践之所以能够成为检验真理的唯一标准，是因为实践是主观见之于客观的活动，是联结主观与客观的桥梁。实践具有直接现实性的特点。",
                "analysis": "这是马克思主义认识论的基本观点，实践标准的唯一性在于它能够把主观认识与客观实际联系起来加以对照。",
                "difficulty": "中等",
                "source": "真题"
            }
        ]
    },
    "毛中特": {
        "中国特色社会主义": [
            {
                "question_text": "中国特色社会主义最本质的特征是什么？",
                "answer": "中国特色社会主义最本质的特征是中国共产党领导，中国特色社会主义制度的最大优势是中国共产党领导。",
                "analysis": "党的领导是中国特色社会主义的根本保证，这是历史和人民的选择。",
                "difficulty": "简单",
                "source": "真题"
            }
        ]
    },
    "史纲": {
        "新民主主义革命": [
            {
                "question_text": "新民主主义革命的三大法宝是什么？",
                "answer": "统一战线、武装斗争、党的建设是中国革命的三大法宝。",
                "analysis": "这三大法宝是毛泽东对中国革命经验的科学总结，是中国革命取得胜利的根本保证。",
                "difficulty": "简单",
                "source": "真题"
            }
        ]
    },
    "思修": {
        "道德修养": [
            {
                "question_text": "社会主义核心价值观的基本内容是什么？",
                "answer": "富强、民主、文明、和谐，自由、平等、公正、法治，爱国、敬业、诚信、友善。",
                "analysis": "社会主义核心价值观分为国家、社会、公民三个层面，是当代中国价值理念的高度概括。",
                "difficulty": "简单",
                "source": "真题"
            }
        ]
    },
    "时政": {
        "热点问题": [
            {
                "question_text": "新发展理念包括哪些内容？",
                "answer": "创新、协调、绿色、开放、共享的新发展理念。",
                "analysis": "新发展理念是习近平新时代中国特色社会主义经济思想的重要内容，是引领我国经济社会发展的指挥棒。",
                "difficulty": "简单",
                "source": "时政"
            }
        ]
    }
}


class RecommendationService:
    def analyze_weak_points(self, db: Session, user_id: int) -> list:
        mistakes = db.query(Mistake).filter(Mistake.user_id == user_id).all()
        
        weak_points = {}
        for mistake in mistakes:
            key = (mistake.subject, mistake.knowledge_point)
            if key not in weak_points:
                weak_points[key] = 0
            weak_points[key] += 1
        
        result = []
        for (subject, knowledge_point), count in weak_points.items():
            existing = db.query(UserWeakPoint).filter(
                UserWeakPoint.user_id == user_id,
                UserWeakPoint.subject == subject,
                UserWeakPoint.knowledge_point == knowledge_point
            ).first()
            
            weak_level = min(5, count)
            
            if existing:
                existing.weak_level = weak_level
                existing.mistake_count = count
                existing.updated_at = datetime.now()
            else:
                new_weak_point = UserWeakPoint(
                    user_id=user_id,
                    subject=subject,
                    knowledge_point=knowledge_point,
                    weak_level=weak_level,
                    mistake_count=count
                )
                db.add(new_weak_point)
        
        db.commit()
        
        weak_points_list = db.query(UserWeakPoint).filter(UserWeakPoint.user_id == user_id).all()
        for wp in weak_points_list:
            result.append({
                "subject": wp.subject,
                "knowledge_point": wp.knowledge_point,
                "weak_level": wp.weak_level,
                "mistake_count": wp.mistake_count,
                "updated_at": wp.updated_at
            })
        
        return result
    
    def generate_recommendations(self, db: Session, user_id: int, count: int = 5) -> list:
        weak_points = self.analyze_weak_points(db, user_id)
        
        recommendations = []
        recommended_ids = set()
        
        for wp in sorted(weak_points, key=lambda x: x["weak_level"], reverse=True):
            if len(recommendations) >= count:
                break
            
            subject = wp["subject"]
            knowledge_point = wp["knowledge_point"]
            
            if subject in PRESET_QUESTIONS:
                if knowledge_point in PRESET_QUESTIONS[subject]:
                    for q in PRESET_QUESTIONS[subject][knowledge_point]:
                        if len(recommendations) >= count:
                            break
                        
                        existing = db.query(Recommendation).filter(
                            Recommendation.user_id == user_id,
                            Recommendation.question_text == q["question_text"],
                            Recommendation.completed == False
                        ).first()
                        
                        if not existing:
                            new_rec = Recommendation(
                                user_id=user_id,
                                subject=subject,
                                knowledge_point=knowledge_point,
                                difficulty=q["difficulty"],
                                question_text=q["question_text"],
                                answer=q["answer"],
                                analysis=q["analysis"],
                                source=q["source"]
                            )
                            db.add(new_rec)
                            recommendations.append(new_rec)
        
        if len(recommendations) < count:
            for subject, topics in PRESET_QUESTIONS.items():
                if len(recommendations) >= count:
                    break
                for knowledge_point, questions in topics.items():
                    if len(recommendations) >= count:
                        break
                    for q in questions:
                        if len(recommendations) >= count:
                            break
                        
                        existing = db.query(Recommendation).filter(
                            Recommendation.user_id == user_id,
                            Recommendation.question_text == q["question_text"],
                            Recommendation.completed == False
                        ).first()
                        
                        if not existing:
                            new_rec = Recommendation(
                                user_id=user_id,
                                subject=subject,
                                knowledge_point=knowledge_point,
                                difficulty=q["difficulty"],
                                question_text=q["question_text"],
                                answer=q["answer"],
                                analysis=q["analysis"],
                                source=q["source"]
                            )
                            db.add(new_rec)
                            recommendations.append(new_rec)
        
        db.commit()
        
        return [self._to_dict(rec) for rec in recommendations]
    
    def get_recommendations(self, db: Session, user_id: int, completed: bool = False) -> list:
        query = db.query(Recommendation).filter(Recommendation.user_id == user_id)
        if completed is not None:
            query = query.filter(Recommendation.completed == completed)
        
        recommendations = query.order_by(Recommendation.created_at.desc()).all()
        return [self._to_dict(rec) for rec in recommendations]
    
    def complete_recommendation(self, db: Session, user_id: int, rec_id: int, result: str) -> dict:
        rec = db.query(Recommendation).filter(
            Recommendation.id == rec_id,
            Recommendation.user_id == user_id
        ).first()
        
        if not rec:
            return None
        
        rec.completed = True
        rec.result = result
        rec.completion_time = datetime.now()
        db.commit()
        
        return self._to_dict(rec)
    
    def get_recommendation_report(self, db: Session, user_id: int) -> dict:
        total = db.query(Recommendation).filter(Recommendation.user_id == user_id).count()
        completed = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.completed == True
        ).count()
        correct = db.query(Recommendation).filter(
            Recommendation.user_id == user_id,
            Recommendation.completed == True,
            Recommendation.result == "正确"
        ).count()
        
        weak_points = db.query(UserWeakPoint).filter(UserWeakPoint.user_id == user_id).all()
        
        return {
            "total_recommendations": total,
            "completed_recommendations": completed,
            "correct_recommendations": correct,
            "accuracy_rate": round(correct / completed * 100, 2) if completed > 0 else 0,
            "weak_points": [
                {
                    "subject": wp.subject,
                    "knowledge_point": wp.knowledge_point,
                    "weak_level": wp.weak_level,
                    "mistake_count": wp.mistake_count
                }
                for wp in sorted(weak_points, key=lambda x: x.weak_level, reverse=True)
            ]
        }
    
    def _to_dict(self, rec: Recommendation) -> dict:
        return {
            "id": rec.id,
            "user_id": rec.user_id,
            "subject": rec.subject,
            "knowledge_point": rec.knowledge_point,
            "difficulty": rec.difficulty,
            "question_text": rec.question_text,
            "answer": rec.answer,
            "analysis": rec.analysis,
            "source": rec.source,
            "completed": rec.completed,
            "result": rec.result,
            "completion_time": rec.completion_time.isoformat() if rec.completion_time else None,
            "created_at": rec.created_at.isoformat() if rec.created_at else None
        }


recommendation_service = RecommendationService()