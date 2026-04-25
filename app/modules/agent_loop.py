"""
Autonomous agent loop (ReAct: Reason → Act → Observe → Repeat).
"""

import asyncio
import json
import re
from datetime import datetime
from collections import deque
from enum import Enum
from typing import Optional, Any

from modules.workspace_tools import execute_tool_call
from modules.llm_client import chat as llm_chat

MAX_ITERATIONS = 50

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "워크스페이스 내 디렉토리 목록을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "조회할 상대 경로. 기본값: 루트"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "워크스페이스 내 파일의 내용을 읽습니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "읽을 파일의 상대 경로"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "워크스페이스 내 파일에 내용을 씁니다. 없으면 생성, 있으면 덮어씁니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "쓸 파일의 상대 경로"},
                    "content": {"type": "string", "description": "파일에 쓸 전체 내용"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_files",
            "description": "glob 패턴으로 파일을 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "glob 패턴 (예: '**/*.py')"},
                    "directory": {"type": "string", "description": "검색 시작 디렉토리. 기본값: 루트"}
                },
                "required": ["pattern"]
            }
        }
    }
]


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class LogEntry:
    __slots__ = ("timestamp", "level", "message", "iteration")

    def __init__(self, level: str, message: str, iteration: int):
        self.timestamp = datetime.now().isoformat()
        self.level = level
        self.message = message
        self.iteration = iteration

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "iteration": self.iteration,
        }


class AgentLoop:
    def __init__(self):
        self.status = AgentStatus.IDLE
        self._task: Optional[asyncio.Task] = None
        self.current_objective: Optional[str] = None
        self.logs: deque[LogEntry] = deque(maxlen=500)
        self.iteration = 0
        self.error: Optional[str] = None
        self._stop_event = asyncio.Event()

    def _log(self, level: str, message: str):
        entry = LogEntry(level, message, self.iteration)
        self.logs.append(entry)
        print(f"[Agent][{level}][iter={self.iteration}] {message}")

    async def _run(self, objective: str, system_prompt: str):
        self._stop_event.clear()

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": objective})

        self._log("INFO", f"Objective: {objective[:200]}")

        try:
            while not self._stop_event.is_set():
                self.iteration += 1
                if self.iteration > MAX_ITERATIONS:
                    self._log("WARN", f"Max iterations ({MAX_ITERATIONS}) reached, stopping")
                    break

                self._log("INFO", f"Calling model (iter {self.iteration})")

                response = await llm_chat(messages, tools=TOOLS)
                msg = response.message
                raw_content: str = msg.content or ""

                # Strip <think>...</think> blocks (Qwen3 thinking tokens)
                visible_content = raw_content
                if "<think>" in raw_content:
                    think_parts = re.findall(r"<think>(.*?)</think>", raw_content, re.DOTALL)
                    if think_parts:
                        self._log("THINK", think_parts[-1].strip()[:300])
                    visible_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL).strip()

                if visible_content:
                    self._log("MODEL", visible_content[:400])

                tool_calls = msg.tool_calls or []

                if not tool_calls:
                    messages.append({"role": "assistant", "content": raw_content})
                    self._log("INFO", "No tool calls — agent loop complete")
                    break

                messages.append({"role": "assistant", "content": raw_content})

                for tc in tool_calls:
                    fn_name: str = tc.function.name
                    fn_args: dict = tc.function.arguments or {}

                    self._log("TOOL", f"{fn_name}({json.dumps(fn_args, ensure_ascii=False)[:150]})")
                    result = execute_tool_call(fn_name, fn_args)
                    result_str = json.dumps(result, ensure_ascii=False)
                    self._log("RESULT", result_str[:300])

                    messages.append({"role": "tool", "content": result_str})

                await asyncio.sleep(0)  # yield to event loop

        except asyncio.CancelledError:
            self._log("INFO", "Agent loop cancelled")
        except Exception as exc:
            self.status = AgentStatus.ERROR
            self.error = str(exc)
            self._log("ERROR", f"Unhandled exception: {exc}")
            return

        if self.status != AgentStatus.ERROR:
            self.status = AgentStatus.IDLE
        self._log("INFO", "Agent loop finished")

    def start(self, objective: str, system_prompt: str) -> None:
        if self.status == AgentStatus.RUNNING:
            raise ValueError("에이전트 루프가 이미 실행 중입니다.")
        self.status = AgentStatus.RUNNING
        self.current_objective = objective
        self.iteration = 0
        self.error = None
        self._task = asyncio.create_task(self._run(objective, system_prompt))

    def stop(self) -> None:
        if self.status != AgentStatus.RUNNING:
            return
        self.status = AgentStatus.STOPPING
        self._stop_event.set()
        self._log("INFO", "Stop requested by user")

    def get_status(self, log_tail: int = 30) -> dict:
        return {
            "status": self.status,
            "current_objective": self.current_objective,
            "iteration": self.iteration,
            "error": self.error,
            "logs": [e.to_dict() for e in list(self.logs)[-log_tail:]],
            "total_logs": len(self.logs),
        }

    def clear_logs(self) -> None:
        self.logs.clear()
        self._log("INFO", "Logs cleared")


# Singleton shared across the FastAPI process
agent_loop = AgentLoop()
