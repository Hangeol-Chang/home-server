from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date as date_type
from models.asset import (
    AssetClass, AssetClassCreate,
    AssetCategory, AssetCategoryCreate,
    AssetTier, AssetTierCreate,
    AssetTransaction, AssetTransactionCreate, AssetTransactionUpdate,
    AssetTransactionDetail, CategoryStatistics, TierStatistics,
    PeriodSummary, MonthlyStatistics
)
from utils.database import get_db_connection

# 라우터 생성
router = APIRouter(
    prefix="/asset-manager",
    tags=["Asset Manager"],
    responses={404: {"description": "Not found"}}
)

# ===== Classes (거래 분류) API =====

@router.get("/classes", response_model=List[AssetClass])
async def get_classes():
    """모든 거래 분류 조회 (지출/수익/저축)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, display_name, description, is_active, created_at
            FROM asset_classes
            WHERE is_active = TRUE
            ORDER BY id
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

# ===== Categories (카테고리) API =====

@router.get("/categories", response_model=List[AssetCategory])
async def get_categories(
    class_id: Optional[int] = Query(None, description="거래 분류 ID로 필터링")
):
    """카테고리 목록 조회 (선택적으로 class_id로 필터링)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if class_id:
            cursor.execute("""
                SELECT id, class_id, name, display_name, description, 
                       is_active, sort_order, created_at
                FROM asset_categories
                WHERE class_id = ? AND is_active = TRUE
                ORDER BY sort_order, id
            """, (class_id,))
        else:
            cursor.execute("""
                SELECT id, class_id, name, display_name, description, 
                       is_active, sort_order, created_at
                FROM asset_categories
                WHERE is_active = TRUE
                ORDER BY class_id, sort_order, id
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/categories", response_model=AssetCategory, status_code=status.HTTP_201_CREATED)
async def create_category(category: AssetCategoryCreate):
    """새 카테고리 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # class_id 유효성 검사
        cursor.execute("SELECT id FROM asset_classes WHERE id = ?", (category.class_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with id {category.class_id} not found"
            )
        
        cursor.execute("""
            INSERT INTO asset_categories 
            (class_id, name, display_name, description, is_active, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (category.class_id, category.name, category.display_name,
              category.description, category.is_active, category.sort_order))
        
        category_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, class_id, name, display_name, description, 
                   is_active, sort_order, created_at
            FROM asset_categories WHERE id = ?
        """, (category_id,))
        return dict(cursor.fetchone())

# ===== Tiers (중요도/필수도) API =====

@router.get("/tiers", response_model=List[AssetTier])
async def get_tiers(
    class_id: Optional[int] = Query(None, description="거래 분류 ID로 필터링")
):
    """티어 목록 조회 (선택적으로 class_id로 필터링)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if class_id:
            cursor.execute("""
                SELECT id, class_id, tier_level, name, display_name, description,
                       is_active, sort_order, created_at
                FROM asset_tiers
                WHERE class_id = ? AND is_active = TRUE
                ORDER BY sort_order, tier_level
            """, (class_id,))
        else:
            cursor.execute("""
                SELECT id, class_id, tier_level, name, display_name, description,
                       is_active, sort_order, created_at
                FROM asset_tiers
                WHERE is_active = TRUE
                ORDER BY class_id, sort_order, tier_level
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/tiers", response_model=AssetTier, status_code=status.HTTP_201_CREATED)
async def create_tier(tier: AssetTierCreate):
    """새 티어 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # class_id 유효성 검사
        cursor.execute("SELECT id FROM asset_classes WHERE id = ?", (tier.class_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Class with id {tier.class_id} not found"
            )
        
        cursor.execute("""
            INSERT INTO asset_tiers 
            (class_id, tier_level, name, display_name, description, is_active, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tier.class_id, tier.tier_level, tier.name, tier.display_name,
              tier.description, tier.is_active, tier.sort_order))
        
        tier_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, class_id, tier_level, name, display_name, description,
                   is_active, sort_order, created_at
            FROM asset_tiers WHERE id = ?
        """, (tier_id,))
        return dict(cursor.fetchone())

# ===== Transactions (거래) CRUD API =====

@router.post("/transactions", response_model=AssetTransaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(transaction: AssetTransactionCreate):
    """새 거래 생성 (지출/수익/저축)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 유효성 검사
        cursor.execute("SELECT id FROM asset_classes WHERE id = ?", (transaction.class_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Class with id {transaction.class_id} not found")
        
        cursor.execute("SELECT id FROM asset_categories WHERE id = ? AND class_id = ?",
                      (transaction.category_id, transaction.class_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Category {transaction.category_id} does not belong to class {transaction.class_id}")
        
        cursor.execute("SELECT id FROM asset_tiers WHERE id = ? AND class_id = ?",
                      (transaction.tier_id, transaction.class_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Tier {transaction.tier_id} does not belong to class {transaction.class_id}")
        
        # 데이터 삽입
        cursor.execute("""
            INSERT INTO assets 
            (name, cost, class_id, category_id, tier_id, date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (transaction.name, transaction.cost, transaction.class_id,
              transaction.category_id, transaction.tier_id, transaction.date,
              transaction.description))
        
        transaction_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, name, cost, class_id, category_id, tier_id, date, description,
                   created_at, updated_at
            FROM assets WHERE id = ?
        """, (transaction_id,))
        return dict(cursor.fetchone())

@router.get("/transactions", response_model=List[AssetTransactionDetail])
async def get_transactions(
    class_id: Optional[int] = Query(None, description="거래 분류 ID (1=지출, 2=수익, 3=저축)"),
    start_date: Optional[date_type] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date_type] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(None, description="카테고리 ID"),
    tier_id: Optional[int] = Query(None, description="티어 ID"),
    limit: int = Query(100, ge=1, le=1000, description="조회 제한"),
    offset: int = Query(0, ge=0, description="조회 시작 위치")
):
    """거래 목록 조회 (상세 정보 포함, 필터링 옵션)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                a.id, a.name, a.cost, a.date, a.description,
                ac.name as class_name, ac.display_name as class_display_name,
                cat.name as category_name, cat.display_name as category_display_name,
                t.tier_level, t.name as tier_name, t.display_name as tier_display_name,
                a.created_at, a.updated_at
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_categories cat ON a.category_id = cat.id
            JOIN asset_tiers t ON a.tier_id = t.id
            WHERE 1=1
        """
        params = []
        
        if class_id:
            query += " AND a.class_id = ?"
            params.append(class_id)
        if start_date:
            query += " AND a.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND a.date <= ?"
            params.append(end_date)
        if category_id:
            query += " AND a.category_id = ?"
            params.append(category_id)
        if tier_id:
            query += " AND a.tier_id = ?"
            params.append(tier_id)
        
        query += " ORDER BY a.date DESC, a.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.get("/transactions/{transaction_id}", response_model=AssetTransactionDetail)
async def get_transaction(transaction_id: int):
    """특정 거래 상세 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                a.id, a.name, a.cost, a.date, a.description,
                ac.name as class_name, ac.display_name as class_display_name,
                cat.name as category_name, cat.display_name as category_display_name,
                t.tier_level, t.name as tier_name, t.display_name as tier_display_name,
                a.created_at, a.updated_at
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_categories cat ON a.category_id = cat.id
            JOIN asset_tiers t ON a.tier_id = t.id
            WHERE a.id = ?
        """, (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Transaction with id {transaction_id} not found")
        return dict(row)

@router.put("/transactions/{transaction_id}", response_model=AssetTransaction)
async def update_transaction(transaction_id: int, transaction: AssetTransactionUpdate):
    """거래 정보 수정"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 거래 존재 확인
        cursor.execute("SELECT class_id FROM assets WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Transaction with id {transaction_id} not found")
        
        class_id = row[0]
        update_data = transaction.dict(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="No fields to update")
        
        # 카테고리/티어 변경 시 유효성 검사
        if 'category_id' in update_data:
            cursor.execute("SELECT id FROM asset_categories WHERE id = ? AND class_id = ?",
                          (update_data['category_id'], class_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Category does not belong to the same class")
        
        if 'tier_id' in update_data:
            cursor.execute("SELECT id FROM asset_tiers WHERE id = ? AND class_id = ?",
                          (update_data['tier_id'], class_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Tier does not belong to the same class")
        
        # 업데이트 쿼리 생성
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        set_clause += ", updated_at = CURRENT_TIMESTAMP"
        params = list(update_data.values()) + [transaction_id]
        
        cursor.execute(f"""
            UPDATE assets 
            SET {set_clause}
            WHERE id = ?
        """, params)
        
        cursor.execute("""
            SELECT id, name, cost, class_id, category_id, tier_id, date, description,
                   created_at, updated_at
            FROM assets WHERE id = ?
        """, (transaction_id,))
        return dict(cursor.fetchone())

@router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: int):
    """거래 삭제"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Transaction with id {transaction_id} not found")
        
        cursor.execute("DELETE FROM assets WHERE id = ?", (transaction_id,))
        return {
            "message": f"Transaction {transaction_id} deleted successfully",
            "deleted_transaction": dict(row)
        }

# ===== 통계 및 분석 API =====

@router.get("/statistics/period", response_model=PeriodSummary)
async def get_period_statistics(
    class_id: int = Query(..., description="거래 분류 ID (1=지출, 2=수익, 3=저축)"),
    start_date: Optional[date_type] = Query(None, description="시작 날짜"),
    end_date: Optional[date_type] = Query(None, description="종료 날짜")
):
    """기간별 통계 (카테고리별, 티어별 집계)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # class 정보 조회
        cursor.execute("SELECT name, display_name FROM asset_classes WHERE id = ?", (class_id,))
        class_row = cursor.fetchone()
        if not class_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Class with id {class_id} not found")
        
        where_clause = "WHERE a.class_id = ?"
        params = [class_id]
        
        if start_date:
            where_clause += " AND a.date >= ?"
            params.append(start_date)
        if end_date:
            where_clause += " AND a.date <= ?"
            params.append(end_date)
        
        # 전체 통계
        cursor.execute(f"""
            SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total
            FROM assets a
            {where_clause}
        """, params)
        total_row = cursor.fetchone()
        
        # 카테고리별 통계
        cursor.execute(f"""
            SELECT 
                cat.id, cat.name, cat.display_name,
                COUNT(*) as count, SUM(a.cost) as total
            FROM assets a
            JOIN asset_categories cat ON a.category_id = cat.id
            {where_clause}
            GROUP BY cat.id
            ORDER BY total DESC
        """, params)
        category_rows = cursor.fetchall()
        
        # 티어별 통계
        cursor.execute(f"""
            SELECT 
                t.id, t.tier_level, t.name, t.display_name,
                COUNT(*) as count, SUM(a.cost) as total
            FROM assets a
            JOIN asset_tiers t ON a.tier_id = t.id
            {where_clause}
            GROUP BY t.id
            ORDER BY t.tier_level
        """, params)
        tier_rows = cursor.fetchall()
        
        return {
            "class_name": class_row[0],
            "class_display_name": class_row[1],
            "total_count": total_row[0],
            "total_cost": total_row[1],
            "by_category": [
                {
                    "category_id": row[0],
                    "category_name": row[1],
                    "category_display_name": row[2],
                    "count": row[3],
                    "total_cost": row[4]
                }
                for row in category_rows
            ],
            "by_tier": [
                {
                    "tier_id": row[0],
                    "tier_level": row[1],
                    "tier_name": row[2],
                    "tier_display_name": row[3],
                    "count": row[4],
                    "total_cost": row[5]
                }
                for row in tier_rows
            ]
        }

@router.get("/statistics/monthly", response_model=MonthlyStatistics)
async def get_monthly_statistics(
    year: int = Query(..., description="연도"),
    month: int = Query(..., ge=1, le=12, description="월")
):
    """월별 통합 통계 (지출/수익/저축 모두)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 지출 합계
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0)
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            WHERE ac.name = 'spend'
            AND strftime('%Y', a.date) = ?
            AND strftime('%m', a.date) = ?
        """, (str(year), f"{month:02d}"))
        spend_total = cursor.fetchone()[0]
        
        # 수익 합계
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0)
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            WHERE ac.name = 'earn'
            AND strftime('%Y', a.date) = ?
            AND strftime('%m', a.date) = ?
        """, (str(year), f"{month:02d}"))
        earn_total = cursor.fetchone()[0]
        
        # 저축 합계
        cursor.execute("""
            SELECT COALESCE(SUM(cost), 0)
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            WHERE ac.name = 'save'
            AND strftime('%Y', a.date) = ?
            AND strftime('%m', a.date) = ?
        """, (str(year), f"{month:02d}"))
        save_total = cursor.fetchone()[0]
        
        return {
            "year": year,
            "month": month,
            "spend_total": spend_total,
            "earn_total": earn_total,
            "save_total": save_total,
            "balance": earn_total - spend_total - save_total
        }

@router.get("/search")
async def search_transactions(
    query: str = Query(..., min_length=1, description="검색어 (거래명 또는 설명)"),
    class_id: Optional[int] = Query(None, description="거래 분류 ID로 필터링")
):
    """거래 검색 (이름 또는 설명)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        search_query = f"%{query}%"
        where_clause = "WHERE (a.name LIKE ? OR a.description LIKE ?)"
        params = [search_query, search_query]
        
        if class_id:
            where_clause += " AND a.class_id = ?"
            params.append(class_id)
        
        cursor.execute(f"""
            SELECT 
                a.id, a.name, a.cost, a.date, a.description,
                ac.name as class_name, ac.display_name as class_display_name,
                cat.name as category_name, cat.display_name as category_display_name,
                t.tier_level, t.name as tier_name, t.display_name as tier_display_name,
                a.created_at, a.updated_at
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_categories cat ON a.category_id = cat.id
            JOIN asset_tiers t ON a.tier_id = t.id
            {where_clause}
            ORDER BY a.date DESC
            LIMIT 50
        """, params)
        
        rows = cursor.fetchall()
        return {
            "query": query,
            "total_results": len(rows),
            "results": [dict(row) for row in rows]
        }
