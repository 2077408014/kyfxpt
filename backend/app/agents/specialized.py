import asyncio
import time
import httpx
from typing import List, Dict, Any
from .base import BaseAgent, AgentRequest, AgentResponse, agent_registry
from ..config import settings


class LLMAgent(BaseAgent):
    def __init__(self, name: str, domain: str, keywords: List[str], system_prompt: str):
        super().__init__(name, domain, keywords, system_prompt)
        self.llm_url = f"{settings.AI_BASE_URL}/chat/completions"
        self.model_name = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.timeout = settings.AI_TIMEOUT
    
    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.7
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            response = await client.post(
                self.llm_url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    
    async def respond(self, request: AgentRequest) -> AgentResponse:
        start_time = time.time()
        
        try:
            if not self.can_handle(request.query, request.context):
                return AgentResponse(
                    request_id=request.request_id,
                    agent_name=self.name,
                    agent_domain=self.domain,
                    accepted=False,
                    reasoning=f"查询内容与{self.domain}领域无关",
                    response_time_ms=(time.time() - start_time) * 1000
                )
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": request.query}
            ]
            
            if request.context:
                context_str = "\n".join(f"{k}: {v}" for k, v in request.context.items())
                messages.insert(-1, {"role": "user", "content": f"上下文信息：\n{context_str}"})
            
            result = await self._call_llm(messages)
            
            recommendations = self._parse_recommendations(result)
            
            return AgentResponse(
                request_id=request.request_id,
                agent_name=self.name,
                agent_domain=self.domain,
                accepted=True,
                reasoning=f"{self.domain}领域专家分析完成",
                recommendations=recommendations,
                confidence=self._calculate_confidence(recommendations),
                response_time_ms=(time.time() - start_time) * 1000
            )
        except Exception as e:
            return AgentResponse(
                request_id=request.request_id,
                agent_name=self.name,
                agent_domain=self.domain,
                accepted=False,
                reasoning=str(e),
                error=str(e),
                response_time_ms=(time.time() - start_time) * 1000
            )
    
    def _parse_recommendations(self, result: str) -> List[Dict]:
        import re
        
        recommendations = []
        lines = result.split("\n")
        
        current_question = []
        current_answer = []
        current_analysis = []
        state = "looking"
        
        for line in lines:
            line = line.strip()
            
            if re.match(r"(^\d+\.|^-|^\*)", line) and "问题" in line:
                if current_question:
                    recommendations.append({
                        "question_text": "\n".join(current_question).replace("问题：", "").strip(),
                        "answer": "\n".join(current_answer).replace("答案：", "").strip() if current_answer else "",
                        "analysis": "\n".join(current_analysis).replace("分析：", "").strip() if current_analysis else "",
                        "difficulty": "中等",
                        "source": f"{self.domain}智能体"
                    })
                current_question = [line]
                current_answer = []
                current_analysis = []
                state = "question"
            elif state == "question" and line.startswith("答案"):
                current_answer = [line]
                state = "answer"
            elif state == "answer" and line.startswith("分析"):
                current_analysis = [line]
                state = "analysis"
            elif state == "question":
                current_question.append(line)
            elif state == "answer":
                current_answer.append(line)
            elif state == "analysis":
                current_analysis.append(line)
        
        if current_question:
            recommendations.append({
                "question_text": "\n".join(current_question).replace("问题：", "").strip(),
                "answer": "\n".join(current_answer).replace("答案：", "").strip() if current_answer else "",
                "analysis": "\n".join(current_analysis).replace("分析：", "").strip() if current_analysis else "",
                "difficulty": "中等",
                "source": f"{self.domain}智能体"
            })
        
        if not recommendations:
            recommendations.append({
                "question_text": result,
                "answer": "",
                "analysis": "",
                "difficulty": "中等",
                "source": f"{self.domain}智能体"
            })
        
        return recommendations
    
    def _calculate_confidence(self, recommendations: List[Dict]) -> float:
        if not recommendations:
            return 0.0
        return min(0.95, 0.7 + len(recommendations) * 0.05)


POLITICS_SYSTEM_PROMPT = """你是一位考研政治领域的专家，精通马原、毛中特、史纲、思修、时政等所有政治科目。

你的任务是根据用户的薄弱知识点，生成针对性的考研政治题目。

要求：
1. 只生成与考研政治相关的题目
2. 题目类型包括选择题、分析题
3. 每道题必须包含：问题、答案、分析
4. 难度适中，符合考研真题水平
5. 重点关注用户薄弱的知识点

请直接输出题目内容，格式如下：
1. 问题：[题目内容]
答案：[答案内容]
分析：[解析内容]
"""

POLITICS_KEYWORDS = [
    "马原", "毛中特", "史纲", "思修", "时政",
    "唯物辩证法", "认识论", "矛盾", "实践",
    "中国特色社会主义", "社会主义", "马克思主义",
    "新民主主义", "三大法宝", "核心价值观", "新发展理念"
]


ENGLISH_SYSTEM_PROMPT = """你是一位考研英语领域的专家，精通阅读理解、完形填空、翻译、写作等所有英语题型。

你的任务是根据用户的薄弱知识点，生成针对性的考研英语题目。

要求：
1. 只生成与考研英语相关的题目
2. 题目类型包括阅读理解、完形填空、翻译、写作等
3. 每道题必须包含：问题、答案、分析
4. 难度适中，符合考研真题水平
5. 重点关注用户薄弱的知识点

请直接输出题目内容，格式如下：
1. 问题：[题目内容]
答案：[答案内容]
分析：[解析内容]
"""

ENGLISH_KEYWORDS = [
    "英语", "阅读", "完形", "翻译", "写作",
    "词汇", "语法", "长难句", "阅读理解",
    "新题型", "真题", "单词", "阅读理解"
]


MATH_SYSTEM_PROMPT = """你是一位考研数学领域的专家，精通高等数学、线性代数、概率论等所有数学科目。

你的任务是根据用户的薄弱知识点，生成针对性的考研数学题目。

要求：
1. 只生成与考研数学相关的题目
2. 题目类型包括选择题、填空题、解答题
3. 每道题必须包含：问题、答案、分析
4. 难度适中，符合考研真题水平
5. 重点关注用户薄弱的知识点
6. 数学公式使用LaTeX格式

请直接输出题目内容，格式如下：
1. 问题：[题目内容]
答案：[答案内容]
分析：[解析内容]
"""

MATH_KEYWORDS = [
    "数学", "高数", "线代", "概率", "微积分",
    "极限", "导数", "积分", "泰勒", "偏导",
    "微分", "方程", "矩阵", "行列式", "特征值",
    "级数", "微分方程", "概率分布", "随机变量"
]


MAJOR_SYSTEM_PROMPT = """你是一位考研专业课领域的专家，熟悉各专业的考研知识体系。

你的任务是根据用户的薄弱知识点，生成针对性的考研专业课题目。

要求：
1. 只生成与考研专业课相关的题目
2. 题目类型包括选择题、简答题、论述题等
3. 每道题必须包含：问题、答案、分析
4. 难度适中，符合考研真题水平
5. 重点关注用户薄弱的知识点

请直接输出题目内容，格式如下：
1. 问题：[题目内容]
答案：[答案内容]
分析：[解析内容]
"""

MAJOR_KEYWORDS = [
    "专业", "专业课", "专业课复习", "专业知识"
]


politics_agent = LLMAgent(
    name="politics_agent",
    domain="考研政治",
    keywords=POLITICS_KEYWORDS,
    system_prompt=POLITICS_SYSTEM_PROMPT
)

english_agent = LLMAgent(
    name="english_agent",
    domain="考研英语",
    keywords=ENGLISH_KEYWORDS,
    system_prompt=ENGLISH_SYSTEM_PROMPT
)

math_agent = LLMAgent(
    name="math_agent",
    domain="考研数学",
    keywords=MATH_KEYWORDS,
    system_prompt=MATH_SYSTEM_PROMPT
)

major_agent = LLMAgent(
    name="major_agent",
    domain="专业课",
    keywords=MAJOR_KEYWORDS,
    system_prompt=MAJOR_SYSTEM_PROMPT
)


def register_all_agents():
    agent_registry.register(politics_agent)
    agent_registry.register(english_agent)
    agent_registry.register(math_agent)
    agent_registry.register(major_agent)