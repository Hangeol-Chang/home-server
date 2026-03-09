"""
Workspace filesystem tools for Gemini function calling.
모든 경로 접근은 WORKSPACE_PATH 내부로 샌드박싱됩니다.
"""

import os
import glob
from pathlib import Path
from typing import Any

# 워크스페이스 루트 (환경변수로 설정, 기본값: Pi 경로)
WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/home/pi/code-server/src")).resolve()


# ===== 보안: 경로 검증 =====

def _safe_path(relative_or_absolute: str) -> Path:
    """
    입력 경로를 WORKSPACE_PATH 내부로 제한해 반환합니다.
    경로 탈출(../) 시도 시 ValueError를 발생시킵니다.
    """
    raw = Path(relative_or_absolute)
    # 절대 경로가 아니면 workspace 기준으로 조합
    if not raw.is_absolute():
        full = (WORKSPACE_PATH / raw).resolve()
    else:
        full = raw.resolve()

    try:
        full.relative_to(WORKSPACE_PATH)
    except ValueError:
        raise ValueError(f"접근 거부: '{relative_or_absolute}' 는 워크스페이스 외부 경로입니다.")
    return full


# ===== Tool 구현 함수 =====

def list_directory(path: str = "") -> dict[str, Any]:
    """
    지정한 경로의 디렉토리 목록을 반환합니다.
    path가 비어있으면 워크스페이스 루트를 조회합니다.
    """
    try:
        target = _safe_path(path) if path else WORKSPACE_PATH
        if not target.exists():
            return {"error": f"경로가 존재하지 않습니다: {path}"}
        if not target.is_dir():
            return {"error": f"디렉토리가 아닙니다: {path}"}

        entries = []
        for item in sorted(target.iterdir()):
            relative = str(item.relative_to(WORKSPACE_PATH))
            entries.append({
                "name": item.name,
                "path": relative,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {
            "path": str(target.relative_to(WORKSPACE_PATH)) or ".",
            "entries": entries,
            "count": len(entries),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"디렉토리 조회 실패: {str(e)}"}


def read_file(path: str) -> dict[str, Any]:
    """
    지정한 파일의 내용을 읽어 반환합니다.
    텍스트 파일만 지원하며, 최대 200KB까지 읽습니다.
    """
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"error": f"파일이 존재하지 않습니다: {path}"}
        if not target.is_file():
            return {"error": f"파일이 아닙니다: {path}"}

        size = target.stat().st_size
        if size > 200 * 1024:  # 200KB 제한
            return {"error": f"파일이 너무 큽니다 ({size} bytes, 최대 200KB)"}

        content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "path": str(target.relative_to(WORKSPACE_PATH)),
            "content": content,
            "size": size,
            "lines": content.count("\n") + 1,
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 읽기 실패: {str(e)}"}


def write_file(path: str, content: str) -> dict[str, Any]:
    """
    지정한 경로에 내용을 씁니다. 파일이 없으면 생성하고,
    있으면 덮어씁니다. 상위 디렉토리가 없으면 자동 생성합니다.
    """
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {
            "path": str(target.relative_to(WORKSPACE_PATH)),
            "success": True,
            "size": len(content.encode("utf-8")),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 쓰기 실패: {str(e)}"}


def find_files(pattern: str, directory: str = "") -> dict[str, Any]:
    """
    glob 패턴으로 파일을 검색합니다.
    예) pattern="**/*.py", directory="home-server/app"
    """
    try:
        base = _safe_path(directory) if directory else WORKSPACE_PATH
        if not base.exists():
            return {"error": f"경로가 존재하지 않습니다: {directory}"}

        matches = []
        for match in sorted(base.glob(pattern)):
            if not match.is_file():
                continue
            try:
                relative = str(match.relative_to(WORKSPACE_PATH))
                matches.append({
                    "path": relative,
                    "size": match.stat().st_size,
                })
            except ValueError:
                pass  # 워크스페이스 외부는 무시

        return {
            "pattern": pattern,
            "base": str(base.relative_to(WORKSPACE_PATH)) or ".",
            "matches": matches,
            "count": len(matches),
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 검색 실패: {str(e)}"}


# ===== Gemini Function Declarations =====

from google.genai import types

WORKSPACE_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="list_directory",
            description=(
                "워크스페이스 내 디렉토리 목록을 조회합니다. "
                "path가 빈 문자열이면 루트를 조회합니다."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "path": types.Schema(
                        type="STRING",
                        description="조회할 상대 경로 (예: 'home-server/app'). 기본값: 루트",
                    )
                },
                required=[],
            ),
        ),
        types.FunctionDeclaration(
            name="read_file",
            description="워크스페이스 내 파일의 내용을 읽습니다.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "path": types.Schema(
                        type="STRING",
                        description="읽을 파일의 상대 경로 (예: 'home-server/app/main.py')",
                    )
                },
                required=["path"],
            ),
        ),
        types.FunctionDeclaration(
            name="write_file",
            description=(
                "워크스페이스 내 파일에 내용을 씁니다. "
                "파일이 없으면 생성하고, 있으면 전체를 덮어씁니다."
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "path": types.Schema(
                        type="STRING",
                        description="쓸 파일의 상대 경로",
                    ),
                    "content": types.Schema(
                        type="STRING",
                        description="파일에 쓸 전체 내용",
                    ),
                },
                required=["path", "content"],
            ),
        ),
        types.FunctionDeclaration(
            name="find_files",
            description=(
                "glob 패턴으로 파일을 검색합니다. "
                "예) pattern='**/*.py' 로 모든 파이썬 파일 검색"
            ),
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "pattern": types.Schema(
                        type="STRING",
                        description="glob 패턴 (예: '**/*.py', '*.md')",
                    ),
                    "directory": types.Schema(
                        type="STRING",
                        description="검색 시작 디렉토리 상대 경로. 기본값: 루트",
                    ),
                },
                required=["pattern"],
            ),
        ),
    ]
)


# ===== Tool Dispatcher =====

TOOL_FUNCTIONS = {
    "list_directory": lambda args: list_directory(**args),
    "read_file":      lambda args: read_file(**args),
    "write_file":     lambda args: write_file(**args),
    "find_files":     lambda args: find_files(**args),
}


def execute_tool_call(name: str, args: dict) -> dict:
    """Gemini가 요청한 함수 호출을 실행하고 결과를 반환합니다."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": f"알 수 없는 도구: {name}"}
    try:
        return fn(args)
    except Exception as e:
        return {"error": f"도구 실행 오류: {str(e)}"}
