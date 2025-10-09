from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

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
        "docs": "/docs"
    }

# 헬스 체크
@app.get("/health")
async def health_check():
    """서버 헬스 체크"""
    return {"status": "healthy"}

# Items CRUD 엔드포인트들
@app.get("/items", response_model=List[Item])
async def get_items():
    """모든 아이템 조회"""
    return items_db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """특정 아이템 조회"""
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """새 아이템 생성"""
    global next_item_id
    item_dict = item.dict()
    item_dict["id"] = next_item_id
    next_item_id += 1
    items_db.append(item_dict)
    return item_dict

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    """아이템 수정"""
    for i, existing_item in enumerate(items_db):
        if existing_item["id"] == item_id:
            item_dict = item.dict()
            item_dict["id"] = item_id
            items_db[i] = item_dict
            return item_dict
    raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """아이템 삭제"""
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            deleted_item = items_db.pop(i)
            return {"message": "아이템이 삭제되었습니다", "deleted_item": deleted_item}
    raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다")

# Users CRUD 엔드포인트들
@app.get("/users", response_model=List[User])
async def get_users():
    """모든 사용자 조회"""
    return users_db

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
        port=8000,
        reload=True  # 코드 변경 시 자동 재시작
    )
