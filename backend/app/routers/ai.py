from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.ai_service import ai_service
from ..routers.auth import get_current_user
from ..schemas.ai import AIChatRequest, AICommandRequest

router = APIRouter(prefix="/api/ai", tags=["AI问答"])


@router.post("/chat")
def chat(
    data: AIChatRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ai_service.chat(db, current_user.id, data.message)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/command")
def command(
    data: AICommandRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ai_service.command(db, current_user.id, data.command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_history(
    limit: int = Query(20, ge=1, le=100),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        result = ai_service.get_history(db, current_user.id, limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
def clear_history(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        ai_service.clear_history(db, current_user.id)
        return {"message": "聊天记录已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
def recommend_questions(
    data: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        question_text = data.get("question_text", "")
        subject = data.get("subject", "")
        knowledge_point = data.get("knowledge_point", "")
        
        prompt = f"""请根据以下题目信息，生成3-5道同类练习题。

题目信息：
科目：{subject}
知识点：{knowledge_point}
原题内容：{question_text}

要求：
1. 生成的题目要与原题同类型、同知识点
2. 难度要循序渐进
3. 每道题包含题目描述、正确答案和详细解析
4. 数学公式必须使用LaTeX格式，行内公式用$...$包裹，独立公式用$$...$$包裹
5. 输出格式为JSON数组，每个元素包含：
   - question: 题目描述
   - answer: 正确答案
   - analysis: 解析过程

输出示例：
[
  {{
    "question": "题目内容",
    "answer": "答案",
    "analysis": "解析"
  }}
]
"""
        
        result = ai_service.chat(db, current_user.id, prompt)
        answer_text = result.get("answer", "")
        
        import re
        json_match = re.search(r'\[.*\]', answer_text, re.DOTALL)
        if json_match:
            import json
            try:
                questions = json.loads(json_match.group(0))
                return {"questions": questions}
            except json.JSONDecodeError:
                pass
        
        return {"questions": [], "raw_response": answer_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))