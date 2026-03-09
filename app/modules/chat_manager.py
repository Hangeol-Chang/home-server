import os
from fastapi import APIRouter, HTTPException, status
from typing import List
from google import genai
from google.genai import types
from models.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    MessageRole
)
from modules.workspace_tools import WORKSPACE_TOOL, execute_tool_call, WORKSPACE_PATH

# 라우터 생성
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}}
)

# ===== Gemini 클라이언트 초기화 =====
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_PRIMARY  = os.getenv("GEMINI_MODEL_PRIMARY",  "gemini-3.1-flash-preview")
GEMINI_MODEL_FALLBACK = os.getenv("GEMINI_MODEL_FALLBACK", "gemini-2.5-flash-lite")

MAX_TOOL_ITERATIONS = 10  # 무한 루프 방지

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful home server assistant running on a Raspberry Pi. "
    "You have access to the user's workspace filesystem via tools. "
    "When the user asks about files or code, use the tools to explore and read them. "
    "When asked to modify files, use write_file after reading the original content first. "
    "Always answer in the same language the user uses."
)


def get_client() -> genai.Client:
    """Gemini 클라이언트 반환"""
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GEMINI_API_KEY가 설정되어 있지 않습니다."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


def is_quota_exceeded(e: Exception) -> bool:
    """429 RESOURCE_EXHAUSTED 에러인지 확인"""
    msg = str(e)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def build_gemini_history(history: List[ChatMessage]) -> list:
    """ChatMessage 리스트를 google.genai Contents 형식으로 변환"""
    return [
        types.Content(
            role="user" if msg.role == MessageRole.user else "model",
            parts=[types.Part(text=msg.content)]
        )
        for msg in history
    ]


def call_gemini(client: genai.Client, model: str, request: ChatRequest, system_prompt: str) -> str:
    """
    Gemini API 호출 + tool calling 에이전틱 루프.
    Gemini가 함수 호출을 요청하면 실행 후 결과를 돌려주며,
    최종 텍스트 응답이 나올 때까지 반복합니다.
    """
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[WORKSPACE_TOOL],
    )

    # 초기 contents 구성 (히스토리 + 현재 메시지)
    contents: list = []
    if request.history:
        contents.extend(build_gemini_history(request.history))
    contents.append(
        types.Content(role="user", parts=[types.Part(text=request.message)])
    )

    for iteration in range(MAX_TOOL_ITERATIONS):
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        response_content = candidate.content

        # 함수 호출 파트 추출
        function_call_parts = [
            part for part in response_content.parts
            if part.function_call is not None
        ]

        if not function_call_parts:
            # 더 이상 tool call 없음 → 최종 텍스트 반환
            return response.text

        # 모델 응답(tool call 요청)을 contents에 추가
        contents.append(response_content)

        # 각 함수 호출 실행 후 결과 parts 구성
        result_parts = []
        for part in function_call_parts:
            fc = part.function_call
            args = dict(fc.args) if fc.args else {}
            print(f"[workspace] tool call: {fc.name}({args})")
            result = execute_tool_call(fc.name, args)
            result_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fc.name,
                        response=result,
                    )
                )
            )

        # tool 결과를 user role로 contents에 추가
        contents.append(
            types.Content(role="user", parts=result_parts)
        )

    # max iteration 도달 시 마지막 텍스트 반환
    return response.text or "최대 반복 횟수에 도달했습니다."


# ===== API Endpoints =====

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    사용자 메시지를 Gemini API로 전달하고 응답을 반환합니다.
    - 워크스페이스 파일시스템 도구가 항상 활성화됩니다.
    - PRIMARY 모델로 먼저 시도하고, 429 시 FALLBACK 모델로 재시도합니다.
    """
    system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT

    used_model = GEMINI_MODEL_PRIMARY
    try:
        client = get_client()

        try:
            reply_text = call_gemini(client, GEMINI_MODEL_PRIMARY, request, system_prompt)
        except Exception as primary_err:
            if not is_quota_exceeded(primary_err):
                raise
            print(f"[chat] {GEMINI_MODEL_PRIMARY} 할당량 초과 → {GEMINI_MODEL_FALLBACK} 으로 재시도")
            used_model = GEMINI_MODEL_FALLBACK
            reply_text = call_gemini(client, GEMINI_MODEL_FALLBACK, request, system_prompt)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini API 요청 실패: {str(e)}"
        )

    return ChatResponse(
        message=reply_text,
        model=used_model
    )


@router.get("/health")
async def chat_health():
    """Chat 모듈 상태 확인"""
    return {
        "status": "ok",
        "model_primary": GEMINI_MODEL_PRIMARY,
        "model_fallback": GEMINI_MODEL_FALLBACK,
        "api_key_configured": bool(GEMINI_API_KEY),
        "workspace_path": str(WORKSPACE_PATH),
    }
