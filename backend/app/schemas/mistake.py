from typing import Optional
from pydantic import BaseModel, Field

class MistakeCreate(BaseModel):
    subject: str = Field(..., description="科目（数学/英语/政治/专业课）")
    knowledge_point: str = Field(..., description="知识点")
    error_type: str = Field(..., description="错误类型（概念错误/计算错误/审题错误）")
    difficulty: str = Field(..., description="难度（简单/中等/困难）")
    question_text: str = Field(..., description="题目文本")
    answer: str = Field(..., description="正确答案")
    analysis: Optional[str] = Field(None, description="解析")
    error_reason: Optional[str] = Field(None, description="错误原因")

class MistakeUpdate(BaseModel):
    subject: Optional[str] = None
    knowledge_point: Optional[str] = None
    error_type: Optional[str] = None
    difficulty: Optional[str] = None
    question_text: Optional[str] = None
    answer: Optional[str] = None
    analysis: Optional[str] = None
    error_reason: Optional[str] = None

class MistakeResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    knowledge_point: str
    error_type: str
    difficulty: str
    mastery_level: str
    question_text: str
    answer: str
    analysis: Optional[str]
    error_reason: Optional[str]
    next_review_date: Optional[str]
    review_count: int
    correct_count: int
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

class MistakeReviewCreate(BaseModel):
    result: str = Field(..., description="结果（正确/错误/部分正确）")
    notes: Optional[str] = None

class MistakeReviewResponse(BaseModel):
    id: int
    mistake_id: int
    user_id: int
    result: str
    review_date: str
    notes: Optional[str]

    class Config:
        from_attributes = True