from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime
from models.asset import Asset, AssetCreate, AssetUpdate, AssetStatus

# 라우터 생성
router = APIRouter(
    prefix="/asset-manager",
    tags=["Asset Manager"],
    responses={404: {"description": "Not found"}}
)

# 메모리 기반 임시 데이터베이스
assets_db = []
next_asset_id = 1

@router.get("/", response_model=List[Asset])
async def get_all_assets():
    """모든 자산 조회"""
    return assets_db

@router.get("/assets", response_model=List[Asset])
async def get_assets():
    """모든 자산 조회 (별칭)"""
    return assets_db

@router.get("/assets/{asset_id}", response_model=Asset)
async def get_asset(asset_id: int):
    """특정 자산 조회"""
    for asset in assets_db:
        if asset["id"] == asset_id:
            return asset
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Asset with id {asset_id} not found"
    )

@router.post("/assets", response_model=Asset, status_code=status.HTTP_201_CREATED)
async def create_asset(asset: AssetCreate):
    """새 자산 생성"""
    global next_asset_id
    
    now = datetime.now()
    asset_dict = asset.dict()
    asset_dict.update({
        "id": next_asset_id,
        "created_at": now,
        "updated_at": now
    })
    
    next_asset_id += 1
    assets_db.append(asset_dict)
    
    return asset_dict

@router.put("/assets/{asset_id}", response_model=Asset)
async def update_asset(asset_id: int, asset_update: AssetUpdate):
    """자산 정보 수정"""
    for i, asset in enumerate(assets_db):
        if asset["id"] == asset_id:
            # 업데이트할 필드만 적용
            update_data = asset_update.dict(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.now()
                assets_db[i].update(update_data)
            return assets_db[i]
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Asset with id {asset_id} not found"
    )

@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: int):
    """자산 삭제"""
    for i, asset in enumerate(assets_db):
        if asset["id"] == asset_id:
            deleted_asset = assets_db.pop(i)
            return {
                "message": f"Asset {asset_id} deleted successfully",
                "deleted_asset": deleted_asset
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Asset with id {asset_id} not found"
    )

@router.get("/assets/status/{status}", response_model=List[Asset])
async def get_assets_by_status(status: AssetStatus):
    """상태별 자산 조회"""
    filtered_assets = [asset for asset in assets_db if asset["status"] == status]
    return filtered_assets

@router.get("/assets/search/{query}")
async def search_assets(query: str):
    """자산 이름으로 검색"""
    results = []
    query_lower = query.lower()
    
    for asset in assets_db:
        if (query_lower in asset["name"].lower() or 
            (asset.get("description") and query_lower in asset["description"].lower()) or
            (asset.get("serial_number") and query_lower in asset["serial_number"].lower())):
            results.append(asset)
    
    return {
        "query": query,
        "total_results": len(results),
        "results": results
    }

@router.get("/stats")
async def get_asset_stats():
    """자산 통계 정보"""
    total_assets = len(assets_db)
    
    if total_assets == 0:
        return {
            "total_assets": 0,
            "by_status": {},
            "by_type": {},
            "total_value": 0
        }
    
    # 상태별 통계
    status_stats = {}
    type_stats = {}
    total_value = 0
    
    for asset in assets_db:
        # 상태별 카운트
        status = asset["status"]
        status_stats[status] = status_stats.get(status, 0) + 1
        
        # 타입별 카운트
        asset_type = asset["asset_type"]
        type_stats[asset_type] = type_stats.get(asset_type, 0) + 1
        
        # 총 가치 계산
        if asset.get("purchase_price"):
            total_value += asset["purchase_price"]
    
    return {
        "total_assets": total_assets,
        "by_status": status_stats,
        "by_type": type_stats,
        "total_value": round(total_value, 2)
    }