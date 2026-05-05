"""
에이전트가 사용할 수 있는 모든 도구 구현.
모든 파일 경로 접근은 WORKSPACE_PATH 내부로 샌드박싱됩니다.
"""

import importlib
import importlib.util
import os
import json
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any

WORKSPACE_PATH = Path(os.getenv("WORKSPACE_PATH", "/home/pi/code-server/src")).resolve()
MEMORY_PATH = Path.home() / ".agent_memory.json"
USER_TOOLS_PATH = Path(__file__).parent / "user_tools.py"

MAX_OUTPUT = 8000  # 도구 결과 최대 문자 수


# ── 사용자 정의 툴 동적 로딩 ──────────────────────────────────

def _load_user_module():
    """user_tools.py를 매번 새로 임포트합니다 (캐시 무시)."""
    if not USER_TOOLS_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("user_tools_dynamic", USER_TOOLS_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_user_tool_functions() -> dict:
    mod = _load_user_module()
    return getattr(mod, "USER_TOOL_FUNCTIONS", {}) if mod else {}


def get_user_tools_schema() -> list:
    mod = _load_user_module()
    return getattr(mod, "USER_TOOLS", []) if mod else []


def reload_user_tools() -> dict[str, Any]:
    """user_tools.py를 즉시 재로드합니다. 새 툴을 작성한 뒤 호출하세요."""
    try:
        mod = _load_user_module()
        fns = getattr(mod, "USER_TOOL_FUNCTIONS", {}) if mod else {}
        tools = getattr(mod, "USER_TOOLS", []) if mod else []
        return {"ok": True, "loaded_tools": list(fns.keys()), "total": len(fns),
                "message": f"user_tools.py 재로드 완료. 등록된 툴: {list(fns.keys())}"}
    except Exception as e:
        return {"error": f"user_tools.py 로드 실패: {e}"}


# ── 경로 보안 ──────────────────────────────────────────────

def _safe_path(relative_or_absolute: str) -> Path:
    # ~ 를 먼저 홈 디렉토리로 변환
    expanded = Path(os.path.expanduser(relative_or_absolute))
    full = expanded.resolve() if expanded.is_absolute() else (WORKSPACE_PATH / expanded).resolve()
    try:
        full.relative_to(WORKSPACE_PATH)
    except ValueError:
        raise ValueError(f"접근 거부: '{relative_or_absolute}' 는 워크스페이스 외부 경로입니다.")
    return full


# ── 파일시스템 ─────────────────────────────────────────────

def list_directory(path: str = "") -> dict[str, Any]:
    try:
        target = _safe_path(path) if path else WORKSPACE_PATH
        if not target.exists():
            return {"error": f"경로가 존재하지 않습니다: {path}"}
        if not target.is_dir():
            return {"error": f"디렉토리가 아닙니다: {path}"}
        entries = []
        for item in sorted(target.iterdir()):
            entries.append({
                "name": item.name,
                "path": str(item.relative_to(WORKSPACE_PATH)),
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None,
            })
        return {"path": str(target.relative_to(WORKSPACE_PATH)) or ".", "entries": entries, "count": len(entries)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"디렉토리 조회 실패: {e}"}


def read_file(path: str, start_line: int = None, end_line: int = None) -> dict[str, Any]:
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"error": f"파일이 존재하지 않습니다: {path}"}
        if not target.is_file():
            return {"error": f"파일이 아닙니다: {path}"}
        size = target.stat().st_size
        if size > 1024 * 1024:
            return {"error": f"파일이 너무 큽니다 ({size} bytes, 최대 1MB). start_line/end_line으로 범위를 지정해주세요."}
        content = target.read_text(encoding="utf-8", errors="replace")
        all_lines = content.splitlines(keepends=True)
        total = len(all_lines)
        if start_line is not None or end_line is not None:
            s = max(0, (start_line or 1) - 1)
            e = min(total, end_line or total)
            sliced = all_lines[s:e]
            return {
                "path": str(target.relative_to(WORKSPACE_PATH)),
                "content": "".join(sliced),
                "start_line": s + 1,
                "end_line": s + len(sliced),
                "total_lines": total,
            }
        return {"path": str(target.relative_to(WORKSPACE_PATH)), "content": content, "size": size, "lines": total}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 읽기 실패: {e}"}


def write_file(path: str, content: str) -> dict[str, Any]:
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"path": str(target.relative_to(WORKSPACE_PATH)), "success": True, "size": len(content.encode())}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 쓰기 실패: {e}"}


def patch_file(path: str, old_str: str, new_str: str) -> dict[str, Any]:
    """파일에서 old_str를 찾아 new_str로 교체합니다. 정확히 1곳만 일치해야 합니다."""
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"error": f"파일이 존재하지 않습니다: {path}"}
        content = target.read_text(encoding="utf-8", errors="replace")
        count = content.count(old_str)
        if count == 0:
            return {"error": "old_str를 파일에서 찾을 수 없습니다. 공백/줄바꿈을 포함해 정확히 일치해야 합니다."}
        if count > 1:
            return {"error": f"old_str가 {count}곳에서 발견되었습니다. 주변 문맥을 더 포함해 유일하게 지정해주세요."}
        new_content = content.replace(old_str, new_str, 1)
        target.write_text(new_content, encoding="utf-8")
        return {"path": str(target.relative_to(WORKSPACE_PATH)), "success": True, "lines": new_content.count("\n") + 1}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 수정 실패: {e}"}


def append_file(path: str, content: str) -> dict[str, Any]:
    """파일 끝에 내용을 추가합니다. 파일이 없으면 생성합니다."""
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as f:
            f.write(content)
        return {"path": str(target.relative_to(WORKSPACE_PATH)), "success": True, "appended_bytes": len(content.encode())}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 추가 실패: {e}"}


def delete_lines(path: str, start_line: int, end_line: int) -> dict[str, Any]:
    """파일에서 start_line~end_line 범위의 줄을 삭제합니다 (1-indexed, 양 끝 포함)."""
    try:
        target = _safe_path(path)
        if not target.exists():
            return {"error": f"파일이 존재하지 않습니다: {path}"}
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        s, e = max(0, start_line - 1), min(len(lines), end_line)
        removed = e - s
        new_lines = lines[:s] + lines[e:]
        target.write_text("".join(new_lines), encoding="utf-8")
        return {"path": str(target.relative_to(WORKSPACE_PATH)), "success": True, "removed_lines": removed, "total_lines": len(new_lines)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"줄 삭제 실패: {e}"}


def find_files(pattern: str, directory: str = "") -> dict[str, Any]:
    try:
        base = _safe_path(directory) if directory else WORKSPACE_PATH
        matches = []
        for match in sorted(base.glob(pattern)):
            if match.is_file():
                try:
                    matches.append({"path": str(match.relative_to(WORKSPACE_PATH)), "size": match.stat().st_size})
                except ValueError:
                    pass
        return {"pattern": pattern, "matches": matches, "count": len(matches)}
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"파일 검색 실패: {e}"}


def search_in_files(pattern: str, directory: str = "", file_pattern: str = "*") -> dict[str, Any]:
    try:
        base = _safe_path(directory) if directory else WORKSPACE_PATH
        result = subprocess.run(
            ["grep", "-rn", "--include", file_pattern, pattern, str(base)],
            capture_output=True, text=True, timeout=15,
        )
        lines = result.stdout.splitlines()
        truncated = len(lines) > 100
        return {
            "pattern": pattern,
            "matches": lines[:100],
            "count": len(lines),
            "truncated": truncated,
        }
    except ValueError as e:
        return {"error": str(e)}
    except subprocess.TimeoutExpired:
        return {"error": "검색 시간 초과"}
    except Exception as e:
        return {"error": f"검색 실패: {e}"}


# ── 셸 / Python 실행 ───────────────────────────────────────

def run_command(command: str, timeout: int = 30) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=str(WORKSPACE_PATH), timeout=timeout,
        )
        return {
            "stdout": result.stdout[:MAX_OUTPUT],
            "stderr": result.stderr[:1000],
            "exit_code": result.returncode,
            "truncated": len(result.stdout) > MAX_OUTPUT,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"명령어 타임아웃 ({timeout}초)"}
    except Exception as e:
        return {"error": f"명령어 실행 실패: {e}"}


def run_python(code: str, timeout: int = 30) -> dict[str, Any]:
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp = f.name
        result = subprocess.run(
            ["python3", tmp], capture_output=True, text=True,
            cwd=str(WORKSPACE_PATH), timeout=timeout,
        )
        os.unlink(tmp)
        return {
            "stdout": result.stdout[:MAX_OUTPUT],
            "stderr": result.stderr[:1000],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Python 실행 타임아웃 ({timeout}초)"}
    except Exception as e:
        return {"error": f"Python 실행 실패: {e}"}


# ── Git ────────────────────────────────────────────────────

def _git_run(args: list, cwd: Path = None) -> str:
    result = subprocess.run(
        ["git"] + args, capture_output=True, text=True,
        cwd=str(cwd or WORKSPACE_PATH), timeout=15,
    )
    return (result.stdout + result.stderr)[:MAX_OUTPUT]


def git_status(path: str = "") -> dict[str, Any]:
    try:
        cwd = _safe_path(path) if path else WORKSPACE_PATH
        return {"output": _git_run(["status"], cwd=cwd)}
    except Exception as e:
        return {"error": str(e)}


def git_diff(path: str = "", staged: bool = False) -> dict[str, Any]:
    try:
        args = ["diff", "--staged"] if staged else ["diff"]
        if path:
            args.append(str(_safe_path(path)))
        return {"output": _git_run(args)}
    except Exception as e:
        return {"error": str(e)}


def git_log(max_count: int = 10, path: str = "") -> dict[str, Any]:
    try:
        args = ["log", f"--max-count={max_count}", "--oneline"]
        if path:
            args.append(str(_safe_path(path)))
        return {"output": _git_run(args)}
    except Exception as e:
        return {"error": str(e)}


def git_commit(message: str, paths: list = None) -> dict[str, Any]:
    try:
        add_args = ["add"] + [str(_safe_path(p)) for p in paths] if paths else ["add", "."]
        _git_run(add_args)
        return {"output": _git_run(["commit", "-m", message])}
    except Exception as e:
        return {"error": str(e)}


# ── 웹 ────────────────────────────────────────────────────

def fetch_webpage(url: str) -> dict[str, Any]:
    try:
        import requests as req
        from bs4 import BeautifulSoup
        resp = req.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return {"url": url, "text": text[:MAX_OUTPUT], "truncated": len(text) > MAX_OUTPUT}
    except Exception as e:
        return {"error": f"웹페이지 가져오기 실패: {e}"}


def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": f"웹 검색 실패: {e}"}


# ── 데이터베이스 ───────────────────────────────────────────

def query_sqlite(db_path: str, sql: str) -> dict[str, Any]:
    try:
        target = _safe_path(db_path)
        if not target.exists():
            return {"error": f"DB 파일 없음: {db_path}"}
        conn = sqlite3.connect(str(target))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(sql)
            rows = [dict(row) for row in cursor.fetchmany(100)]
            conn.commit()
            return {"rows": rows, "count": len(rows)}
        finally:
            conn.close()
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"쿼리 실패: {e}"}


# ── 메모리 ────────────────────────────────────────────────

def _load_memory() -> dict:
    if MEMORY_PATH.exists():
        try:
            return json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_memory(data: dict) -> None:
    MEMORY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def remember(key: str, value: str) -> dict[str, Any]:
    try:
        data = _load_memory()
        data[key] = value
        _save_memory(data)
        return {"ok": True, "key": key, "value": value}
    except Exception as e:
        return {"error": str(e)}


def recall(key: str = "") -> dict[str, Any]:
    try:
        data = _load_memory()
        if key:
            return {"key": key, "value": data.get(key)}
        return {"memories": data, "count": len(data)}
    except Exception as e:
        return {"error": str(e)}


def forget(key: str) -> dict[str, Any]:
    try:
        data = _load_memory()
        if key not in data:
            return {"error": f"키를 찾을 수 없습니다: '{key}'"}
        del data[key]
        _save_memory(data)
        return {"ok": True, "deleted": key}
    except Exception as e:
        return {"error": str(e)}


# ── Tool Dispatcher ────────────────────────────────────────

TOOL_FUNCTIONS: dict[str, Any] = {
    # 파일시스템
    "list_directory":  lambda a: list_directory(**a),
    "read_file":       lambda a: read_file(**a),
    "write_file":      lambda a: write_file(**a),
    "patch_file":      lambda a: patch_file(**a),
    "append_file":     lambda a: append_file(**a),
    "delete_lines":    lambda a: delete_lines(**a),
    "find_files":      lambda a: find_files(**a),
    "search_in_files": lambda a: search_in_files(**a),
    # 실행
    "run_command":     lambda a: run_command(**a),
    "run_python":      lambda a: run_python(**a),
    # Git
    "git_status":      lambda a: git_status(**a),
    "git_diff":        lambda a: git_diff(**a),
    "git_log":         lambda a: git_log(**a),
    "git_commit":      lambda a: git_commit(**a),
    # 웹
    "fetch_webpage":   lambda a: fetch_webpage(**a),
    "search_web":      lambda a: search_web(**a),
    # DB
    "query_sqlite":    lambda a: query_sqlite(**a),
    # 메모리
    "remember":        lambda a: remember(**a),
    "recall":          lambda a: recall(**a),
    "forget":          lambda a: forget(**a),
    # 사용자 정의 툴 관리
    "reload_user_tools": lambda a: reload_user_tools(),
}


def execute_tool_call(name: str, args: dict) -> dict:
    # 빌트인 툴 먼저 확인
    fn = TOOL_FUNCTIONS.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            return {"error": f"도구 실행 오류: {e}"}
    # user_tools.py에서 동적으로 로드된 툴 확인
    user_fns = get_user_tool_functions()
    fn = user_fns.get(name)
    if fn:
        try:
            return fn(args)
        except Exception as e:
            return {"error": f"사용자 정의 도구 실행 오류: {e}"}
    return {"error": f"알 수 없는 도구: '{name}'. reload_user_tools를 호출했는지 확인하세요."}
