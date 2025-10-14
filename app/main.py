import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# 라우터 임포트
from modules import asset_manager, schedule_manager


# .env load 예시
env_dir = Path(__file__).resolve().parent / "env"
load_dotenv(env_dir / ".env")

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Home Server API",
    description="간단한 FastAPI 백엔드 서버 예제",
    version="1.0.0"
)

# CORS 미들웨어 추가 (프론트엔드에서 접근할 수 있도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(asset_manager.router)
app.include_router(schedule_manager.router)

# 간단한 데이터 모델 정의
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: str

# 메모리에 저장할 임시 데이터
items_db = []
users_db = []
next_item_id = 1
next_user_id = 1

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
            "schedule_manager": "/schedule-manager"
        }
    }

# 헬스 체크
@app.get("/health")
async def health_check():
    """서버 헬스 체크"""
    return {"status": "healthy"}

@app.post("/users", response_model=User)
async def create_user(user: User):
    """새 사용자 생성"""
    global next_user_id
    user_dict = user.dict()
    user_dict["id"] = next_user_id
    next_user_id += 1
    users_db.append(user_dict)
    return user_dict

# 검색 엔드포인트
@app.get("/items/search/{query}")
async def search_items(query: str):
    """아이템 이름으로 검색"""
    results = []
    for item in items_db:
        if query.lower() in item["name"].lower():
            results.append(item)
    return {"query": query, "results": results}

if __name__ == "__main__":
    # 서버 실행 (개발 환경)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5005,
        reload=True  # 코드 변경 시 자동 재시작
    )
