from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ===== Role (메시지 역할) =====
class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


# ===== Chat Message (단일 메시지) =====
class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="메시지 역할 (user / assistant)")
    content: str = Field(..., description="메시지 내용")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="메시지 시각")


# ===== Chat Request (프론트 → 백엔드) =====
class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    history: Optional[List[ChatMessage]] = Field(
        default_factory=list,
        description="이전 대화 히스토리 (멀티턴 지원)"
    )
    system_prompt: Optional[str] = Field(
        None,
        description="시스템 프롬프트 (없으면 기본값 사용)"
    )


# ===== Chat Response (백엔드 → 프론트) =====
class ChatResponse(BaseModel):
    message: str = Field(..., description="Gemini 응답 내용")
    role: MessageRole = Field(default=MessageRole.assistant, description="응답 역할")
    timestamp: datetime = Field(default_factory=datetime.now, description="응답 시각")
    model: Optional[str] = Field(None, description="사용된 Gemini 모델명")


# ===== Chat Error Response =====
class ChatErrorResponse(BaseModel):
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
