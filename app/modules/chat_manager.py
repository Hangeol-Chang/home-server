import os
import re
import json
from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Dict, Any

from models.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    MessageRole,
    AgentStartRequest,
    AgentStatusResponse,
    AgentSessionSummary,
    AgentSessionDetail,
)
from modules.workspace_tools import execute_tool_call, WORKSPACE_PATH
from modules.agent_loop import agent_loop, TOOLS, AgentStatus
from modules.llm_client import chat as llm_chat, LLM_MODEL_PATH, LLM_NUM_CTX
import modules.agent_sessions as sessions

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={404: {"description": "Not found"}},
)

MAX_TOOL_ITERATIONS = 10

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful home server assistant. "
    "You have access to the user's workspace filesystem via tools. "
    "When the user asks about files or code, use the tools to explore and read them. "
    "When asked to modify files, use write_file after reading the original content first. "
    "Always answer in the same language the user uses."
)


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _truncate_history(messages: List[Dict[str, Any]], max_ctx: int) -> List[Dict[str, Any]]:
    # 한국어/영어 혼합 기준 3자 ≈ 1 토큰으로 추정
    budget = max_ctx * 3
    result = []
    used = 0
    for msg in reversed(messages):
        size = len(msg.get("content") or "")
        if used + size > budget and result:
            break
        result.insert(0, msg)
        used += size
    return result


def _build_messages(history: List[ChatMessage], message: str) -> List[Dict[str, Any]]:
    messages = []
    for msg in history:
        role = "user" if msg.role == MessageRole.user else "assistant"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": message})
    return messages


async def _call_llm(messages: List[Dict[str, Any]], system_prompt: str, max_ctx: int = None) -> str:
    if max_ctx:
        messages = _truncate_history(messages, max_ctx)
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    for iteration in range(MAX_TOOL_ITERATIONS):
        print(f"[Chat] iter={iteration} msgs={len(full_messages)}")

        response = await llm_chat(full_messages, tools=TOOLS)
        msg = response.message
        raw_content: str = msg.content or ""
        tool_calls = msg.tool_calls or []

        if not tool_calls:
            return _strip_thinking(raw_content)

        full_messages.append({"role": "assistant", "content": raw_content})

        for tc in tool_calls:
            fn_name = tc.function.name
            fn_args = tc.function.arguments or {}
            print(f"[Chat][tool] {fn_name}({fn_args})")
            result = execute_tool_call(fn_name, fn_args)
            full_messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})

    return "최대 도구 실행 횟수(10회)에 도달했습니다."


# ===== Regular chat =====

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    system_prompt = request.system_prompt or DEFAULT_SYSTEM_PROMPT
    try:
        messages = _build_messages(request.history or [], request.message)
        reply = await _call_llm(messages, system_prompt, max_ctx=request.max_ctx)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM 요청 실패: {exc}",
        )
    return ChatResponse(message=reply, model=os.path.basename(LLM_MODEL_PATH))


# ===== Agent loop control =====

@router.post("/agent/start", response_model=AgentStatusResponse)
async def agent_start(request: AgentStartRequest):
    try:
        agent_loop.start(
            objective=request.objective,
            system_prompt=request.system_prompt or DEFAULT_SYSTEM_PROMPT,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return AgentStatusResponse(**agent_loop.get_status())


@router.post("/agent/stop", response_model=AgentStatusResponse)
async def agent_stop():
    agent_loop.stop()
    return AgentStatusResponse(**agent_loop.get_status())


@router.get("/agent/status", response_model=AgentStatusResponse)
async def agent_status(log_tail: int = Query(default=30, ge=1, le=200)):
    return AgentStatusResponse(**agent_loop.get_status(log_tail=log_tail))


@router.delete("/agent/logs")
async def agent_clear_logs():
    agent_loop.clear_logs()
    return {"ok": True}


# ===== Agent sessions =====

@router.get("/agent/sessions", response_model=list[AgentSessionSummary])
async def list_sessions():
    return sessions.list_all()


@router.get("/agent/sessions/{session_id}", response_model=AgentSessionDetail)
async def get_session(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return s


@router.post("/agent/sessions/{session_id}/resume", response_model=AgentStatusResponse)
async def resume_session(session_id: str):
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    try:
        agent_loop.start(
            objective=s["objective"],
            system_prompt=s["system_prompt"] or DEFAULT_SYSTEM_PROMPT,
            initial_messages=s["messages"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return AgentStatusResponse(**agent_loop.get_status())


@router.delete("/agent/sessions/{session_id}")
async def delete_session(session_id: str):
    if not sessions.delete(session_id):
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    return {"ok": True}


# ===== Health =====

@router.get("/health")
async def chat_health():
    return {
        "status": "ok",
        "provider": "llama-cpp-python",
        "model": os.path.basename(LLM_MODEL_PATH),
        "model_path": LLM_MODEL_PATH,
        "num_ctx": LLM_NUM_CTX,
        "workspace_path": str(WORKSPACE_PATH),
        "agent_status": agent_loop.status,
    }
