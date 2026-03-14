import os
import io
import requests
import google.auth.transport.requests as google_requests
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / "env" / ".env")

# Google Drive API
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

router = APIRouter(
    prefix="/gdrive",
    tags=["Google Drive"],
    responses={404: {"description": "Not found"}}
)

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "")
ROOT_FOLDER_ID = os.getenv("GDRIVE_ROOT_FOLDER_ID", "root")


def _get_service():
    """Service Account로 Drive 서비스 반환"""
    if not SERVICE_ACCOUNT_FILE:
        raise HTTPException(
            status_code=503,
            detail="GDRIVE_SERVICE_ACCOUNT_JSON 환경변수가 설정되지 않았습니다."
        )
    cred_path = Path(__file__).resolve().parent.parent / SERVICE_ACCOUNT_FILE
    if not cred_path.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Service Account 키 파일을 찾을 수 없습니다: {cred_path}"
        )
    credentials = service_account.Credentials.from_service_account_file(
        str(cred_path), scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


@router.get("/files")
def list_files(
    folder_id: Optional[str] = Query(default=None, description="폴더 ID (기본값: 루트 폴더)"),
    page_size: int = Query(default=50, le=200),
    page_token: Optional[str] = Query(default=None)
):
    """
    특정 폴더의 파일 목록을 반환합니다.
    folder_id가 없으면 GDRIVE_ROOT_FOLDER_ID 환경변수에 설정된 폴더를 사용합니다.
    """
    service = _get_service()
    target_folder = folder_id or ROOT_FOLDER_ID

    try:
        query = f"'{target_folder}' in parents and trashed = false"
        kwargs = {
            "q": query,
            "pageSize": page_size,
            "fields": "nextPageToken, files(id, name, mimeType, size, modifiedTime, parents, iconLink, webViewLink)",
            "orderBy": "folder,name"
        }
        if page_token:
            kwargs["pageToken"] = page_token

        result = service.files().list(**kwargs).execute()

        files = result.get("files", [])
        # 폴더 / 파일 분류
        items = []
        for f in files:
            items.append({
                "id": f["id"],
                "name": f["name"],
                "mimeType": f["mimeType"],
                "isFolder": f["mimeType"] == "application/vnd.google-apps.folder",
                "size": f.get("size"),
                "modifiedTime": f.get("modifiedTime"),
                "webViewLink": f.get("webViewLink"),
            })

        return {
            "folderId": target_folder,
            "items": items,
            "nextPageToken": result.get("nextPageToken")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}/meta")
def get_file_meta(file_id: str):
    """파일/폴더 메타데이터 반환"""
    service = _get_service()
    try:
        meta = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, modifiedTime, parents, webViewLink, description"
        ).execute()
        return meta
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class DownloadStreamer:
    def __init__(self):
        self.buffer = b""
    def write(self, d):
        self.buffer += d
    def get_and_clear(self):
        ret = self.buffer
        self.buffer = b""
        return ret


@router.get("/files/{file_id}/content")
def get_file_content(file_id: str, request: Request):
    """
    파일 내용을 스트리밍으로 반환합니다. HTTP Range 요청을 지원하여 재생 탐색이 가능하게 합니다.
    Google Docs/Sheets/Slides 같은 Google 네이티브 형식은 PDF로 export합니다.
    """
    service = _get_service()

    EXPORT_MIME_MAP = {
        "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.spreadsheet": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
    }

    try:
        meta = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size"
        ).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    mime = meta["mimeType"]
    filename = meta["name"]
    from urllib.parse import quote
    encoded_filename = quote(filename.encode("utf-8"))

    try:
        if mime in EXPORT_MIME_MAP:
            export_mime, ext = EXPORT_MIME_MAP[mime]
            req_api = service.files().export_media(fileId=file_id, mimeType=export_mime)
            if not filename.endswith(ext):
                filename += ext
            encoded_filename = quote(filename.encode("utf-8"))

            def gdrive_stream():
                streamer = DownloadStreamer()
                downloader = MediaIoBaseDownload(streamer, req_api, chunksize=5*1024*1024)
                done = False
                while not done:
                    try:
                        _, done = downloader.next_chunk()
                        yield streamer.get_and_clear()
                    except Exception:
                        break

            return StreamingResponse(
                gdrive_stream(),
                media_type=export_mime,
                headers={
                    "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
                }
            )
        else:
            # Native media - Supports Range header via direct requests
            cred_path = Path(__file__).resolve().parent.parent / SERVICE_ACCOUNT_FILE
            credentials = service_account.Credentials.from_service_account_file(
                str(cred_path), scopes=SCOPES
            )
            req = google_requests.Request()
            credentials.refresh(req)
            token = credentials.token

            url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
            headers = {"Authorization": f"Bearer {token}"}
            
            # Forward Range request
            range_header = request.headers.get("Range")
            if range_header:
                headers["Range"] = range_header
                
            upstream_response = requests.get(url, headers=headers, stream=True)
            
            def stream_generator():
                for chunk in upstream_response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        yield chunk
                        
            resp_headers = {
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
                "Accept-Ranges": "bytes"
            }
            
            for h in ["Content-Length", "Content-Range", "Content-Type"]:
                if h in upstream_response.headers:
                    resp_headers[h] = upstream_response.headers[h]
                    
            if "Content-Type" not in resp_headers:
                resp_headers["Content-Type"] = mime

            status_code = upstream_response.status_code
            # Ensure it is allowed by FastAPI (FastAPI automatically handles 200/206 based on standard Response if passed properly, but we explicitly set it)
            return StreamingResponse(
                stream_generator(),
                status_code=status_code,
                headers=resp_headers
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    mime = meta["mimeType"]
    filename = meta["name"]
    from urllib.parse import quote

    try:
        if mime in EXPORT_MIME_MAP:
            export_mime, ext = EXPORT_MIME_MAP[mime]
            request = service.files().export_media(fileId=file_id, mimeType=export_mime)
            if not filename.endswith(ext):
                filename += ext
        else:
            export_mime = mime
            request = service.files().get_media(fileId=file_id)

        def gdrive_stream():
            streamer = DownloadStreamer()
            # 5MB chunks
            downloader = MediaIoBaseDownload(streamer, request, chunksize=5*1024*1024)
            done = False
            while not done:
                try:
                    _, done = downloader.next_chunk()
                    yield streamer.get_and_clear()
                except Exception:
                    break
                    
        encoded_filename = quote(filename.encode("utf-8"))
        # 스트리밍 응답 (inline으로 바로 볼 수 있도록 변경)
        return StreamingResponse(
            gdrive_stream(),
            media_type=export_mime,
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/breadcrumb")
def get_breadcrumb(folder_id: str = Query(..., description="현재 폴더 ID")):
    """
    폴더의 경로(breadcrumb)를 반환합니다. 루트까지 거슬러 올라갑니다.
    """
    service = _get_service()
    crumbs = []
    current_id = folder_id
    visited = set()

    try:
        while current_id and current_id not in visited:
            visited.add(current_id)
            meta = service.files().get(
                fileId=current_id,
                fields="id, name, parents"
            ).execute()
            crumbs.insert(0, {"id": meta["id"], "name": meta["name"]})
            parents = meta.get("parents", [])
            if not parents:
                break
            current_id = parents[0]
            # Drive root 도달 시 중단
            if current_id == ROOT_FOLDER_ID:
                crumbs.insert(0, {"id": ROOT_FOLDER_ID, "name": "홈"})
                break
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"breadcrumb": crumbs}
