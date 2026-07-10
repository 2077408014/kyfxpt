from typing import Optional
from pydantic import BaseModel, Field

class WordResponse(BaseModel):
    id: int
    word: str
    phonetic: Optional[str]
    meaning: str
    example_sentence: Optional[str]
    difficulty: int
    frequency: int
    exam_requirement: str

    class Config:
        from_attributes = True

class UserWordResponse(BaseModel):
    id: int
    user_id: int
    word_id: int
    word: str
    mastery_level: str
    next_review_date: Optional[str]
    review_count: int
    correct_count: int
    last_study_date: Optional[str]

    class Config:
        from_attributes = True

class WordStudyRequest(BaseModel):
    word_id: int
    result: str = Field(..., description="学习结果（正确/错误）")

class StudyPlanRequest(BaseModel):
    daily_word_count: int = Field(..., ge=5, le=100, description="每日学习单词数量")