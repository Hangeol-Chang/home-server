import re

with open('/home/pi/code-server/src/home-server/app/modules/gdrive_manager.py', 'r') as f:
    text = f.read()

new_func = """@router.get("/files/{file_id}/content")
def get_file_content(file_id: str, request: Request):
    \"\"\"
    파일 내용을 스트리밍으로 반환합니다. HTTP Range 요청을 지원하여 재생 탐색이 가능하게 합니다.
    Google Docs/Sheets/Slides 같은 Google 네이티브 형식은 PDF로 export합니다.
    \"\"\"
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
"""

pattern = re.compile(r'@router\.get\("/files/\{file_id\}/content"\)\ndef get_file_content\(file_id: str\):.*?except Exception as e:\n\s+raise HTTPException\(status_code=500, detail=str\(e\)\)\n', re.DOTALL)

if not pattern.search(text):
    print("Pattern not found!")
else:
    new_text = pattern.sub(new_func, text)
    with open('/home/pi/code-server/src/home-server/app/modules/gdrive_manager.py', 'w') as f:
        f.write(new_text)
    print("Replaced successfully.")
