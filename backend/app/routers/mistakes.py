import os
import uuid
import asyncio
import re
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..config import UPLOAD_PATH
from ..schemas.mistake import (
    MistakeCreate, MistakeUpdate, MistakeResponse,
    MistakeReviewCreate, MistakeReviewResponse,
    MistakeRecognizeRequest, MistakeRecognizeResponse,
    SimilarMistakeResponse
)
from ..services.mistake_service import mistake_service
from ..services.ocr_service import ocr_service
from ..routers.auth import get_current_user
from ..models.user import User

router = APIRouter(prefix="/api/mistakes", tags=["mistakes"])

@router.post("", response_model=MistakeResponse)
async def create_mistake(
    data: MistakeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        mistake = mistake_service.create_mistake(db, current_user.id, data)
        return mistake
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("", response_model=list[MistakeResponse])
async def get_mistakes(
    subject: Optional[str] = Query(None),
    knowledge_point: Optional[str] = Query(None),
    error_type: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    mastery_level: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filters = {k: v for k, v in locals().items() if v is not None and k != "db" and k != "current_user"}
    mistakes = mistake_service.get_mistakes(db, current_user.id, filters)
    return mistakes

@router.post("/upload")
async def upload_mistake_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持 JPG/PNG/WEBP 图片")

    mistakes_dir = UPLOAD_PATH / "mistakes"
    mistakes_dir.mkdir(parents=True, exist_ok=True)

    ext = file.filename.split(".")[-1] if file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = mistakes_dir / filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "image_path": f"mistakes/{filename}",
        "image_url": f"/uploads/mistakes/{filename}"
    }

def _clean_markdown_json(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r'^```json\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = re.sub(r'^```\s*', '', cleaned)
    cleaned = re.sub(r'\s*```$', '', cleaned)
    cleaned = re.sub(r'^["\']?json["\']?\s*', '', cleaned)
    cleaned = cleaned.strip()
    return cleaned

def _validate_json_schema(data: dict) -> bool:
    required_fields = ["subject", "knowledge_point", "question_text", "answer", "analysis", "difficulty", "error_type"]
    for field in required_fields:
        if field not in data:
            return False
    valid_subjects = ["数学", "英语", "政治", "专业课", ""]
    if data.get("subject") not in valid_subjects:
        return False
    valid_difficulties = ["简单", "中等", "困难", ""]
    if data.get("difficulty") not in valid_difficulties:
        return False
    valid_error_types = ["概念错误", "计算错误", "审题错误", ""]
    if data.get("error_type") not in valid_error_types:
        return False
    return True

@router.post("/recognize", response_model=MistakeRecognizeResponse)
async def recognize_mistake(
    data: MistakeRecognizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    full_path = UPLOAD_PATH / data.image_path
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="图片不存在")

    result = await asyncio.to_thread(ocr_service.recognize, str(full_path))
    
    question_text = result.get("question_text", "")
    
    if not question_text:
        result["answer"] = None
        result["analysis"] = "图片中未识别到题目内容"
        result["confidence"] = 0.0
        return result
    
    try:
        from ..services.ai_service import ai_service
        
        prompt = f"""你是一个专业的考研题目分析助手。请分析以下题目内容，提取并生成以下信息：

题目内容：
{question_text}

请严格按照以下JSON格式输出，不要包含任何额外内容：
{{
  "subject": "科目名称（只能是：数学/英语/政治/专业课）",
  "knowledge_point": "知识点名称（如：高等数学-极限、线性代数-矩阵等）",
  "question_text": "题目完整描述",
  "answer": "正确答案（数学公式使用LaTeX格式，行内公式用$...$包裹，独立公式用$$...$$包裹）",
  "analysis": "详细解析过程，包含解题步骤和公式（数学公式使用LaTeX格式）",
  "difficulty": "难度等级（只能是：简单/中等/困难）",
  "error_type": "错误类型（只能是：概念错误/计算错误/审题错误）"
}}

要求：
1. 如果无法识别为考研题目，所有字段返回空字符串""
2. 答案和解析中的数学公式必须使用标准LaTeX格式
3. 输出必须是合法的JSON格式，不能包含markdown代码块标记或任何解释文字
4. 字段值必须严格匹配给定的选项范围，不要使用其他词汇
"""
        
        max_retries = 2
        ai_data = None
        last_error = ""
        
        for attempt in range(max_retries + 1):
            try:
                ai_result = ai_service.chat(db, current_user.id, prompt)
                answer_text = ai_result.get("answer", "")
                
                print(f"[AI识别] AI原始返回: {repr(answer_text[:500])}...")
                
                cleaned_text = _clean_markdown_json(answer_text)
                
                json_match = re.search(r'\{[\s\S]*\}', cleaned_text)
                if not json_match:
                    raise ValueError("未找到JSON内容")
                
                ai_data = json.loads(json_match.group(0))
                
                if not _validate_json_schema(ai_data):
                    raise ValueError("JSON schema验证失败")
                
                break
            except json.JSONDecodeError as e:
                last_error = f"JSON解析错误: {str(e)}"
                print(f"[AI识别] 第{attempt+1}次尝试失败: {last_error}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
            except ValueError as e:
                last_error = str(e)
                print(f"[AI识别] 第{attempt+1}次尝试失败: {last_error}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
            except Exception as e:
                last_error = f"未知错误: {str(e)}"
                print(f"[AI识别] 第{attempt+1}次尝试失败: {last_error}")
                if attempt < max_retries:
                    await asyncio.sleep(1)
        
        if ai_data and _validate_json_schema(ai_data):
            result["subject"] = ai_data.get("subject", result.get("subject", ""))
            result["knowledge_point"] = ai_data.get("knowledge_point", result.get("knowledge_point", ""))
            result["question_text"] = ai_data.get("question_text", question_text)
            result["answer"] = ai_data.get("answer", "")
            result["analysis"] = ai_data.get("analysis", "")
            result["difficulty"] = ai_data.get("difficulty", "")
            result["error_type"] = ai_data.get("error_type", "")
            result["confidence"] = 1.0
        else:
            result["answer"] = None
            result["analysis"] = f"AI返回的内容格式不正确，已重试{max_retries}次，请重新尝试。错误信息: {last_error}"
            result["confidence"] = 0.3
    except Exception as e:
        print(f"[AI] 识别失败: {e}")
        result["answer"] = None
        result["analysis"] = "AI识别服务暂时不可用，请稍后重试"
        result["confidence"] = 0.0
    
    return result

@router.get("/review/today", response_model=list[MistakeResponse])
async def get_today_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistakes = mistake_service.get_today_reviews(db, current_user.id)
    return mistakes

@router.get("/{mistake_id}", response_model=MistakeResponse)
async def get_mistake(
    mistake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistake = mistake_service.get_mistake_by_id(db, current_user.id, mistake_id)
    if not mistake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return mistake

@router.get("/{mistake_id}/similar", response_model=list[SimilarMistakeResponse])
async def get_similar_mistakes(
    mistake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = mistake_service.get_similar_mistakes(db, current_user.id, mistake_id)
    return [
        SimilarMistakeResponse(
            id=item["mistake"].id,
            subject=item["mistake"].subject,
            knowledge_point=item["mistake"].knowledge_point,
            question_text=item["mistake"].question_text,
            difficulty=item["mistake"].difficulty,
            mastery_level=item["mistake"].mastery_level,
            similarity_score=item["similarity_score"]
        )
        for item in results
    ]

@router.put("/{mistake_id}", response_model=MistakeResponse)
async def update_mistake(
    mistake_id: int,
    data: MistakeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    mistake = mistake_service.update_mistake(db, current_user.id, mistake_id, data)
    if not mistake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return mistake

@router.delete("/{mistake_id}")
async def delete_mistake(
    mistake_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    success = mistake_service.delete_mistake(db, current_user.id, mistake_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="错题不存在")
    return {"message": "删除成功"}

@router.post("/{mistake_id}/review", response_model=MistakeReviewResponse)
async def review_mistake(
    mistake_id: int,
    data: MistakeReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        review = mistake_service.review_mistake(db, current_user.id, mistake_id, data)
        return review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
