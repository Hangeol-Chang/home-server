"""
에이전트가 런타임에 추가하는 사용자 정의 툴.

새 툴을 추가하려면:
1. 아래에 Python 함수를 작성합니다.
2. USER_TOOL_FUNCTIONS 딕셔너리에 등록합니다.
3. USER_TOOLS 리스트에 JSON 스키마를 추가합니다.
4. reload_user_tools 툴을 호출해 즉시 반영합니다 (서버 재시작 불필요).

예시:
    def my_tool(arg1: str, arg2: int = 0) -> dict:
        return {"result": arg1 * arg2}

    USER_TOOL_FUNCTIONS["my_tool"] = lambda a: my_tool(**a)

    USER_TOOLS.append({
        "type": "function",
        "function": {
            "name": "my_tool",
            "description": "설명",
            "parameters": {
                "type": "object",
                "properties": {
                    "arg1": {"type": "string", "description": "..."},
                    "arg2": {"type": "integer", "description": "...", "default": 0}
                },
                "required": ["arg1"]
            }
        }
    })
"""

from typing import Any

# ── 사용자 정의 툴 함수 ──────────────────────────────────────

# 여기에 새 툴 함수를 추가하세요.


# ── 툴 등록 ─────────────────────────────────────────────────

USER_TOOL_FUNCTIONS: dict[str, Any] = {
    # "tool_name": lambda a: tool_function(**a),
}

USER_TOOLS: list[dict] = [
    # { "type": "function", "function": { ... } }
]
