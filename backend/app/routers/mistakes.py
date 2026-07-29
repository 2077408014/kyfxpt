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
        from ..services.feature_agent_service import feature_agent_service

        prompt = f"""分析以下OCR识别出的考研题目，用自然语言组织输出：

题目内容：
{question_text}

请按以下格式输出（不要JSON，不要markdown代码块，直接用自然语言）：

## 题目
[题目完整描述]

## 答案
[正确答案]

## 解析
[详细解题步骤和思路]

## 题目信息
- 科目：[数学/英语/政治/专业课]
- 知识点：[知识点名称]
- 难度：[简单/中等/困难]
- 错误类型：[概念错误/计算错误/审题错误]
"""
        
        ai_result = feature_agent_service.chat(
            db=db,
            user_id=current_user.id,
            agent_name='mistake-recognition',
            message=prompt,
        )
        ai_answer = ai_result.get("answer", "")
        
        if ai_answer:
            result["question_text"] = question_text
            result["answer"] = ai_answer
            result["analysis"] = ai_answer
            result["confidence"] = 0.9
        else:
            result["answer"] = None
            result["analysis"] = "AI分析失败，请重试"
            result["confidence"] = 0.3
    except Exception as e:
        print(f"[AI识别] 错误: {e}")
        import traceback
        traceback.print_exc()
        result["answer"] = None
        result["analysis"] = f"AI分析出错: {str(e)}"
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
