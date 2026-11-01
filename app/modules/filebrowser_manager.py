import os
import mimetypes
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

load_dotenv(Path(__file__).resolve().parent.parent / "env" / ".env")

router = APIRouter(prefix="/filebrowser", tags=["File Browser"])

FB_URL = os.getenv("FILEBROWSER_URL", "").rstrip("/")
FB_USER = os.getenv("FILEBROWSER_USER", "")
FB_PASS = os.getenv("FILEBROWSER_PASS", "")
# 자체 서명 인증서 환경 기본값: 검증 끔. 정식 인증서면 FILEBROWSER_VERIFY_TLS=true
FB_VERIFY = os.getenv("FILEBROWSER_VERIFY_TLS", "false").lower() == "true"

_client = httpx.AsyncClient(verify=FB_VERIFY, timeout=httpx.Timeout(30.0, read=None))
_token: str | None = None


async def _login() -> str:
    global _token
    if not (FB_URL and FB_USER and FB_PASS):
        raise HTTPException(503, "FILEBROWSER_URL/USER/PASS 환경변수가 설정되지 않았습니다.")
    r = await _client.post(f"{FB_URL}/api/login", json={"username": FB_USER, "password": FB_PASS})
    if r.status_code != 200:
        raise HTTPException(502, f"File Browser 로그인 실패: {r.status_code}")
    _token = r.text.strip().strip('"')
    return _token


async def _send(method: str, api_path: str, *, headers=None, content=None, params=None, stream=False):
    """토큰 자동 로그인/401 시 1회 재로그인. 업로드 스트림은 재시도 불가라 401이면 그대로 실패."""
    for attempt in (0, 1):
        token = _token or await _login()
        req = _client.build_request(
            method, f"{FB_URL}{api_path}", params=params, content=content,
            headers={**(headers or {}), "X-Auth": token},
        )
        try:
            r = await _client.send(req, stream=stream)
        except httpx.HTTPError as e:
            raise HTTPException(502, f"File Browser 연결 실패: {e}")
        if r.status_code != 401 or attempt == 1 or content is not None:
            return r
        await r.aclose()
        await _login()


def _norm(path: str) -> str:
    p = "/" + path.strip("/")
    if ".." in p.split("/"):
        raise HTTPException(400, "잘못된 경로")
    return p


def _enc(path: str) -> str:
    return quote(path, safe="/")


@router.get("/files")
async def list_files(path: str = Query(default="/")):
    p = _norm(path)
    r = await _send("GET", f"/api/resources{_enc(p)}")
    if r.status_code != 200:
        raise HTTPException(r.status_code, r.text or "목록 조회 실패")
    data = r.json()
    items = [
        {
            "id": it["path"],
            "name": it["name"],
            "isFolder": it["isDir"],
            "size": None if it["isDir"] else it.get("size"),
            "modifiedTime": it.get("modified"),
            "mimeType": "folder" if it["isDir"] else (mimetypes.guess_type(it["name"])[0] or "application/octet-stream"),
        }
        for it in data.get("items") or []
    ]
    items.sort(key=lambda i: (not i["isFolder"], i["name"].lower()))
    return {"path": p, "items": items}


@router.get("/content")
async def get_content(request: Request, path: str, download: bool = False):
    """Range 요청을 그대로 전달 → 비디오 탐색/스트리밍 가능."""
    p = _norm(path)
    fwd = {"Range": request.headers["Range"]} if "Range" in request.headers else None
    r = await _send("GET", f"/api/raw{_enc(p)}", params={"inline": "true"}, headers=fwd, stream=True)
    if r.status_code not in (200, 206):
        await r.aclose()
        raise HTTPException(r.status_code, "파일을 가져올 수 없습니다.")

    name = p.rsplit("/", 1)[-1]
    headers = {
        "Content-Disposition": f"{'attachment' if download else 'inline'}; filename*=UTF-8''{quote(name)}",
        "Accept-Ranges": "bytes",
    }
    for h in ("Content-Length", "Content-Range", "Content-Type", "Last-Modified"):
        if h in r.headers:
            headers[h] = r.headers[h]
    if "Content-Type" not in headers:
        headers["Content-Type"] = mimetypes.guess_type(name)[0] or "application/octet-stream"

    async def body():
        try:
            async for chunk in r.aiter_raw(1024 * 1024):
                yield chunk
        finally:
            await r.aclose()

    return StreamingResponse(body(), status_code=r.status_code, headers=headers)


@router.post("/upload")
async def upload(request: Request, path: str, override: bool = False):
    """요청 본문(raw bytes)을 File Browser로 그대로 스트리밍. path = 저장될 전체 경로(파일명 포함)."""
    p = _norm(path)
    if p == "/":
        raise HTTPException(400, "파일 경로가 필요합니다.")
    headers = {}
    if "content-length" in request.headers:
        headers["Content-Length"] = request.headers["content-length"]
    r = await _send(
        "POST", f"/api/resources{_enc(p)}",
        params={"override": "true" if override else "false"},
        headers=headers, content=request.stream(),
    )
    if r.status_code == 409:
        raise HTTPException(409, "같은 이름의 파일이 이미 있습니다.")
    if r.status_code not in (200, 201):
        raise HTTPException(r.status_code, r.text or "업로드 실패")
    return {"ok": True, "path": p}


@router.post("/mkdir")
async def mkdir(path: str):
    p = _norm(path)
    if p == "/":
        raise HTTPException(400, "폴더 이름이 필요합니다.")
    r = await _send("POST", f"/api/resources{_enc(p)}/")
    if r.status_code == 409:
        raise HTTPException(409, "같은 이름이 이미 있습니다.")
    if r.status_code not in (200, 201):
        raise HTTPException(r.status_code, r.text or "폴더 생성 실패")
    return {"ok": True, "path": p}


@router.delete("/files")
async def delete(path: str):
    """파일 또는 폴더(하위 포함) 삭제."""
    p = _norm(path)
    if p == "/":
        raise HTTPException(400, "루트는 삭제할 수 없습니다.")
    r = await _send("DELETE", f"/api/resources{_enc(p)}")
    if r.status_code not in (200, 204):
        raise HTTPException(r.status_code, r.text or "삭제 실패")
    return {"ok": True}
