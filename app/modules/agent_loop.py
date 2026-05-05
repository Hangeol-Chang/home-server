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

from modules.workspace_tools import execute_tool_call, get_user_tools_schema
from modules.llm_client import chat as llm_chat
import modules.agent_sessions as sessions

MAX_ITERATIONS = 50

TOOLS = [
    # ── 파일시스템 ──
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "워크스페이스 내 디렉토리 목록을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "조회할 상대 경로. 기본값: 루트"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "워크스페이스 내 파일의 내용을 읽습니다. start_line/end_line으로 범위를 지정할 수 있습니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "읽을 파일의 상대 경로"},
                    "start_line": {"type": "integer", "description": "읽기 시작 줄 번호 (1-indexed, 선택)"},
                    "end_line": {"type": "integer", "description": "읽기 끝 줄 번호 (1-indexed, 포함, 선택)"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "파일 전체를 새 내용으로 씁니다. 없으면 생성, 있으면 덮어씁니다. 긴 파일은 append_file로 나눠서 쓰세요.",
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
            "name": "patch_file",
            "description": "파일에서 old_str를 찾아 new_str로 교체합니다. 정확히 1곳만 일치해야 합니다. 파일 일부를 수정할 때 사용하세요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "수정할 파일의 상대 경로"},
                    "old_str": {"type": "string", "description": "파일에서 찾을 기존 문자열 (공백/줄바꿈 포함 정확히 일치)"},
                    "new_str": {"type": "string", "description": "교체할 새 문자열"}
                },
                "required": ["path", "old_str", "new_str"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "파일 끝에 내용을 추가합니다. 긴 파일을 여러 번 나눠 쓸 때 유용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "추가할 파일의 상대 경로"},
                    "content": {"type": "string", "description": "파일 끝에 추가할 내용"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_lines",
            "description": "파일에서 지정한 줄 범위를 삭제합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "수정할 파일의 상대 경로"},
                    "start_line": {"type": "integer", "description": "삭제 시작 줄 번호 (1-indexed)"},
                    "end_line": {"type": "integer", "description": "삭제 끝 줄 번호 (1-indexed, 포함)"}
                },
                "required": ["path", "start_line", "end_line"]
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
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_files",
            "description": "파일 내용에서 텍스트 패턴을 grep으로 검색합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "검색할 텍스트 또는 정규식"},
                    "directory": {"type": "string", "description": "검색 시작 디렉토리. 기본값: 루트"},
                    "file_pattern": {"type": "string", "description": "파일 필터 (예: '*.py'). 기본값: '*'"}
                },
                "required": ["pattern"]
            }
        }
    },
    # ── 실행 ──
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "워크스페이스 디렉토리에서 쉘 명령어를 실행합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "실행할 쉘 명령어"},
                    "timeout": {"type": "integer", "description": "타임아웃(초). 기본값: 30"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_python",
            "description": "Python 코드를 실행하고 stdout/stderr를 반환합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "실행할 Python 코드"},
                    "timeout": {"type": "integer", "description": "타임아웃(초). 기본값: 30"}
                },
                "required": ["code"]
            }
        }
    },
    # ── Git ──
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "git status를 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "확인할 디렉토리. 기본값: 워크스페이스 루트"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "git diff로 변경사항을 확인합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "특정 파일 경로 (선택)"},
                    "staged": {"type": "boolean", "description": "staged 변경사항만 보기. 기본값: false"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_log",
            "description": "git 커밋 히스토리를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_count": {"type": "integer", "description": "조회할 커밋 수. 기본값: 10"},
                    "path": {"type": "string", "description": "특정 파일 경로 (선택)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "파일을 스테이징하고 커밋합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "커밋 메시지"},
                    "paths": {"type": "array", "items": {"type": "string"}, "description": "커밋할 파일 목록. 비워두면 전체(git add .)"}
                },
                "required": ["message"]
            }
        }
    },
    # ── 웹 ──
    {
        "type": "function",
        "function": {
            "name": "fetch_webpage",
            "description": "URL에서 웹페이지 내용을 텍스트로 가져옵니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "가져올 웹페이지 URL"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "DuckDuckGo로 웹 검색을 수행합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색 쿼리"},
                    "max_results": {"type": "integer", "description": "최대 결과 수. 기본값: 5"}
                },
                "required": ["query"]
            }
        }
    },
    # ── 데이터베이스 ──
    {
        "type": "function",
        "function": {
            "name": "query_sqlite",
            "description": "워크스페이스 내 SQLite DB에 SQL 쿼리를 실행합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "db_path": {"type": "string", "description": "워크스페이스 내 .db 파일 경로"},
                    "sql": {"type": "string", "description": "실행할 SQL 쿼리"}
                },
                "required": ["db_path", "sql"]
            }
        }
    },
    # ── 메모리 ──
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "에이전트 장기 메모리에 정보를 저장합니다. 세션이 끝나도 유지됩니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "저장할 키 (예: 'project_structure')"},
                    "value": {"type": "string", "description": "저장할 내용"}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "에이전트 장기 메모리에서 정보를 불러옵니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "조회할 키. 비워두면 전체 메모리 반환"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forget",
            "description": "에이전트 장기 메모리에서 특정 항목을 삭제합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "삭제할 키"}
                },
                "required": ["key"]
            }
        }
    },
    # ── 사용자 정의 툴 관리 ──
    {
        "type": "function",
        "function": {
            "name": "reload_user_tools",
            "description": (
                "user_tools.py를 즉시 재로드합니다. "
                "새 툴 코드를 user_tools.py에 작성한 뒤 반드시 이 툴을 호출해야 새 툴을 사용할 수 있습니다. "
                "user_tools.py 경로: app/modules/user_tools.py (WORKSPACE_PATH 기준: home-server/app/modules/user_tools.py)"
            ),
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
]


def _get_tools() -> list:
    """빌트인 툴 + user_tools.py에 정의된 사용자 툴을 합쳐 반환합니다."""
    return TOOLS + get_user_tools_schema()


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
        self.session_id: Optional[str] = None
        self._messages: list = []
        self.summary: Optional[str] = None

    def _log(self, level: str, message: str):
        entry = LogEntry(level, message, self.iteration)
        self.logs.append(entry)
        print(f"[Agent][{level}][iter={self.iteration}] {message}")

    async def _run(self, objective: str, system_prompt: str, initial_messages: list = None):
        self._stop_event.clear()

        if initial_messages:
            messages: list[dict[str, Any]] = list(initial_messages)
            messages.append({"role": "user", "content": "이전 작업에서 이어서 계속 진행해줘."})
            self._log("INFO", f"[재개] {objective[:200]}")
        else:
            messages = []
            # 목표를 시스템 프롬프트에 항상 포함시켜 반복적으로 상기
            goal_anchor = (
                f"## 현재 목표\n{objective}\n\n"
                "위 목표를 완수하는 것이 최우선입니다. "
                "도구를 사용해 단계적으로 목표를 달성하세요. "
                "목표와 무관한 작업(다른 파일 분석 등)은 하지 마세요."
            )
            base_system = (system_prompt + "\n\n" + goal_anchor) if system_prompt else goal_anchor
            messages.append({"role": "system", "content": base_system})
            messages.append({"role": "user", "content": objective})
            self._log("INFO", f"Objective: {objective[:200]}")

        no_tool_retries = 0
        MAX_NO_TOOL_RETRIES = 3

        try:
            while not self._stop_event.is_set():
                self.iteration += 1
                if self.iteration > MAX_ITERATIONS:
                    self._log("WARN", f"Max iterations ({MAX_ITERATIONS}) reached, stopping")
                    break

                self._log("INFO", f"Calling model (iter {self.iteration})")

                response = await llm_chat(messages, tools=_get_tools())
                msg = response.message
                raw_content: str = msg.content or ""

                # Strip <think>...</think> blocks and orphan </think> tags (Qwen3 thinking tokens)
                visible_content = raw_content
                if "<think>" in raw_content:
                    think_parts = re.findall(r"<think>(.*?)</think>", raw_content, re.DOTALL)
                    if think_parts:
                        self._log("THINK", think_parts[-1].strip()[:300])
                    visible_content = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.DOTALL)
                visible_content = re.sub(r"</think>", "", visible_content).strip()

                if visible_content:
                    self._log("MODEL", visible_content[:400])

                tool_calls = msg.tool_calls or []

                if not tool_calls:
                    messages.append({"role": "assistant", "content": raw_content})
                    if no_tool_retries < MAX_NO_TOOL_RETRIES:
                        no_tool_retries += 1
                        self._log("WARN", f"No tool calls (retry {no_tool_retries}/{MAX_NO_TOOL_RETRIES}) — prompting model to use tools")
                        messages.append({
                            "role": "user",
                            "content": (
                                f"목표: {objective}\n\n"
                                "설명하거나 계획하는 대신 즉시 <tool_call> 형식으로 도구를 호출하세요. "
                                "목표와 무관한 분석은 하지 말고 목표 달성에 필요한 도구만 호출하세요."
                            )
                        })
                        continue
                    self._log("INFO", "No tool calls after retries — agent loop complete")
                    break

                no_tool_retries = 0
                messages.append({"role": "assistant", "content": raw_content})

                for tc in tool_calls:
                    fn_name: str = tc.function.name
                    fn_args: dict = tc.function.arguments or {}

                    self._log("TOOL", f"{fn_name}({json.dumps(fn_args, ensure_ascii=False)[:150]})")
                    result = execute_tool_call(fn_name, fn_args)
                    result_str = json.dumps(result, ensure_ascii=False)
                    self._log("RESULT", result_str[:300])

                    messages.append({"role": "tool", "content": result_str})

                self._messages = messages  # 항상 최신 상태 유지
                await asyncio.sleep(0)  # yield to event loop

        except asyncio.CancelledError:
            self._log("INFO", "Agent loop cancelled")
        except Exception as exc:
            self.status = AgentStatus.ERROR
            self.error = str(exc)
            self._log("ERROR", f"Unhandled exception: {exc}")
        else:
            # 루프가 정상 종료됐을 때만 요약 생성
            if self._messages and self.status != AgentStatus.STOPPING:
                try:
                    self._log("INFO", "결과 요약 생성 중...")
                    summary_messages = list(self._messages) + [{
                        "role": "user",
                        "content": (
                            "지금까지 수행한 작업을 간결하게 요약해줘. "
                            "무엇을 했고 어떤 결과가 나왔는지, 중요한 발견이나 변경사항 위주로 "
                            "3~5문장 이내로 정리해줘. 도구 호출 과정은 생략하고 최종 결과만."
                        )
                    }]
                    summary_resp = await llm_chat(summary_messages)
                    raw_summary = summary_resp.message.content or ""
                    # thinking 토큰 제거
                    self.summary = re.sub(r"<think>.*?</think>", "", raw_summary, flags=re.DOTALL)
                    self.summary = re.sub(r"</think>", "", self.summary).strip()
                    self._log("SUMMARY", self.summary[:300])
                except Exception as e:
                    self._log("WARN", f"요약 생성 실패: {e}")
        finally:
            if self.status not in (AgentStatus.ERROR,):
                self.status = AgentStatus.IDLE
            self._log("INFO", "Agent loop finished")
            if self.session_id:
                sessions.save(
                    self.session_id,
                    status=self.status,
                    iteration=self.iteration,
                    error=self.error,
                    messages=self._messages,
                    logs=[e.to_dict() for e in self.logs],
                    summary=self.summary,
                )

    def start(self, objective: str, system_prompt: str,
              initial_messages: list = None) -> None:
        if self.status == AgentStatus.RUNNING:
            raise ValueError("에이전트 루프가 이미 실행 중입니다.")
        self.status = AgentStatus.RUNNING
        self.current_objective = objective
        self.iteration = 0
        self.error = None
        self.summary = None
        self._messages = list(initial_messages) if initial_messages else []
        self.session_id = sessions.create(objective, system_prompt)
        self.logs.clear()
        self._task = asyncio.create_task(
            self._run(objective, system_prompt, initial_messages)
        )

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
            "session_id": self.session_id,
            "summary": self.summary,
            "logs": [e.to_dict() for e in list(self.logs)[-log_tail:]],
            "total_logs": len(self.logs),
        }

    def clear_logs(self) -> None:
        self.logs.clear()
        self._log("INFO", "Logs cleared")


# Singleton shared across the FastAPI process
agent_loop = AgentLoop()
