from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="메시지 역할 (user / assistant)")
    content: str = Field(..., description="메시지 내용")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 메시지")
    history: Optional[List[ChatMessage]] = Field(default_factory=list)
    system_prompt: Optional[str] = Field(None, description="시스템 프롬프트 (없으면 기본값)")
    max_ctx: Optional[int] = Field(None, description="히스토리 제한에 사용할 컨텍스트 토큰 수")


class ChatResponse(BaseModel):
    message: str = Field(..., description="모델 응답 내용")
    role: MessageRole = Field(default=MessageRole.assistant)
    timestamp: datetime = Field(default_factory=datetime.now)
    model: Optional[str] = Field(None, description="사용된 모델명")


class ChatErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None


# ===== Agent loop models =====

class AgentStartRequest(BaseModel):
    objective: str = Field(..., description="에이전트에게 줄 목표/임무")
    system_prompt: Optional[str] = Field(None, description="시스템 프롬프트 (없으면 기본값)")
    model: Optional[str] = Field(None, description="사용할 Ollama 모델 (없으면 OLLAMA_MODEL_CHAT)")


class AgentLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
    iteration: int


class AgentStatusResponse(BaseModel):
    status: str
    current_objective: Optional[str] = None
    iteration: int = 0
    error: Optional[str] = None
    session_id: Optional[str] = None
    summary: Optional[str] = None
    logs: List[Any] = Field(default_factory=list)
    total_logs: int = 0


class AgentSessionSummary(BaseModel):
    id: str
    objective: str
    status: str
    iteration: int = 0
    error: Optional[str] = None
    started_at: str
    finished_at: Optional[str] = None
    summary: Optional[str] = None


class AgentSessionDetail(AgentSessionSummary):
    system_prompt: Optional[str] = None
    logs: List[Any] = Field(default_factory=list)
    messages: List[Any] = Field(default_factory=list)
