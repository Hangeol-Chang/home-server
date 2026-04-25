"""
llama-cpp-python LLM client (Ollama 대체).
로컬 GGUF 파일을 로드하고 Ollama와 동일한 인터페이스를 제공합니다.
"""

import os
import asyncio
import json
import threading
from typing import Optional

LLM_MODEL_PATH = os.path.expanduser(os.getenv("LLM_MODEL_PATH", "~/qwen3.6-35b-a3b-ud-q3_k_xl.gguf"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "16384"))
LLM_N_THREADS = int(os.getenv("LLM_N_THREADS", str(os.cpu_count() or 4)))
LLM_N_GPU_LAYERS = int(os.getenv("LLM_N_GPU_LAYERS", "0"))

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


def _parse_response(raw: dict) -> ChatResponse:
    msg = raw["choices"][0]["message"]
    content: str = msg.get("content") or ""
    tool_calls = []
    for tc in msg.get("tool_calls") or []:
        name = tc["function"]["name"]
        args_raw = tc["function"]["arguments"]
        if isinstance(args_raw, str):
            try:
                args = json.loads(args_raw)
            except json.JSONDecodeError:
                args = {}
        else:
            args = args_raw or {}
        tool_calls.append(_ToolCall(name, args))
    return ChatResponse(_Message(content, tool_calls or None))


def _do_inference(messages: list, tools: Optional[list]) -> dict:
    with _lock:
        llm = load_model()
        kwargs: dict = {"messages": messages}
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        return llm.create_chat_completion(**kwargs)


def chat_sync(messages: list, tools: Optional[list] = None) -> ChatResponse:
    """동기 호출 (APScheduler 백그라운드 스레드용)."""
    return _parse_response(_do_inference(messages, tools))


async def chat(messages: list, tools: Optional[list] = None) -> ChatResponse:
    """비동기 호출 (FastAPI 엔드포인트용)."""
    loop = asyncio.get_running_loop()
    raw = await loop.run_in_executor(None, _do_inference, messages, tools)
    return _parse_response(raw)
