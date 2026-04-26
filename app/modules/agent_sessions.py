"""
에이전트 세션 영속성 관리.
각 에이전트 실행을 SQLite에 저장하고 조회/재개할 수 있게 합니다.
"""

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "agent_sessions.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_sessions (
            id          TEXT PRIMARY KEY,
            objective   TEXT NOT NULL,
            system_prompt TEXT,
            status      TEXT NOT NULL DEFAULT 'running',
            iteration   INTEGER DEFAULT 0,
            error       TEXT,
            started_at  TEXT NOT NULL,
            finished_at TEXT,
            messages    TEXT DEFAULT '[]',
            logs        TEXT DEFAULT '[]',
            summary     TEXT
        )
    """)
    # 기존 DB에 summary 컬럼이 없으면 추가
    try:
        conn.execute("ALTER TABLE agent_sessions ADD COLUMN summary TEXT")
        conn.commit()
    except Exception:
        pass
    conn.commit()
    return conn


def create(objective: str, system_prompt: Optional[str]) -> str:
    """새 세션을 생성하고 ID를 반환합니다."""
    session_id = uuid.uuid4().hex[:8]
    with _conn() as conn:
        conn.execute(
            "INSERT INTO agent_sessions (id, objective, system_prompt, started_at) VALUES (?, ?, ?, ?)",
            (session_id, objective, system_prompt, datetime.now().isoformat()),
        )
    return session_id


def save(session_id: str, status: str, iteration: int, error: Optional[str],
         messages: list, logs: list, summary: Optional[str] = None) -> None:
    """실행 완료 후 세션 전체 상태를 저장합니다."""
    with _conn() as conn:
        conn.execute(
            """UPDATE agent_sessions
               SET status=?, iteration=?, error=?, finished_at=?, messages=?, logs=?, summary=?
               WHERE id=?""",
            (
                status, iteration, error,
                datetime.now().isoformat(),
                json.dumps(messages, ensure_ascii=False),
                json.dumps(logs, ensure_ascii=False),
                summary,
                session_id,
            ),
        )


def list_all(limit: int = 50) -> list[dict]:
    """세션 목록을 최신순으로 반환합니다 (messages/logs 제외)."""
    conn = _conn()
    rows = conn.execute(
        """SELECT id, objective, status, iteration, error, started_at, finished_at, summary
           FROM agent_sessions ORDER BY started_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get(session_id: str) -> Optional[dict]:
    """세션 전체 데이터를 반환합니다 (messages/logs 포함)."""
    conn = _conn()
    row = conn.execute("SELECT * FROM agent_sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["messages"] = json.loads(d["messages"] or "[]")
    d["logs"] = json.loads(d["logs"] or "[]")
    return d


def delete(session_id: str) -> bool:
    conn = _conn()
    affected = conn.execute("DELETE FROM agent_sessions WHERE id=?", (session_id,)).rowcount
    conn.commit()
    conn.close()
    return affected > 0
