"""
llama-cpp-python LLM client (Ollama 대체).
로컬 GGUF 파일을 로드하고 Ollama와 동일한 인터페이스를 제공합니다.

Tool calling은 GGUF에 내장된 Jinja 채팅 템플릿(Gemma4 네이티브 포맷)에
그대로 맡깁니다. 단, llama-cpp-python은 이 템플릿의 tool_call 출력을
구조화된 tool_calls로 파싱해주지 않으므로, 모델이 생성한 원문에서
`<|tool_call>call:NAME{...}<tool_call|>` 블록을 직접 파싱합니다.
"""

import os
import asyncio
import re
import threading
from typing import Optional

LLM_MODEL_PATH = os.path.expanduser(os.getenv(
    "LLM_MODEL_PATH",
    "/usr/share/ollama/.ollama/models/blobs/sha256-1278394b693672ac2799eadc9a83fd98259a6a88a40acfb1dcaa6c6fc895a606",
))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "16384"))
LLM_N_THREADS = int(os.getenv("LLM_N_THREADS", str(os.cpu_count() or 4)))
LLM_N_GPU_LAYERS = int(os.getenv("LLM_N_GPU_LAYERS", "0"))

_CTX_STEPS = [8192, 16384, 32768, 65536, 131072]

# 모델이 tool_call 이후 가짜 tool_response/다음 turn을 스스로 이어 생성(반복 환각)하는 것을 막는다.
_STOP_SEQUENCES = ["<|tool_response>", "<|turn>"]

_llm = None
_lock = threading.Lock()


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


# ── Gemma4 네이티브 tool_call 파싱 ──
#
# 채팅 템플릿이 인자를 표준 JSON이 아니라 자체 포맷으로 직렬화한다:
#   call:NAME{key:<|"|>string_value<|"|>,key2:123,key3:[1,2],key4:{...}}
# 문자열은 " 대신 <|"|> 로 감싸고, 키는 따옴표 없이 그대로 노출된다.

_STR_DELIM = '<|"|>'
_TOOL_CALL_START_RE = re.compile(r'<\|tool_call>call:([A-Za-z0-9_]+)')
_TOOL_CALL_END = '<tool_call|>'


def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i] in ' \t\n\r':
        i += 1
    return i


def _parse_gemma_string(s: str, i: int) -> tuple[str, int]:
    i += len(_STR_DELIM)
    end = s.index(_STR_DELIM, i)
    return s[i:end], end + len(_STR_DELIM)


def _parse_gemma_value(s: str, i: int):
    i = _skip_ws(s, i)
    if s.startswith(_STR_DELIM, i):
        return _parse_gemma_string(s, i)
    if s.startswith('true', i):
        return True, i + 4
    if s.startswith('false', i):
        return False, i + 5
    if s[i] == '[':
        return _parse_gemma_array(s, i)
    if s[i] == '{':
        return _parse_gemma_object(s, i)
    j = i
    while j < len(s) and s[j] not in ',}]':
        j += 1
    token = s[i:j].strip()
    try:
        return int(token), j
    except ValueError:
        pass
    try:
        return float(token), j
    except ValueError:
        return token, j


def _parse_gemma_array(s: str, i: int) -> tuple[list, int]:
    i = _skip_ws(s, i + 1)
    arr = []
    if s[i] == ']':
        return arr, i + 1
    while True:
        val, i = _parse_gemma_value(s, i)
        arr.append(val)
        i = _skip_ws(s, i)
        if s[i] == ',':
            i = _skip_ws(s, i + 1)
            continue
        break
    return arr, i + 1


def _parse_gemma_object(s: str, i: int) -> tuple[dict, int]:
    i = _skip_ws(s, i + 1)
    obj = {}
    if s[i] == '}':
        return obj, i + 1
    while True:
        i = _skip_ws(s, i)
        colon = s.index(':', i)
        key = s[i:colon].strip()
        val, i = _parse_gemma_value(s, colon + 1)
        obj[key] = val
        i = _skip_ws(s, i)
        if i < len(s) and s[i] == ',':
            i = _skip_ws(s, i + 1)
            continue
        break
    return obj, i + 1


def _extract_tool_calls(content: str) -> tuple[str, list]:
    """content에서 <|tool_call>call:NAME{...}<tool_call|> 블록을 파싱합니다."""
    tool_calls = []
    parts = []
    cursor = 0
    while True:
        m = _TOOL_CALL_START_RE.search(content, cursor)
        if not m:
            parts.append(content[cursor:])
            break
        parts.append(content[cursor:m.start()])
        name = m.group(1)
        try:
            args, after = _parse_gemma_object(content, m.end())
            end = content.index(_TOOL_CALL_END, after)
        except (ValueError, IndexError):
            # 파싱 실패 시 이 블록은 건너뛰고 원문 그대로 남긴다
            parts.append(content[m.start():m.end()])
            cursor = m.end()
            continue
        tool_calls.append(_ToolCall(name, args))
        cursor = end + len(_TOOL_CALL_END)
    clean = "".join(parts).strip()
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

    # llama-cpp가 tool_calls를 직접 파싱해주는 chat_format이면 그대로 사용
    raw_tcs = msg.get("tool_calls") or []
    if raw_tcs:
        import json
        tool_calls = []
        for tc in raw_tcs:
            name = tc["function"]["name"]
            args_raw = tc["function"]["arguments"]
            args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
            tool_calls.append(_ToolCall(name, args))
        return ChatResponse(_Message(content, tool_calls))

    # gemma4 네이티브 포맷: content 안의 <|tool_call>...<tool_call|> 직접 파싱
    if had_tools:
        content, tool_calls = _extract_tool_calls(content)
        if tool_calls:
            return ChatResponse(_Message(content, tool_calls))

    return ChatResponse(_Message(content, None))


def _do_inference(messages: list, tools: Optional[list]) -> tuple[dict, bool]:
    with _lock:
        load_model()
        # 출력 토큰을 컨텍스트의 절반까지 보장 (최소 4096)
        max_tokens = max(4096, LLM_NUM_CTX // 2)
        while True:
            try:
                raw = _llm.create_chat_completion(
                    messages=messages, tools=tools, max_tokens=max_tokens, stop=_STOP_SEQUENCES
                )
                return raw, bool(tools)
            except ValueError as e:
                if "exceed context window" not in str(e):
                    raise
                if not _expand_ctx():
                    messages = _trim_messages(messages)
                max_tokens = max(4096, LLM_NUM_CTX // 2)  # 컨텍스트 확장 시 재계산


def chat_sync(messages: list, tools: Optional[list] = None) -> ChatResponse:
    """동기 호출 (APScheduler 백그라운드 스레드용)."""
    raw, had_tools = _do_inference(messages, tools)
    return _parse_response(raw, had_tools)


async def chat(messages: list, tools: Optional[list] = None) -> ChatResponse:
    """비동기 호출 (FastAPI 엔드포인트용)."""
    loop = asyncio.get_running_loop()
    raw, had_tools = await loop.run_in_executor(None, _do_inference, messages, tools)
    return _parse_response(raw, had_tools)
