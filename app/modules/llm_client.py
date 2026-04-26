"""
llama-cpp-python LLM client (Ollama 대체).
로컬 GGUF 파일을 로드하고 Ollama와 동일한 인터페이스를 제공합니다.

Tool calling은 llama-cpp-python에 맡기지 않고, Qwen3 네이티브 형식
(<tool_call>JSON</tool_call>)으로 시스템 프롬프트에 주입한 뒤 직접 파싱합니다.
"""

import os
import asyncio
import json
import re
import threading
from typing import Optional

LLM_MODEL_PATH = os.path.expanduser(os.getenv("LLM_MODEL_PATH", "~/qwen3.6-35b-a3b-ud-q3_k_xl.gguf"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "16384"))
LLM_N_THREADS = int(os.getenv("LLM_N_THREADS", str(os.cpu_count() or 4)))
LLM_N_GPU_LAYERS = int(os.getenv("LLM_N_GPU_LAYERS", "0"))

_CTX_STEPS = [8192, 16384, 32768, 65536, 131072]

_llm = None
_lock = threading.Lock()

# Qwen3 네이티브 tool calling 형식으로 시스템 프롬프트에 주입
_TOOL_SECTION = """\

# Tools

You have access to the following tools. You MUST use them to take actions.
CRITICAL RULES:
- NEVER just describe what you plan to do. ALWAYS call the tool immediately.
- Only stop calling tools when the task is fully and completely finished.
- After each tool result, decide your next action and call the next tool right away.

<tools>
{tools_json}
</tools>

To call a tool, output EXACTLY this format (valid JSON inside the tags):
<tool_call>
{{"name": "tool_name", "arguments": {{"key": "value"}}}}
</tool_call>"""


def load_model():
    global _llm
    if _llm is not None:
        return _llm
    from llama_cpp import Llama
    print(f"[LLM] Loading {LLM_MODEL_PATH} (n_ctx={LLM_NUM_CTX}, threads={LLM_N_THREADS})...")
    _llm = Llama(
        model_path=LLM_MODEL_PATH,
        n_ctx=LLM_NUM_CTX,
        n_threads=LLM_N_THREADS,
        n_gpu_layers=LLM_N_GPU_LAYERS,
        verbose=False,
    )
    print("[LLM] Model ready.")
    return _llm


def _expand_ctx() -> bool:
    """n_ctx를 다음 단계로 늘리고 모델을 재로드합니다. _lock 내부에서만 호출. 확장 불가면 False 반환."""
    global _llm, LLM_NUM_CTX
    next_ctx = next((s for s in _CTX_STEPS if s > LLM_NUM_CTX), None)
    if next_ctx is None:
        return False
    old = LLM_NUM_CTX
    LLM_NUM_CTX = next_ctx
    print(f"[LLM] Context overflow → 자동 확장: {old} → {LLM_NUM_CTX}")
    _llm = None
    load_model()
    return True


def _trim_messages(msgs: list) -> list:
    """오래된 메시지를 제거해 컨텍스트를 줄입니다. 시스템 메시지는 항상 보존."""
    start = 1 if msgs and msgs[0]["role"] == "system" else 0
    body = msgs[start:]
    if len(body) <= 2:
        raise RuntimeError("컨텍스트가 꽉 찼고 더 이상 메시지를 줄일 수 없습니다.")
    drop = max(2, len(body) // 4)
    trimmed = msgs[:start] + body[drop:]
    print(f"[LLM] 최대 컨텍스트 도달 → 오래된 메시지 {drop}개 제거 ({len(msgs)} → {len(trimmed)}개)")
    return trimmed


def _inject_tools(messages: list, tools: list) -> list:
    """시스템 메시지에 tool 정의를 Qwen3 형식으로 추가합니다."""
    section = _TOOL_SECTION.format(
        tools_json=json.dumps(tools, ensure_ascii=False, indent=2)
    )
    result = list(messages)
    for i, msg in enumerate(result):
        if msg["role"] == "system":
            result[i] = {**msg, "content": msg["content"] + section}
            return result
    # 시스템 메시지가 없으면 맨 앞에 추가
    return [{"role": "system", "content": section.lstrip()}] + result


_TOOL_CALL_RE = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)


def _extract_tool_calls(content: str) -> tuple[str, list]:
    """content에서 <tool_call>JSON</tool_call> 블록을 파싱합니다."""
    tool_calls = []
    for match in _TOOL_CALL_RE.finditer(content):
        try:
            data = json.loads(match.group(1).strip())
            name = data.get("name", "")
            args = data.get("arguments") or {}
            if name:
                tool_calls.append(_ToolCall(name, args))
        except (json.JSONDecodeError, AttributeError):
            pass
    clean = _TOOL_CALL_RE.sub("", content).strip()
    return clean, tool_calls


# ── Ollama 호환 응답 래퍼 ──

class _ToolFunction:
    __slots__ = ("name", "arguments")

    def __init__(self, name: str, arguments: dict):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    __slots__ = ("function",)

    def __init__(self, name: str, arguments: dict):
        self.function = _ToolFunction(name, arguments)


class _Message:
    __slots__ = ("content", "tool_calls")

    def __init__(self, content: str, tool_calls: Optional[list]):
        self.content = content
        self.tool_calls = tool_calls


class ChatResponse:
    __slots__ = ("message",)

    def __init__(self, message: _Message):
        self.message = message


def _parse_response(raw: dict, had_tools: bool) -> ChatResponse:
    msg = raw["choices"][0]["message"]
    content: str = msg.get("content") or ""

    # llama-cpp가 tool_calls를 파싱했으면 그대로 사용
    raw_tcs = msg.get("tool_calls") or []
    if raw_tcs:
        tool_calls = []
        for tc in raw_tcs:
            name = tc["function"]["name"]
            args_raw = tc["function"]["arguments"]
            args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
            tool_calls.append(_ToolCall(name, args))
        return ChatResponse(_Message(content, tool_calls))

    # fallback: content에서 <tool_call> 블록 직접 파싱
    if had_tools:
        content, tool_calls = _extract_tool_calls(content)
        if tool_calls:
            return ChatResponse(_Message(content, tool_calls))

    return ChatResponse(_Message(content, None))


def _do_inference(messages: list, tools: Optional[list]) -> tuple[dict, bool]:
    with _lock:
        load_model()
        msgs = _inject_tools(messages, tools) if tools else messages
        while True:
            try:
                raw = _llm.create_chat_completion(messages=msgs)
                return raw, bool(tools)
            except ValueError as e:
                if "exceed context window" not in str(e):
                    raise
                if not _expand_ctx():
                    msgs = _trim_messages(msgs)  # 최대 크기 도달 시 오래된 메시지 제거


def chat_sync(messages: list, tools: Optional[list] = None) -> ChatResponse:
    """동기 호출 (APScheduler 백그라운드 스레드용)."""
    raw, had_tools = _do_inference(messages, tools)
    return _parse_response(raw, had_tools)


async def chat(messages: list, tools: Optional[list] = None) -> ChatResponse:
    """비동기 호출 (FastAPI 엔드포인트용)."""
    loop = asyncio.get_running_loop()
    raw, had_tools = await loop.run_in_executor(None, _do_inference, messages, tools)
    return _parse_response(raw, had_tools)
