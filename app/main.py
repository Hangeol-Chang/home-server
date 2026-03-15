import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# 라우터 임포트
from modules import asset_manager, schedule_manager, notebook_manager, chat_manager, gdrive_manager
# 데이터베이스 초기화
from utils.database import init_database

# .env load 예시
env_dir = Path(__file__).resolve().parent / "env"
load_dotenv(env_dir / ".env")

# 데이터베이스 초기화
init_database()

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Home Server API",
    description="간단한 FastAPI 백엔드 서버 예제",
    version="1.0.0"
)

# 허용된 오리진 목록
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://hgchang1.iptime.org:5173",
]

# CORS 미들웨어 추가 (특정 도메인만 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(asset_manager.router)
app.include_router(schedule_manager.router)
app.include_router(notebook_manager.router)
app.include_router(chat_manager.router)
app.include_router(gdrive_manager.router)

# 기본 라우트
@app.get("/")
async def root():
    """서버 상태 확인용 기본 엔드포인트"""
    return {
        "message": "FastAPI 홈 서버가 실행 중입니다!",
        "status": "running",
        "docs": "/docs",
        "modules": {
            "asset_manager": "/asset-manager",
            "schedule_manager": "/schedule-manager",
            "chat": "/chat"
        }
    }

# 헬스 체크
@app.get("/health")
async def health_check():
    """서버 헬스 체크"""
    return {"status": "healthy"}

if __name__ == "__main__":
    # 서버 실행 (개발 환경)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        reload=True  # 코드 변경 시 자동 재시작
    )
