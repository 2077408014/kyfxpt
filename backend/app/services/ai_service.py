from sqlalchemy.orm import Session
from datetime import datetime
from ..models.ai_chat import AIChatHistory
import requests
import os
from dotenv import load_dotenv
from ..config import settings
from .llm_service import llm_service

load_dotenv()


SYSTEM_PROMPT = """你是一个专业的考研复习助手，精通考研英语、政治、数学、专业课等各科目知识。

你的任务是：
1. 回答用户关于考研复习的各类问题
2. 提供专业的学习建议和备考策略
3. 解释考研相关的概念和知识点
4. 根据用户需求提供个性化的复习指导

格式要求：
- 使用markdown格式增强可读性（列表、加粗、标题等）
- **数学公式必须使用标准LaTeX格式**：
  - 所有数学符号、公式、变量、函数都必须用LaTeX格式表示
  - 行内公式用$...$包裹，独立公式用$$...$$包裹
  - 极限：使用 $\lim_{x \to a} f(x)$ 格式
  - 分数：使用 $\frac{分子}{分母}$ 格式
  - 指数：使用 $e^{指数}$ 格式
  - 三角函数：使用 \sin, \cos, \tan 等
  - 对数：使用 \ln, \log 格式
  - 导数：使用 $f'(x)$ 格式
  - 积分：使用 $\int$ 格式
  - 求和：使用 $\sum$ 格式
  - 希腊字母：使用 \alpha, \beta, \gamma, \pi 等
- 输出示例（极限题）：求极限 $\lim_{x \to 0} \frac{\sin x}{x}$ 的值，答案是1。
- 输出示例（导数题）：函数 $f(x) = x^2$ 的导数是 $f'(x) = 2x$。
- 输出示例（积分题）：不定积分 $\int x^2 dx = \frac{1}{3}x^3 + C$。

如果用户的问题不属于考研相关内容，你可以礼貌地说明你专注于考研复习领域。

你的回答应该帮助用户更好地备考，提供有价值的信息。
"""


class AIService:
    def __init__(self):
        self.default_api_key = os.getenv("AI_API_KEY", "")
        self.default_base_url = os.getenv("AI_BASE_URL", "https://api.deepseek.com/v1")
        self.default_model = os.getenv("AI_MODEL", "deepseek-chat")
        self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "2048"))
        self.timeout = int(os.getenv("AI_TIMEOUT", "60"))
        self.local_llm_available = False
    
    def chat_with_rag(self, db: Session, user_id: int, message: str, top_k: int = 3, threshold: float = 0.3, subject: str = None, only_knowledge_base: bool = False) -> dict:
        from .rag_service import rag_service

        try:
            user_config = self._get_user_ai_config(db, user_id)
            rag_result = rag_service.chat(user_id, message, top_k, threshold, user_config, subject=subject, only_knowledge_base=only_knowledge_base)

            source = rag_result.get("source") or (rag_result.get("from_knowledge_base") and "知识库") or "AI"

            if only_knowledge_base and not rag_result.get("from_knowledge_base"):
                return {
                    "answer": rag_result.get("answer", "未从您的资料中找到相关内容。"),
                    "category": "知识库",
                    "suggestions": [],
                    "from_knowledge_base": False,
                    "relevant_chunks": rag_result.get("relevant_chunks", []),
                    "source": None
                }

            # RAG 成功，question 和 answer 各保存一次
            self._save_message(db, user_id, "question", message)
            self._save_message(db, user_id, "answer", rag_result["answer"], source)

            return {
                "answer": rag_result["answer"],
                "category": source,
                "suggestions": [],
                "from_knowledge_base": rag_result.get("from_knowledge_base", False),
                "relevant_chunks": rag_result.get("relevant_chunks", []),
                "source": rag_result.get("source")
            }
        except Exception as e:
            print(f"RAG chat failed: {e}")
            import traceback
            traceback.print_exc()
            if only_knowledge_base:
                return {
                    "answer": f"检索失败：{str(e)}",
                    "category": "知识库",
                    "suggestions": [],
                    "from_knowledge_base": False,
                    "relevant_chunks": [],
                    "source": None
                }
            return self.chat(db, user_id, message, skip_save_question=True)

    def _get_user_ai_config(self, db: Session, user_id: int) -> dict:
        from ..models.user import User
        from ..models.ai_config import AIConfig

        user = db.query(User).filter(User.id == user_id).first()

        # 优先使用 ai_configs 表中激活的配置
        if user and user.active_ai_config_id:
            config = db.query(AIConfig).filter(
                AIConfig.id == user.active_ai_config_id,
                AIConfig.user_id == user_id
            ).first()
            if config:
                return {
                    "api_key": config.api_key,
                    "base_url": config.base_url or self.default_base_url,
                    "model": config.model or self.default_model
                }

        # 回退到 users 表中的旧配置字段（兼容已有数据）
        if user and user.ai_api_key:
            return {
                "api_key": user.ai_api_key,
                "base_url": user.ai_api_base_url or self.default_base_url,
                "model": user.ai_api_model or self.default_model
            }

        return {
            "api_key": self.default_api_key,
            "base_url": self.default_base_url,
            "model": self.default_model
        }

    def chat(self, db: Session, user_id: int, message: str, skip_save_question: bool = False) -> dict:
        if not skip_save_question:
            self._save_message(db, user_id, "question", message)
        
        answer = ""
        source = "default"
        
        user_config = self._get_user_ai_config(db, user_id)
        
        if user_config["api_key"]:
            try:
                answer = self._call_ai_model(db, user_id, message, user_config)
                source = "AI"
            except Exception as e:
                print(f"AI API call failed: {e}")
                answer = f"抱歉，AI 服务调用失败（{e}），暂时无法回答您的问题。请检查 AI 配置是否正确。"
        elif settings.USE_LOCAL_LLM:
            try:
                answer = self._call_local_llm(message)
                source = "Local LLM"
            except Exception as e:
                print(f"Local LLM call failed: {e}")
                answer = f"抱歉，本地 LLM 调用失败（{e}），暂时无法回答您的问题。"
        else:
            answer = "抱歉，尚未配置 AI 服务，无法回答您的问题。请在「AI 配置」页面设置 API。"
        
        self._save_message(db, user_id, "answer", answer, source)
        
        return {
            "answer": answer,
            "category": source,
            "suggestions": []
        }
    
    def command(self, db: Session, user_id: int, command: str) -> dict:
        self._save_message(db, user_id, "question", command)
        
        command_lower = command.lower()
        result = {"action": "unknown", "message": "无法识别的指令"}
        
        if any(keyword in command_lower for keyword in ["错题", "错误", "mistake"]):
            result = {
                "action": "open_mistakes",
                "message": "正在打开错题管理模块..."
            }
        elif any(keyword in command_lower for keyword in ["单词", "背诵", "recitation"]):
            result = {
                "action": "start_recitation",
                "message": "正在启动单词背诵模式..."
            }
        elif any(keyword in command_lower for keyword in ["推荐", "题目"]):
            result = {
                "action": "generate_recommendation",
                "message": "正在为您推荐相关题目..."
            }
        elif any(keyword in command_lower for keyword in ["薄弱", "分析", "知识点"]):
            result = {
                "action": "analyze_weak_points",
                "message": "正在分析您的薄弱知识点..."
            }
        elif any(keyword in command_lower for keyword in ["计划", "安排", "规划"]):
            result = {
                "action": "generate_plan",
                "message": "正在为您生成个性化复习计划..."
            }
        elif any(keyword in command_lower for keyword in ["统计", "报告", "进度"]):
            result = {
                "action": "generate_report",
                "message": "正在生成学习报告..."
            }
        
        self._save_message(db, user_id, "answer", result["message"], "command")
        
        return result
    
    def get_history(self, db: Session, user_id: int, limit: int = 20) -> list:
        messages = db.query(AIChatHistory).filter(
            AIChatHistory.user_id == user_id
        ).order_by(AIChatHistory.created_at.desc()).limit(limit).all()
        
        return [self._to_dict(msg) for msg in reversed(messages)]
    
    def clear_history(self, db: Session, user_id: int) -> bool:
        db.query(AIChatHistory).filter(AIChatHistory.user_id == user_id).delete()
        db.commit()
        return True
    
    def _call_local_llm(self, message: str) -> str:
        llm_url = f"{settings.AI_BASE_URL}/chat/completions"
        
        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message}
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(llm_url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    
    def _call_ai_model(self, db: Session, user_id: int, message: str, config: dict = None) -> str:
        if config is None:
            config = self._get_user_ai_config(db, user_id)
        
        history = self._get_conversation_history(db, user_id)
        
        history_messages = []
        for msg in history:
            role = "user" if msg["message_type"] == "question" else "assistant"
            history_messages.append({"role": role, "content": msg["content"]})
        
        print(f"[AI调用] 模型: {config['model']}")
        print(f"[AI调用] 消息数量: {len(history_messages) + 1}")
        
        return llm_service.chat_with_history(
            user_message=message,
            history=history_messages,
            ai_config=config,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.7,
        )
    
    def _get_conversation_history(self, db: Session, user_id: int, limit: int = 10) -> list:
        messages = db.query(AIChatHistory).filter(
            AIChatHistory.user_id == user_id
        ).order_by(AIChatHistory.created_at.desc()).limit(limit).all()
        
        return [self._to_dict(msg) for msg in reversed(messages)]
    
    def _save_message(self, db: Session, user_id: int, message_type: str, content: str, source: str = None):
        message = AIChatHistory(
            user_id=user_id,
            message_type=message_type,
            content=content,
            source=source
        )
        db.add(message)
        db.commit()
    
    def _to_dict(self, msg: AIChatHistory) -> dict:
        return {
            "id": msg.id,
            "user_id": msg.user_id,
            "message_type": msg.message_type,
            "content": msg.content,
            "source": msg.source,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }


ai_service = AIService()
