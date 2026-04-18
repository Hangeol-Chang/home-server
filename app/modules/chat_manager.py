import os
import anthropic
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from models.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    MessageRole
)
from modules.workspace_tools import execute_tool_call, WORKSPACE_PATH

# 라우터 생성
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}}
)

# ===== 모델 설정 =====
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

MAX_TOOL_ITERATIONS = 10

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful home server assistant running on a Raspberry Pi. "
    "You have access to the user's workspace filesystem via tools. "
    "When the user asks about files or code, use the tools to explore and read them. "
    "When asked to modify files, use write_file after reading the original content first. "
    "Always answer in the same language the user uses."
)

# ===== Claude Tool Schema =====
# Anthropic API 형식: input_schema 사용 (OpenAI의 parameters와 다름)
CLAUDE_TOOLS = [
    {
        "name": "list_directory",
        "description": "워크스페이스 내 디렉토리 목록을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "조회할 상대 경로 (예: 'home-server/app'). 기본값: 루트"
                }
            },
            "required": []
        }
    },
    {
        "name": "read_file",
        "description": "워크스페이스 내 파일의 내용을 읽습니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "읽을 파일의 상대 경로 (예: 'home-server/app/main.py')"
                }
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "워크스페이스 내 파일에 내용을 씁니다. 파일이 없으면 생성하고, 있으면 전체를 덮어씁니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "쓸 파일의 상대 경로"
                },
                "content": {
                    "type": "string",
                    "description": "파일에 쓸 전체 내용"
                }
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "find_files",
        "description": "glob 패턴으로 파일을 검색합니다. 예) pattern='**/*.py' 로 모든 파이썬 파일 검색",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "glob 패턴 (예: '**/*.py', '*.md')"
                },
                "directory": {
                    "type": "string",
                    "description": "검색 시작 디렉토리 상대 경로. 기본값: 루트"
                }
            },
            "required": ["pattern"]
        }
    }
]

# ===== Claude 로직 =====

def build_claude_messages(history: List[ChatMessage], message: str) -> List[Dict[str, Any]]:
    """Anthropic API에 전달할 messages 구조체를 구성 (system은 별도 파라미터로 전달)"""
    messages = []
    for msg in history:
        messages.append({
            "role": "user" if msg.role == MessageRole.user else "assistant",
            "content": msg.content
        })
    messages.append({"role": "user", "content": message})
    return messages


def call_claude(messages: List[Dict[str, Any]], system_prompt: str) -> str:
    """Anthropic API 호출 + Tool 실행 Agentic Loop"""
    if not ANTHROPIC_API_KEY:
        raise Exception("ANTHROPIC_API_KEY가 설정되지 않았습니다. app/env/.env 파일을 확인하세요.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    messages_copy = [m.copy() for m in messages]

    for iteration in range(MAX_TOOL_ITERATIONS):
        print(f"[Claude] iteration={iteration}, model={CLAUDE_MODEL}, messages={len(messages_copy)}")

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=messages_copy,
            tools=CLAUDE_TOOLS
        )

        # 최종 응답 (tool 호출 없음)
        if response.stop_reason == "end_turn":
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(text_blocks)

        # Tool 호출 처리
        if response.stop_reason == "tool_use":
            # 1. assistant 메시지(tool_use 블록 포함) 누적
            messages_copy.append({
                "role": "assistant",
                "content": [b.model_dump() for b in response.content]
            })

            # 2. 각 tool 실행 후 tool_result 메시지 누적
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[workspace] Claude tool call: {block.name}({block.input})")
                    result = execute_tool_call(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": str(result)
                    })

            messages_copy.append({"role": "user", "content": tool_results})
            continue

        # 예상치 못한 stop_reason
        text_blocks = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(text_blocks) if text_blocks else ""

    return "무한 루프 방지: 최대 도구 실행 횟수(10회)에 도달했습니다."


# ===== API Endpoints =====

@router.post("/message", response_model=ChatResponse)
def send_message(request: ChatRequest):
    """Claude API로 메시지 전송"""
    system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT

    try:
        messages = build_claude_messages(request.history, request.message)
        reply_text = call_claude(messages, system_prompt)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API 요청 실패: {str(e)}"
        )

    return ChatResponse(
        message=reply_text,
        model=CLAUDE_MODEL
    )


@router.get("/health")
def chat_health():
    """Chat 모듈 상태 확인"""
    return {
        "status": "ok",
        "provider": "claude",
        "model": CLAUDE_MODEL,
        "api_key_set": bool(ANTHROPIC_API_KEY),
        "workspace_path": str(WORKSPACE_PATH),
    }
