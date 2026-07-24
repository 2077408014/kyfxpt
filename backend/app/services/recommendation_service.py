from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
from ..models.recommendation import Recommendation, UserWeakPoint
from ..models.mistake import Mistake
from ..schemas.recommendation import RecommendationCreate, RecommendationComplete
from ..agents.orchestrator import recommendation_orchestrator
from ..agents.specialized import register_all_agents
from ..services.agent_log_service import agent_log_service


register_all_agents()


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
    
    async def generate_recommendations(self, db: Session, user_id: int, count: int = 5, subject: str = None) -> list:
        weak_points = self.analyze_weak_points(db, user_id)
        
        recommendations = []
        
        mistakes = db.query(Mistake).filter(
            Mistake.user_id == user_id
        )
        
        if subject:
            mistakes = mistakes.filter(Mistake.subject == subject)
        
        mistakes = mistakes.order_by(Mistake.created_at.desc()).all()
        
        for mistake in mistakes[:count]:
            existing = db.query(Recommendation).filter(
                Recommendation.user_id == user_id,
                Recommendation.question_text == mistake.question_text,
                Recommendation.completed == False
            ).first()
            
            if not existing:
                recommendations.append({
                    "question_text": mistake.question_text,
                    "answer": mistake.answer,
                    "analysis": mistake.analysis,
                    "difficulty": mistake.difficulty,
                    "source": "错题推荐",
                    "agent_domain": mistake.subject,
                    "knowledge_point": mistake.knowledge_point,
                    "confidence": 0.95
                })
        
        remaining_count = count - len(recommendations)
        
        if remaining_count > 0:
            try:
                ai_recommendations = await self._generate_ai_recommendations(db, user_id, weak_points, remaining_count, subject)
                recommendations.extend(ai_recommendations)
            except ValueError as ve:
                print(f"生成AI推荐题目失败: {ve}")
        
        if not recommendations:
            from ..services.ai_service import ai_service
            user_config = ai_service._get_user_ai_config(db, user_id)
            
            if not user_config["api_key"]:
                raise ValueError("无法生成推荐题目：请先在AI配置页面设置API Key")
            
            if subject:
                subject_mistakes = db.query(Mistake).filter(Mistake.user_id == user_id, Mistake.subject == subject).count()
                if subject_mistakes == 0:
                    raise ValueError(f"无法生成推荐题目：科目「{subject}」暂无错题，请先添加该科目的错题")
                else:
                    raise ValueError(f"无法生成推荐题目：科目「{subject}」的题目生成失败，请稍后重试")
            else:
                total_mistakes = db.query(Mistake).filter(Mistake.user_id == user_id).count()
                if total_mistakes == 0:
                    raise ValueError("无法生成推荐题目：暂无错题，请先添加错题")
                else:
                    raise ValueError("无法生成推荐题目：题目生成失败，请稍后重试")
        
        db_recommendations = []
        
        for rec in recommendations:
            existing = db.query(Recommendation).filter(
                Recommendation.user_id == user_id,
                Recommendation.question_text == rec.get("question_text", ""),
                Recommendation.completed == False
            ).first()
            
            if not existing:
                new_rec = Recommendation(
                    user_id=user_id,
                    subject=rec.get("agent_domain", rec.get("subject", "未知")),
                    knowledge_point=rec.get("knowledge_point", rec.get("question_text", "")[:100]) if rec.get("question_text") else "",
                    difficulty=rec.get("difficulty", "中等"),
                    question_text=rec.get("question_text", ""),
                    answer=rec.get("answer", ""),
                    analysis=rec.get("analysis", ""),
                    source=rec.get("source", "AI生成"),
                    result=None,
                    completed=False
                )
                db.add(new_rec)
                db_recommendations.append(new_rec)
        
        db.commit()
        
        return [self._to_dict(rec) for rec in db_recommendations]
    
    async def _generate_ai_recommendations(self, db: Session, user_id: int, weak_points: list, count: int, subject: str = None) -> list:
        from ..services.rag_service import rag_service
        from ..services.ai_service import ai_service
        
        recommendations = []
        
        filtered_weak_points = weak_points
        if subject:
            filtered_weak_points = [wp for wp in weak_points if wp["subject"] == subject]
        
        if not filtered_weak_points:
            if subject:
                raise ValueError(f"科目「{subject}」暂无薄弱知识点，请先添加该科目的错题")
            else:
                raise ValueError("暂无薄弱知识点，请先添加错题")
        
        user_config = ai_service._get_user_ai_config(db, user_id)
        
        try:
            for wp in filtered_weak_points[:count]:
                wp_subject = wp["subject"]
                knowledge_point = wp["knowledge_point"]
                
                search_query = f"{wp_subject} {knowledge_point} 考研题目"
                rag_result = rag_service.chat(user_id, search_query, top_k=3, threshold=0.3, ai_config=user_config)
                
                context = ""
                for chunk in rag_result.get("relevant_chunks", []):
                    context += f"【来源：{chunk['metadata'].get('filename', '未知文档')}】\n"
                    context += f"{chunk['content']}\n\n"
                
                example_output = '{{"question_text": "求极限 $\\\\lim_{x \\\\to 0} \\\\frac{\\\\sin x}{x}$ 的值。", "answer": "1", "analysis": "根据重要极限公式，$\\\\lim_{x \\\\to 0} \\\\frac{\\\\sin x}{x} = 1$", "difficulty": "简单"}}'
                
                prompt = """你是一个专业的考研数学出题专家。请根据以下知识库内容，为考研复习生成一道关于""" + \
                    f"【{wp_subject} - {knowledge_point}】" + """的数学练习题。

知识库内容：
""" + context + """

要求：
1. 题目类型：选择题或填空题或解答题（根据知识点选择合适的题型）
2. 必须包含：题目（question_text）、答案（answer）、解析（analysis）
3. 数学公式必须使用标准LaTeX格式：
   - 极限：使用 $\\\\lim_{x \\\\to a} f(x)$ 格式
   - 分数：使用 $\\\\frac{分子}{分母}$ 格式
   - 指数：使用 $e^{\\\\text{指数}}$ 或 $a^{\\\\text{指数}}$ 格式
   - 三角函数：使用 \\\\sin, \\\\cos, \\\\tan, \\\\arcsin, \\\\arccos, \\\\arctan 等
   - 对数：使用 \\\\ln, \\\\log 格式
   - 导数：使用 $f'(x)$ 或 $\\\\frac{df}{dx}$ 格式
   - 积分：使用 $\\\\int$ 格式
   - 求和：使用 $\\\\sum$ 格式
4. 所有数学符号、公式、变量、函数都必须用LaTeX格式表示，行内公式用$...$包裹，独立公式用$$...$$包裹
5. 数字"1"和字母"l"要区分清楚，"0"和字母"o"要区分清楚
6. 输出格式必须是纯JSON格式，不要包含任何markdown标记或额外文字
7. JSON结构：{"question_text": "...", "answer": "...", "analysis": "...", "difficulty": "简单/中等/困难"}

示例输出（极限题）：
{"question_text": "求极限 $\\\\lim_{x \\\\to 0} \\\\frac{e^{\\\\sin x} - 1}{x}$ 的值。", "answer": "1", "analysis": "当 $x \\\\to 0$ 时，$\\\\sin x \\\\sim x$，所以 $e^{\\\\sin x} - 1 \\\\sim \\\\sin x \\\\sim x$，因此 $\\\\lim_{x \\\\to 0} \\\\frac{e^{\\\\sin x} - 1}{x} = \\\\lim_{x \\\\to 0} \\\\frac{x}{x} = 1$", "difficulty": "中等"}

示例输出（导数题）：
{"question_text": "求函数 $f(x) = x^{\\\\ln x}$ 的导数 $f'(x)$。", "answer": "$x^{\\\\ln x - 1} \\\\cdot 2 \\\\ln x$", "analysis": "使用对数求导法，设 $y = x^{\\\\ln x}$，两边取对数得 $\\\\ln y = (\\\\ln x)^2$，两边对x求导得 $\\\\frac{y'}{y} = \\\\frac{2 \\\\ln x}{x}$，所以 $y' = x^{\\\\ln x} \\\\cdot \\\\frac{2 \\\\ln x}{x} = x^{\\\\ln x - 1} \\\\cdot 2 \\\\ln x$", "difficulty": "困难"}

示例输出（积分题）：
{"question_text": "计算不定积分 $\\\\int x \\\\cdot e^{2x} dx$。", "answer": "$\\\\frac{1}{4}(2x - 1)e^{2x} + C$", "analysis": "使用分部积分法，设 $u = x$，$dv = e^{2x}dx$，则 $du = dx$，$v = \\\\frac{1}{2}e^{2x}$。根据分部积分公式 $\\\\int u dv = uv - \\\\int v du$，得 $\\\\int x e^{2x} dx = \\\\frac{1}{2}x e^{2x} - \\\\frac{1}{2} \\\\int e^{2x} dx = \\\\frac{1}{2}x e^{2x} - \\\\frac{1}{4}e^{2x} + C = \\\\frac{1}{4}(2x - 1)e^{2x} + C$", "difficulty": "中等"}

注意：必须严格按照示例格式输出，数学公式必须正确使用LaTeX语法！
"""
                
                ai_result = self._call_ai_for_question(db, user_id, prompt)
                
                try:
                    import json
                    parsed = json.loads(ai_result)
                    
                    recommendations.append({
                        **parsed,
                        "agent_domain": wp_subject,
                        "knowledge_point": knowledge_point,
                        "source": "AI+知识库",
                        "confidence": 0.85
                    })
                except json.JSONDecodeError:
                    recommendations.append({
                        "question_text": f"【{wp_subject} - {knowledge_point}】根据知识库内容，请分析以下问题：{knowledge_point}的核心考点是什么？",
                        "answer": "请参考知识库内容回答",
                        "analysis": ai_result,
                        "difficulty": "中等",
                        "agent_domain": wp_subject,
                        "knowledge_point": knowledge_point,
                        "source": "AI+知识库",
                        "confidence": 0.7
                    })
                
                if len(recommendations) >= count:
                    break
        
        except ValueError as ve:
            raise ve
        except Exception as e:
            print(f"AI生成推荐题目失败: {e}")
            raise ValueError(f"AI生成题目失败: {str(e)}")
        
        return recommendations
    
    def _call_ai_for_question(self, db: Session, user_id: int, prompt: str) -> str:
        from ..services.ai_service import ai_service
        
        user_config = ai_service._get_user_ai_config(db, user_id)
        
        if not user_config["api_key"]:
            raise ValueError("用户未配置AI服务，请先在AI配置页面设置API Key")
        
        try:
            import requests
            
            llm_url = f"{user_config['base_url']}/chat/completions"
            payload = {
                "model": user_config["model"],
                "messages": [
                    {"role": "system", "content": "你是一个专业的考研数学出题专家，擅长根据知识点生成高质量的练习题。"},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1024,
                "temperature": 0.5
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_config['api_key']}"
            }
            
            response = requests.post(llm_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except ValueError as ve:
            raise ve
        except Exception as e:
            print(f"AI生成题目失败: {e}")
            raise ValueError(f"AI服务调用失败: {str(e)}")
    
    def _generate_preset_recommendations(self, weak_points: list, count: int, subject: str = None) -> list:
        recommendations = []
        recommended_ids = set()
        
        subjects_with_mistakes = set(wp["subject"] for wp in weak_points)
        
        if subject:
            available_subjects = [subject]
        else:
            available_subjects = list(subjects_with_mistakes) if subjects_with_mistakes else list(PRESET_QUESTIONS.keys())
        
        for wp in sorted(weak_points, key=lambda x: x["weak_level"], reverse=True):
            if len(recommendations) >= count:
                break
            
            wp_subject = wp["subject"]
            knowledge_point = wp["knowledge_point"]
            
            if wp_subject not in available_subjects:
                continue
            
            if wp_subject in PRESET_QUESTIONS:
                if knowledge_point in PRESET_QUESTIONS[wp_subject]:
                    for q in PRESET_QUESTIONS[wp_subject][knowledge_point]:
                        if len(recommendations) >= count:
                            break
                        
                        question_hash = q["question_text"][:100]
                        if question_hash in recommended_ids:
                            continue
                        
                        recommended_ids.add(question_hash)
                        recommendations.append({
                            **q,
                            "agent_domain": wp_subject,
                            "confidence": 0.8,
                            "response_time_ms": 0
                        })
        
        if len(recommendations) < count:
            for sub in available_subjects:
                if len(recommendations) >= count:
                    break
                if sub in PRESET_QUESTIONS:
                    for knowledge_point, questions in PRESET_QUESTIONS[sub].items():
                        if len(recommendations) >= count:
                            break
                        for q in questions:
                            if len(recommendations) >= count:
                                break
                            
                            question_hash = q["question_text"][:100]
                            if question_hash in recommended_ids:
                                continue
                            
                            recommended_ids.add(question_hash)
                            recommendations.append({
                                **q,
                                "agent_domain": sub,
                                "confidence": 0.75,
                                "response_time_ms": 0
                            })
        
        if len(recommendations) < count and not subject:
            for sub, topics in PRESET_QUESTIONS.items():
                if len(recommendations) >= count:
                    break
                if sub in available_subjects:
                    continue
                for knowledge_point, questions in topics.items():
                    if len(recommendations) >= count:
                        break
                    for q in questions:
                        if len(recommendations) >= count:
                            break
                        
                        question_hash = q["question_text"][:100]
                        if question_hash in recommended_ids:
                            continue
                        
                        recommended_ids.add(question_hash)
                        recommendations.append({
                            **q,
                            "agent_domain": sub,
                            "confidence": 0.7,
                            "response_time_ms": 0
                        })
        
        return recommendations
    
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
    
    def get_agent_status(self) -> list:
        return recommendation_orchestrator.get_agent_status()
    
    def toggle_agent(self, agent_name: str, enabled: bool):
        recommendation_orchestrator.toggle_agent(agent_name, enabled)
    
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