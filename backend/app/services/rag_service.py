import requests
import os
import random
from ..config import settings
from ..services.knowledge_base_service import knowledge_base_service


SYSTEM_PROMPT = """你是一个专业的考研复习助手。请根据以下提供的知识库内容回答用户的问题。

知识库内容：
{context}

用户问题：{question}

回答要求：
1. 必须基于知识库内容回答，不得编造信息
2. 如果知识库中没有相关内容，请明确说明"该问题超出知识库范围"
3. 如果知识库内容不足，请结合你的知识补充，但要注明"补充信息"
4. 回答要简洁明了，使用markdown格式
5. 在回答末尾标注来源文档名称
6. **数学公式必须使用标准LaTeX格式**：
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
7. 输出示例（极限题）：求极限 $\lim_{x \to 0} \frac{\sin x}{x}$ 的值，答案是1。
8. 输出示例（导数题）：函数 $f(x) = x^2$ 的导数是 $f'(x) = 2x$。
"""

AI_RESPONSES = {
    "default": [
        "好的，我来帮您解答！",
        "这个问题很有意思，让我为您分析一下。",
        "考研复习是一个系统性的工程，需要合理规划。",
        "坚持就是胜利，加油！"
    ],
    "考研英语": [
        "考研英语分为英语一和英语二，英语一难度较高。",
        "阅读理解是得分重点，建议每天练习2-3篇。",
        "写作需要积累模板和素材，每周至少练习1篇。",
        "词汇是基础，建议使用艾宾浩斯记忆法进行复习。",
        "完形填空考察综合能力，建议放在最后做。",
        "翻译题要注意中英文表达差异，确保语句通顺。"
    ],
    "考研政治": [
        "政治分为马原、毛中特、史纲、思修、时政五个部分。",
        "马原重在理解，毛中特重在记忆。",
        "建议暑期开始系统复习，10月份开始刷题。",
        "肖秀荣系列是考研政治的经典资料。",
        "时政部分要关注当年的重大事件。",
        "分析题需要掌握答题模板和关键词。"
    ],
    "考研数学": [
        "数学分为数一、数二、数三，难度依次递减。",
        "高数占比最高，是复习的重点。",
        "建议从基础开始，打好知识点基础。",
        "刷题是关键，建议完成至少两遍真题。",
        "错题要反复研究，总结解题方法。",
        "线代和概率虽然分值少，但不能忽视。"
    ],
    "专业课": [
        "专业课要以目标院校的参考书为主。",
        "历年真题是最重要的复习资料。",
        "建议联系学长学姐获取复习经验。",
        "笔记整理很重要，便于后期复习。",
        "关注目标院校的招生政策和考试大纲变化。"
    ],
    "复习规划": [
        "建议制定详细的复习计划，按月、周、日安排。",
        "暑期是黄金复习期，要充分利用。",
        "9-10月份是强化阶段，重点刷题。",
        "11-12月份是冲刺阶段，模拟考试很重要。",
        "注意劳逸结合，保持良好的心态。",
        "定期总结复习进度，及时调整计划。"
    ],
    "心态调整": [
        "考研是一场持久战，保持积极心态很重要。",
        "遇到困难时可以适当放松，不要给自己太大压力。",
        "找研友一起学习，互相鼓励。",
        "相信自己的努力一定会有回报。",
        "适当的运动有助于缓解压力。"
    ]
}


class RAGService:
    def __init__(self):
        self.max_tokens = settings.AI_MAX_TOKENS
        self.timeout = settings.AI_TIMEOUT

    def chat(self, user_id: int, question: str, top_k: int = 3, threshold: float = 0.3, ai_config: dict = None, subject: str = None) -> dict:
        relevant_chunks = knowledge_base_service.search(user_id, question, top_k, threshold, subject=subject)
        
        from_knowledge_base = len(relevant_chunks) > 0
        
        if not relevant_chunks:
            answer = self._call_llm(question, "", ai_config)
            return {
                "answer": answer,
                "source": None,
                "relevant_chunks": [],
                "from_knowledge_base": False
            }
        
        context = ""
        sources = set()
        
        for chunk in relevant_chunks:
            context += f"【来源：{chunk['metadata'].get('filename', '未知文档')}】\n"
            context += f"{chunk['content']}\n\n"
            sources.add(chunk['metadata'].get('filename', '未知文档'))
        
        answer = self._call_llm(question, context, ai_config)
        
        return {
            "answer": answer,
            "source": ", ".join(sources),
            "relevant_chunks": relevant_chunks,
            "from_knowledge_base": from_knowledge_base
        }

    def search_only(self, user_id: int, question: str, top_k: int = 3, threshold: float = 0.3, subject: str = None) -> dict:
        relevant_chunks = knowledge_base_service.search(user_id, question, top_k, threshold, subject=subject)
        return {"results": relevant_chunks}

    def _classify_question(self, question: str) -> str:
        question_lower = question.lower()
        
        if any(keyword in question_lower for keyword in ["英语", "阅读", "写作", "翻译", "完形", "词汇"]):
            return "考研英语"
        if any(keyword in question_lower for keyword in ["政治", "马原", "毛中特", "史纲", "思修", "时政"]):
            return "考研政治"
        if any(keyword in question_lower for keyword in ["数学", "高数", "线代", "概率", "微积分", "极限", "导数", "积分", "泰勒", "偏导", "微分", "方程"]):
            return "考研数学"
        if any(keyword in question_lower for keyword in ["专业", "专业课"]):
            return "专业课"
        if any(keyword in question_lower for keyword in ["计划", "安排", "规划", "时间"]):
            return "复习规划"
        if any(keyword in question_lower for keyword in ["心态", "压力", "焦虑", "放松"]):
            return "心态调整"
        
        return "default"
    
    def _call_llm(self, question: str, context: str, ai_config: dict = None) -> str:
        if context:
            prompt = SYSTEM_PROMPT.format(context=context, question=question)
        else:
            prompt = f"你是一个专业的考研复习助手。请回答以下问题：\n\n{question}\n\n如果这个问题超出你的知识范围，请明确说明。"
        
        if ai_config and ai_config.get("api_key"):
            llm_url = f"{ai_config['base_url']}/chat/completions"
            model_name = ai_config["model"]
            api_key = ai_config["api_key"]
        else:
            llm_url = f"{settings.AI_BASE_URL}/chat/completions"
            model_name = settings.AI_MODEL
            api_key = None
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "你是一个专业的考研复习助手，精通考研各科目知识。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            response = requests.post(llm_url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"RAG LLM call failed: {e}")
            category = self._classify_question(question)
            responses = AI_RESPONSES.get(category, AI_RESPONSES["default"])
            fallback_answer = responses[random.randint(0, len(responses) - 1)]
            
            if context:
                return f"抱歉，LLM服务暂时不可用。以下是知识库中相关内容：\n\n{context}\n\n参考建议：{fallback_answer}"
            return fallback_answer


rag_service = RAGService()