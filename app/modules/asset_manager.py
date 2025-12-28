from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime, date as date_type
from models.asset import (
    AssetClass, AssetClassCreate,
    AssetCategory, AssetCategoryCreate,
    AssetSubCategory, AssetSubCategoryCreate,
    AssetTier, AssetTierCreate,
    AssetTransaction, AssetTransactionCreate, AssetTransactionUpdate,
    AssetTransactionDetail, CategoryStatistics, TierStatistics,
    PeriodSummary, MonthlyStatistics,
    AssetTag, AssetTagCreate, AssetTagUpdate,
    AssetBudget, AssetBudgetCreate, AssetBudgetUpdate
)
from utils.database import get_db_connection

# 라우터 생성
router = APIRouter(
    prefix="/asset-manager",
    tags=["Asset Manager"],
    responses={404: {"description": "Not found"}}
)

# ===== 헬퍼 함수 =====

def get_or_create_tags(cursor, tag_names: List[str]) -> List[int]:
    """태그 이름 리스트를 받아서 태그 ID 리스트 반환 (없으면 생성)"""
    tag_ids = []
    
    for tag_name in tag_names:
        tag_name = tag_name.strip()
        if not tag_name:
            continue
        
        # 기존 태그 확인
        cursor.execute("SELECT id FROM asset_tags WHERE name = ?", (tag_name,))
        row = cursor.fetchone()
        
        if row:
            tag_ids.append(row[0])
        else:
            # 새 태그 생성
            cursor.execute("""
                INSERT INTO asset_tags (name, description, color, is_active)
                VALUES (?, ?, ?, ?)
            """, (tag_name, f"자동 생성된 태그: {tag_name}", "#6366f1", True))
            tag_ids.append(cursor.lastrowid)
    
    return tag_ids

def sync_asset_tags(cursor, asset_id: int, tag_names: List[str]):
    """거래의 태그 동기화 (기존 관계 삭제 후 새로 생성)"""
    # 기존 관계 삭제 및 사용 횟수 감소
    cursor.execute("""
        UPDATE asset_tags 
        SET usage_count = usage_count - 1
        WHERE id IN (
            SELECT tag_id FROM asset_tag_relations WHERE asset_id = ?
        )
    """, (asset_id,))
    
    cursor.execute("DELETE FROM asset_tag_relations WHERE asset_id = ?", (asset_id,))
    
    # 새 태그 생성/조회
    if tag_names:
        tag_ids = get_or_create_tags(cursor, tag_names)
        
        # 새 관계 생성 및 사용 횟수 증가
        for tag_id in tag_ids:
            cursor.execute("""
                INSERT INTO asset_tag_relations (asset_id, tag_id)
                VALUES (?, ?)
            """, (asset_id, tag_id))
            
            cursor.execute("""
                UPDATE asset_tags 
                SET usage_count = usage_count + 1
                WHERE id = ?
            """, (tag_id,))

def get_asset_tags(cursor, asset_id: int) -> List[str]:
    """거래의 태그 이름 리스트 조회"""
    cursor.execute("""
        SELECT t.name
        FROM asset_tags t
        JOIN asset_tag_relations r ON t.id = r.tag_id
        WHERE r.asset_id = ?
        ORDER BY t.name
    """, (asset_id,))
    
    return [row[0] for row in cursor.fetchall()]

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
                SELECT id, class_id, name, display_name, tier_id, description, 
                       is_active, sort_order, created_at, default_budget
                FROM asset_categories
                WHERE class_id = ? AND is_active = TRUE
                ORDER BY sort_order, id
            """, (class_id,))
        else:
            cursor.execute("""
                SELECT id, class_id, name, display_name, tier_id, description, 
                       is_active, sort_order, created_at, default_budget
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
        
        # 기존에 같은 이름의 카테고리가 있는지 확인 (비활성화된 것 포함)
        cursor.execute("""
            SELECT id, is_active FROM asset_categories 
            WHERE class_id = ? AND name = ?
        """, (category.class_id, category.name))
        existing_category = cursor.fetchone()

        if existing_category:
            category_id = existing_category[0]
            # 기존 카테고리 업데이트 및 활성화
            cursor.execute("""
                UPDATE asset_categories 
                SET display_name = ?, tier_id = ?, description = ?, is_active = TRUE, sort_order = ?, default_budget = ?
                WHERE id = ?
            """, (category.display_name, category.tier_id, category.description, category.sort_order, category.default_budget, category_id))
        else:
            # 새 카테고리 생성
            cursor.execute("""
                INSERT INTO asset_categories 
                (class_id, name, display_name, tier_id, description, is_active, sort_order, default_budget)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (category.class_id, category.name, category.display_name, category.tier_id,
                  category.description, category.is_active, category.sort_order, category.default_budget))
            category_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT id, class_id, name, display_name, tier_id, description, 
                   is_active, sort_order, created_at, default_budget
            FROM asset_categories WHERE id = ?
        """, (category_id,))
        return dict(cursor.fetchone())

# ===== Sub Categories (하위 카테고리) API =====

@router.get("/sub-categories", response_model=List[AssetSubCategory])
async def get_sub_categories(
    category_id: Optional[int] = Query(None, description="상위 카테고리 ID로 필터링")
):
    """하위 카테고리 목록 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if category_id:
            cursor.execute("""
                SELECT id, category_id, name, tier_id, is_active, created_at
                FROM asset_sub_categories
                WHERE category_id = ? AND is_active = TRUE
                ORDER BY name
            """, (category_id,))
        else:
            cursor.execute("""
                SELECT id, category_id, name, tier_id, is_active, created_at
                FROM asset_sub_categories
                WHERE is_active = TRUE
                ORDER BY category_id, name
            """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/sub-categories", response_model=AssetSubCategory, status_code=status.HTTP_201_CREATED)
async def create_sub_category(sub_category: AssetSubCategoryCreate):
    """새 하위 카테고리 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # category_id 유효성 검사
        cursor.execute("SELECT id FROM asset_categories WHERE id = ?", (sub_category.category_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {sub_category.category_id} not found"
            )
            
        # tier_id 유효성 검사
        cursor.execute("SELECT id FROM asset_tiers WHERE id = ?", (sub_category.tier_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tier with id {sub_category.tier_id} not found"
            )
        
        cursor.execute("""
            INSERT INTO asset_sub_categories 
            (category_id, name, tier_id, is_active)
            VALUES (?, ?, ?, ?)
        """, (sub_category.category_id, sub_category.name, sub_category.tier_id, sub_category.is_active))
        
        sub_category_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, category_id, name, tier_id, is_active, created_at
            FROM asset_sub_categories WHERE id = ?
        """, (sub_category_id,))
        return dict(cursor.fetchone())

@router.delete("/sub-categories/{sub_category_id}")
async def delete_sub_category(sub_category_id: int):
    """하위 카테고리 삭제 (비활성화)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 존재 확인
        cursor.execute("SELECT * FROM asset_sub_categories WHERE id = ?", (sub_category_id,))
        sub_category = cursor.fetchone()
        if not sub_category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sub Category with id {sub_category_id} not found"
            )
        
        # 사용 중인지 확인
        cursor.execute("SELECT COUNT(*) FROM assets WHERE sub_category_id = ?", (sub_category_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("UPDATE asset_sub_categories SET is_active = FALSE WHERE id = ?", (sub_category_id,))
            message = f"Sub Category {sub_category_id} deactivated (has {count} transactions)"
        else:
            cursor.execute("DELETE FROM asset_sub_categories WHERE id = ?", (sub_category_id,))
            message = f"Sub Category {sub_category_id} deleted permanently"
            
        return {"message": message}

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

@router.delete("/categories/{category_id}")
async def delete_category(category_id: int):
    """카테고리 삭제 (비활성화)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 카테고리 존재 확인
        cursor.execute("SELECT * FROM asset_categories WHERE id = ?", (category_id,))
        category = cursor.fetchone()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )
        
        # 해당 카테고리를 사용하는 거래가 있는지 확인
        cursor.execute("SELECT COUNT(*) FROM assets WHERE category_id = ?", (category_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # 거래가 있으면 비활성화만
            cursor.execute("""
                UPDATE asset_categories 
                SET is_active = FALSE 
                WHERE id = ?
            """, (category_id,))
            message = f"Category {category_id} deactivated (has {count} transactions)"
        else:
            # 거래가 없으면 완전 삭제
            cursor.execute("DELETE FROM asset_categories WHERE id = ?", (category_id,))
            message = f"Category {category_id} deleted permanently"
        
        return {
            "message": message,
            "category": dict(category)
        }

@router.delete("/tiers/{tier_id}")
async def delete_tier(tier_id: int):
    """티어 삭제 (비활성화)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 티어 존재 확인
        cursor.execute("SELECT * FROM asset_tiers WHERE id = ?", (tier_id,))
        tier = cursor.fetchone()
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tier with id {tier_id} not found"
            )
        
        # 해당 티어를 사용하는 거래가 있는지 확인
        cursor.execute("SELECT COUNT(*) FROM assets WHERE tier_id = ?", (tier_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # 거래가 있으면 비활성화만
            cursor.execute("""
                UPDATE asset_tiers 
                SET is_active = FALSE 
                WHERE id = ?
            """, (tier_id,))
            message = f"Tier {tier_id} deactivated (has {count} transactions)"
        else:
            # 거래가 없으면 완전 삭제
            cursor.execute("DELETE FROM asset_tiers WHERE id = ?", (tier_id,))
            message = f"Tier {tier_id} deleted permanently"
        
        return {
            "message": message,
            "tier": dict(tier)
        }

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
        
        # 카테고리 확인
        cursor.execute("SELECT id FROM asset_categories WHERE id = ? AND class_id = ?",
                      (transaction.category_id, transaction.class_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Category {transaction.category_id} does not belong to class {transaction.class_id}")
        
        # 하위 카테고리 확인 및 티어 결정
        final_tier_id = transaction.tier_id
        
        if transaction.sub_category_id:
            cursor.execute("SELECT id, tier_id FROM asset_sub_categories WHERE id = ? AND category_id = ?",
                          (transaction.sub_category_id, transaction.category_id))
            sub_cat_row = cursor.fetchone()
            if not sub_cat_row:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Sub Category {transaction.sub_category_id} does not belong to category {transaction.category_id}")
            
            # 하위 카테고리의 티어 사용 (명시적 입력이 없으면)
            if final_tier_id is None:
                final_tier_id = sub_cat_row[1]
        else:
            # 하위 카테고리가 없으면 카테고리의 기본 티어 사용 (하위 호환성)
            cursor.execute("SELECT tier_id FROM asset_categories WHERE id = ?", (transaction.category_id,))
            cat_row = cursor.fetchone()
            if final_tier_id is None and cat_row:
                final_tier_id = cat_row[0]

        if final_tier_id is None:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="Tier ID is required and no default tier found")

        # 티어 유효성 검사
        cursor.execute("SELECT id FROM asset_tiers WHERE id = ? AND class_id = ?",
                      (final_tier_id, transaction.class_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail=f"Tier {final_tier_id} does not belong to class {transaction.class_id}")
        
        # 데이터 삽입
        cursor.execute("""
            INSERT INTO assets 
            (name, cost, class_id, category_id, sub_category_id, tier_id, date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (transaction.name, transaction.cost, transaction.class_id,
              transaction.category_id, transaction.sub_category_id, final_tier_id, transaction.date,
              transaction.description))
        
        transaction_id = cursor.lastrowid
        
        # 태그 처리 (자동 생성 포함)
        if transaction.tags:
            sync_asset_tags(cursor, transaction_id, transaction.tags)
        
        cursor.execute("""
            SELECT id, name, cost, class_id, category_id, sub_category_id, tier_id, date, description,
                   created_at, updated_at
            FROM assets WHERE id = ?
        """, (transaction_id,))
        row = dict(cursor.fetchone())
        
        # 태그 조회
        row['tags'] = get_asset_tags(cursor, transaction_id)
        
        return row

@router.get("/transactions/unclassified", response_model=List[AssetTransactionDetail])
async def get_unclassified_transactions():
    """분류되지 않은 거래 내역 조회 (sub_category_id가 NULL인 경우)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                t.id, t.name, t.cost, t.date, t.description, t.created_at, t.updated_at,
                c.id as class_id, c.name as class_name, c.display_name as class_display_name,
                cat.id as category_id, cat.name as category_name, cat.display_name as category_display_name,
                sub.id as sub_category_id, sub.name as sub_category_name,
                tr.id as tier_id, tr.name as tier_name, tr.display_name as tier_display_name, tr.tier_level
            FROM assets t
            JOIN asset_classes c ON t.class_id = c.id
            JOIN asset_categories cat ON t.category_id = cat.id
            LEFT JOIN asset_sub_categories sub ON t.sub_category_id = sub.id
            JOIN asset_tiers tr ON t.tier_id = tr.id
            WHERE t.sub_category_id IS NULL
            ORDER BY t.date DESC, t.id DESC
        """)
        
        transactions = []
        rows = cursor.fetchall()
        
        for row in rows:
            row_dict = dict(row)
            # 태그 조회
            row_dict['tags'] = get_asset_tags(cursor, row_dict['id'])
            transactions.append(row_dict)
            
        return transactions

@router.get("/transactions", response_model=List[AssetTransactionDetail])
async def get_transactions(
    class_id: Optional[int] = Query(None, description="거래 분류 ID (1=지출, 2=수익, 3=저축)"),
    start_date: Optional[date_type] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[date_type] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(None, description="카테고리 ID"),
    sub_category_id: Optional[int] = Query(None, description="하위 카테고리 ID"),
    tier_id: Optional[int] = Query(None, description="티어 ID"),
    limit: int = Query(100, ge=1, le=10000, description="조회 제한"),
    offset: int = Query(0, ge=0, description="조회 시작 위치")
):
    """거래 목록 조회 (상세 정보 포함, 필터링 옵션)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                a.id, a.name, a.cost, a.date, a.description,
                a.class_id, ac.name as class_name, ac.display_name as class_display_name,
                a.category_id, cat.name as category_name, cat.display_name as category_display_name,
                a.sub_category_id, sc.name as sub_category_name,
                a.tier_id, t.tier_level, t.name as tier_name, t.display_name as tier_display_name,
                a.created_at, a.updated_at
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_categories cat ON a.category_id = cat.id
            LEFT JOIN asset_sub_categories sc ON a.sub_category_id = sc.id
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
        if sub_category_id:
            query += " AND a.sub_category_id = ?"
            params.append(sub_category_id)
        if tier_id:
            query += " AND a.tier_id = ?"
            params.append(tier_id)
        
        query += " ORDER BY a.date DESC, a.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # 각 거래의 태그 조회
        result = []
        for row in rows:
            row_dict = dict(row)
            row_dict['tags'] = get_asset_tags(cursor, row_dict['id'])
            result.append(row_dict)
        
        return result

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
                sc.name as sub_category_name,
                t.tier_level, t.name as tier_name, t.display_name as tier_display_name,
                a.created_at, a.updated_at
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_categories cat ON a.category_id = cat.id
            LEFT JOIN asset_sub_categories sc ON a.sub_category_id = sc.id
            JOIN asset_tiers t ON a.tier_id = t.id
            WHERE a.id = ?
        """, (transaction_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                              detail=f"Transaction with id {transaction_id} not found")
        
        row_dict = dict(row)
        # 태그 조회
        row_dict['tags'] = get_asset_tags(cursor, transaction_id)
        
        return row_dict

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
        
        # 태그는 따로 처리
        tags = update_data.pop('tags', None)
        
        if not update_data and tags is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                              detail="No fields to update")
        
        # 카테고리/하위 카테고리/티어 변경 시 유효성 검사 및 티어 자동 업데이트
        current_category_id = update_data.get('category_id')
        if not current_category_id:
            # 업데이트 데이터에 없으면 기존 값 조회
            cursor.execute("SELECT category_id FROM assets WHERE id = ?", (transaction_id,))
            current_category_id = cursor.fetchone()[0]

        if 'category_id' in update_data:
            cursor.execute("SELECT id FROM asset_categories WHERE id = ? AND class_id = ?",
                          (update_data['category_id'], class_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Category does not belong to the same class")
            
            # 카테고리가 바뀌면 하위 카테고리 초기화 (명시적 업데이트가 없으면)
            if 'sub_category_id' not in update_data:
                update_data['sub_category_id'] = None
                
        if 'sub_category_id' in update_data and update_data['sub_category_id'] is not None:
            cursor.execute("SELECT id, tier_id FROM asset_sub_categories WHERE id = ? AND category_id = ?",
                          (update_data['sub_category_id'], current_category_id))
            sub_cat_row = cursor.fetchone()
            if not sub_cat_row:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Sub Category does not belong to the category")
            
            # 하위 카테고리가 변경되면 티어도 자동 업데이트 (명시적 업데이트가 없으면)
            if 'tier_id' not in update_data:
                update_data['tier_id'] = sub_cat_row[1]
        
        # 하위 카테고리가 없고 카테고리만 변경된 경우, 카테고리의 기본 티어 사용 (하위 호환성)
        if 'category_id' in update_data and 'sub_category_id' not in update_data and 'tier_id' not in update_data:
             cursor.execute("SELECT tier_id FROM asset_categories WHERE id = ?", (update_data['category_id'],))
             cat_row = cursor.fetchone()
             if cat_row and cat_row[0]:
                 update_data['tier_id'] = cat_row[0]

        if 'tier_id' in update_data:
            cursor.execute("SELECT id FROM asset_tiers WHERE id = ? AND class_id = ?",
                          (update_data['tier_id'], class_id))
            if not cursor.fetchone():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                  detail=f"Tier does not belong to the same class")
        
        # 기본 필드 업데이트
        if update_data:
            set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
            set_clause += ", updated_at = CURRENT_TIMESTAMP"
            params = list(update_data.values()) + [transaction_id]
            
            cursor.execute(f"""
                UPDATE assets 
                SET {set_clause}
                WHERE id = ?
            """, params)
        
        # 태그 업데이트 (자동 생성 포함)
        if tags is not None:
            sync_asset_tags(cursor, transaction_id, tags)
        
        cursor.execute("""
            SELECT id, name, cost, class_id, category_id, sub_category_id, tier_id, date, description,
                   created_at, updated_at
            FROM assets WHERE id = ?
        """, (transaction_id,))
        
        row_dict = dict(cursor.fetchone())
        # 태그 조회
        row_dict['tags'] = get_asset_tags(cursor, transaction_id)
        
        return row_dict

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

        # 지출 티어별 합계
        cursor.execute("""
            SELECT t.name, t.display_name, COALESCE(SUM(a.cost), 0) as total
            FROM assets a
            JOIN asset_classes ac ON a.class_id = ac.id
            JOIN asset_tiers t ON a.tier_id = t.id
            WHERE ac.name = 'spend'
            AND strftime('%Y', a.date) = ?
            AND strftime('%m', a.date) = ?
            GROUP BY t.id
            ORDER BY t.sort_order
        """, (str(year), f"{month:02d}"))
        spend_by_tier = [dict(row) for row in cursor.fetchall()]
        
        return {
            "year": year,
            "month": month,
            "spend_total": spend_total,
            "earn_total": earn_total,
            "save_total": save_total,
            "balance": earn_total - spend_total - save_total,
            "spend_by_tier": spend_by_tier
        }

# ===== Period Comparison (기간별 비교) API =====

@router.get("/statistics/period-comparison")
async def get_period_comparison(
    unit: str = Query("week", description="비교 단위: day, week, month, year"),
    periods: int = Query(4, ge=1, le=8, description="비교할 기간 수 (1~8)"),
    end_date: Optional[str] = Query(None, description="기준 종료일 (YYYY-MM-DD), 미지정시 오늘")
):
    """기간별 비교 통계 조회"""
    from datetime import timedelta
    from models.asset import PeriodUnit, PeriodComparison, PeriodData
    
    # 단위 검증
    try:
        period_unit = PeriodUnit(unit)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid unit: {unit}. Must be one of: day, week, month, year"
        )
    
    # 종료일 파싱
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        end = datetime.now().date()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        period_data_list = []
        
        for i in range(periods):
            # 각 기간의 시작/종료 계산
            if period_unit == PeriodUnit.day:
                period_end = end - timedelta(days=i)
                period_start = period_end
                label = period_end.strftime("%Y-%m-%d")
                
            elif period_unit == PeriodUnit.week:
                # 주 단위: 월요일~일요일
                period_end = end - timedelta(weeks=i)
                weekday = period_end.weekday()  # 0=월요일, 6=일요일
                period_end = period_end - timedelta(days=weekday) + timedelta(days=6)  # 일요일
                period_start = period_end - timedelta(days=6)  # 월요일
                label = f"{period_start.strftime('%m/%d')}~{period_end.strftime('%m/%d')}"
                
            elif period_unit == PeriodUnit.month:
                # 월 단위
                year = end.year
                month = end.month - i
                while month < 1:
                    month += 12
                    year -= 1
                
                # 해당 월의 첫날과 마지막날
                period_start = date_type(year, month, 1)
                if month == 12:
                    period_end = date_type(year, 12, 31)
                else:
                    period_end = date_type(year, month + 1, 1) - timedelta(days=1)
                label = f"{year}년 {month}월"
                
            else:  # year
                year = end.year - i
                period_start = date_type(year, 1, 1)
                period_end = date_type(year, 12, 31)
                label = f"{year}년"
            
            # 해당 기간의 거래 조회
            cursor.execute("""
                SELECT 
                    ac.name as class_name,
                    SUM(a.cost) as total,
                    COUNT(*) as count
                FROM assets a
                JOIN asset_classes ac ON a.class_id = ac.id
                WHERE a.date BETWEEN ? AND ?
                GROUP BY ac.name
            """, (period_start.strftime("%Y-%m-%d"), period_end.strftime("%Y-%m-%d")))
            
            class_totals = {}
            total_count = 0
            for row in cursor.fetchall():
                class_totals[row[0]] = row[1]
                total_count += row[2]
            
            spend_total = class_totals.get('spend', 0.0)
            earn_total = class_totals.get('earn', 0.0)
            save_total = class_totals.get('save', 0.0)
            balance = earn_total - spend_total - save_total
            
            # 카테고리별 통계 (지출만)
            cursor.execute("""
                SELECT 
                    cat.id,
                    cat.name,
                    cat.display_name,
                    COUNT(*) as count,
                    SUM(a.cost) as total
                FROM assets a
                JOIN asset_categories cat ON a.category_id = cat.id
                JOIN asset_classes ac ON a.class_id = ac.id
                WHERE a.date BETWEEN ? AND ?
                  AND ac.name = 'spend'
                GROUP BY cat.id
                ORDER BY total DESC
            """, (period_start.strftime("%Y-%m-%d"), period_end.strftime("%Y-%m-%d")))
            
            by_category = []
            for row in cursor.fetchall():
                by_category.append({
                    "category_id": row[0],
                    "category_name": row[1],
                    "category_display_name": row[2],
                    "count": row[3],
                    "total_cost": row[4]
                })
            
            # 상위 거래 5건 (지출액 기준)
            cursor.execute("""
                SELECT 
                    a.id, a.name, a.cost, a.class_id, a.category_id, 
                    a.tier_id, a.date, a.description,
                    ac.name as class_name, ac.display_name as class_display_name,
                    cat.name as category_name, cat.display_name as category_display_name,
                    t.tier_level, t.name as tier_name, t.display_name as tier_display_name
                FROM assets a
                JOIN asset_classes ac ON a.class_id = ac.id
                JOIN asset_categories cat ON a.category_id = cat.id
                JOIN asset_tiers t ON a.tier_id = t.id
                WHERE a.date BETWEEN ? AND ?
                  AND ac.name = 'spend'
                ORDER BY a.cost DESC
                LIMIT 5
            """, (period_start.strftime("%Y-%m-%d"), period_end.strftime("%Y-%m-%d")))
            
            top_transactions = []
            for row in cursor.fetchall():
                # 태그 조회
                cursor.execute("""
                    SELECT at.name
                    FROM asset_tags at
                    JOIN asset_tag_relations atr ON at.id = atr.tag_id
                    WHERE atr.asset_id = ?
                """, (row[0],))
                tags = [t[0] for t in cursor.fetchall()]
                
                top_transactions.append({
                    "id": row[0],
                    "name": row[1],
                    "cost": row[2],
                    "class_id": row[3],
                    "category_id": row[4],
                    "tier_id": row[5],
                    "date": row[6],
                    "description": row[7],
                    "class_name": row[8],
                    "class_display_name": row[9],
                    "category_name": row[10],
                    "category_display_name": row[11],
                    "tier_level": row[12],
                    "tier_name": row[13],
                    "tier_display_name": row[14],
                    "tags": tags
                })
            
            period_data_list.append({
                "period_label": label,
                "start_date": period_start,
                "end_date": period_end,
                "spend_total": spend_total,
                "earn_total": earn_total,
                "save_total": save_total,
                "balance": balance,
                "transaction_count": total_count,
                "by_category": by_category,
                "top_transactions": top_transactions
            })
        
        # 평균 및 트렌드 계산
        if period_data_list:
            avg_spend = sum(p["spend_total"] for p in period_data_list) / len(period_data_list)
            avg_earn = sum(p["earn_total"] for p in period_data_list) / len(period_data_list)
            avg_save = sum(p["save_total"] for p in period_data_list) / len(period_data_list)
            
            # 트렌드: 최근 기간 vs 이전 기간들 평균
            if len(period_data_list) > 1:
                recent = period_data_list[0]
                prev_avg_spend = sum(p["spend_total"] for p in period_data_list[1:]) / (len(period_data_list) - 1)
                prev_avg_earn = sum(p["earn_total"] for p in period_data_list[1:]) / (len(period_data_list) - 1)
                
                spend_trend = ((recent["spend_total"] - prev_avg_spend) / prev_avg_spend * 100) if prev_avg_spend > 0 else 0
                earn_trend = ((recent["earn_total"] - prev_avg_earn) / prev_avg_earn * 100) if prev_avg_earn > 0 else 0
            else:
                spend_trend = 0
                earn_trend = 0
        else:
            avg_spend = avg_earn = avg_save = 0
            spend_trend = earn_trend = 0
        
        return {
            "unit": unit,
            "periods": period_data_list,
            "avg_spend": avg_spend,
            "avg_earn": avg_earn,
            "avg_save": avg_save,
            "spend_trend": spend_trend,
            "earn_trend": earn_trend
        }

# ===== Tags (태그) API =====

@router.get("/tags", response_model=List[AssetTag])
async def get_all_tags(active_only: bool = Query(True, description="활성 태그만 조회")):
    """모든 태그 목록 조회"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("""
                SELECT id, name, description, color, is_active, usage_count, created_at
                FROM asset_tags
                WHERE is_active = TRUE
                ORDER BY usage_count DESC, name
            """)
        else:
            cursor.execute("""
                SELECT id, name, description, color, is_active, usage_count, created_at
                FROM asset_tags
                ORDER BY usage_count DESC, name
            """)
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

@router.post("/tags", response_model=AssetTag, status_code=status.HTTP_201_CREATED)
async def create_tag(tag: AssetTagCreate):
    """새 태그 생성"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 중복 체크
        cursor.execute("SELECT id FROM asset_tags WHERE name = ?", (tag.name,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{tag.name}' already exists"
            )
        
        cursor.execute("""
            INSERT INTO asset_tags (name, description, color, is_active)
            VALUES (?, ?, ?, ?)
        """, (tag.name, tag.description, tag.color, tag.is_active))
        
        tag_id = cursor.lastrowid
        cursor.execute("""
            SELECT id, name, description, color, is_active, usage_count, created_at
            FROM asset_tags WHERE id = ?
        """, (tag_id,))
        
        return dict(cursor.fetchone())

@router.put("/tags/{tag_id}", response_model=AssetTag)
async def update_tag(tag_id: int, tag: AssetTagUpdate):
    """태그 정보 수정"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 태그 존재 확인
        cursor.execute("SELECT id FROM asset_tags WHERE id = ?", (tag_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id {tag_id} not found"
            )
        
        update_data = tag.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # 이름 변경 시 중복 체크
        if 'name' in update_data:
            cursor.execute("SELECT id FROM asset_tags WHERE name = ? AND id != ?", 
                          (update_data['name'], tag_id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tag name '{update_data['name']}' already exists"
                )
        
        # 업데이트 쿼리 생성
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        params = list(update_data.values()) + [tag_id]
        
        cursor.execute(f"""
            UPDATE asset_tags 
            SET {set_clause}
            WHERE id = ?
        """, params)
        
        cursor.execute("""
            SELECT id, name, description, color, is_active, usage_count, created_at
            FROM asset_tags WHERE id = ?
        """, (tag_id,))
        
        return dict(cursor.fetchone())

@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int, force: bool = Query(False, description="강제 삭제")):
    """태그 삭제 (또는 비활성화)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 태그 존재 확인
        cursor.execute("SELECT * FROM asset_tags WHERE id = ?", (tag_id,))
        tag = cursor.fetchone()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tag with id {tag_id} not found"
            )
        
        # 사용 중인 거래 개수 확인
        cursor.execute("""
            SELECT COUNT(*) FROM asset_tag_relations WHERE tag_id = ?
        """, (tag_id,))
        usage_count = cursor.fetchone()[0]
        
        if usage_count > 0 and not force:
            # 사용 중이면 비활성화만
            cursor.execute("""
                UPDATE asset_tags 
                SET is_active = FALSE 
                WHERE id = ?
            """, (tag_id,))
            message = f"Tag '{tag[1]}' deactivated ({usage_count} transactions using it)"
        else:
            # 사용하지 않거나 강제 삭제 시
            cursor.execute("DELETE FROM asset_tag_relations WHERE tag_id = ?", (tag_id,))
            cursor.execute("DELETE FROM asset_tags WHERE id = ?", (tag_id,))
            message = f"Tag '{tag[1]}' deleted permanently"
        
        return {
            "message": message,
            "tag": dict(tag)
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

# ===== Budget (예산) API =====

def calculate_budget_for_month(cursor, category_id: int, year: int, month: int) -> dict:
    """특정 월의 예산을 계산하고 DB에 저장 (이월 로직 포함)"""
    # 1. 이미 존재하는지 확인
    cursor.execute("""
        SELECT id, category_id, year, month, budget_amount, rollover_amount, created_at, updated_at
        FROM asset_budgets
        WHERE category_id = ? AND year = ? AND month = ?
    """, (category_id, year, month))
    existing = cursor.fetchone()
    if existing:
        return dict(existing)

    # 2. 카테고리 기본 정보 조회
    cursor.execute("SELECT default_budget FROM asset_categories WHERE id = ?", (category_id,))
    category = cursor.fetchone()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    default_budget = category['default_budget'] or 0

    # 3. 이전 달 정보 조회 (이월 계산용)
    prev_year = year
    prev_month = month - 1
    if prev_month == 0:
        prev_year -= 1
        prev_month = 12
    
    rollover_amount = 0
    
    # 이전 달 예산 조회
    cursor.execute("""
        SELECT budget_amount
        FROM asset_budgets
        WHERE category_id = ? AND year = ? AND month = ?
    """, (category_id, prev_year, prev_month))
    prev_budget_row = cursor.fetchone()
    
    if prev_budget_row:
        prev_budget = prev_budget_row['budget_amount']
        
        # 이전 달 지출 조회
        start_date = f"{prev_year}-{prev_month:02d}-01"
        if prev_month == 12:
            end_date = f"{prev_year+1}-01-01"
        else:
            end_date = f"{prev_year}-{prev_month+1:02d}-01"
            
        cursor.execute("""
            SELECT SUM(cost) 
            FROM assets 
            WHERE category_id = ? AND date >= ? AND date < ?
        """, (category_id, start_date, end_date))
        prev_spent_row = cursor.fetchone()
        prev_spent = prev_spent_row[0] if prev_spent_row and prev_spent_row[0] else 0
        
        remaining = prev_budget - prev_spent
        if remaining > 0:
            rollover_amount = remaining * 0.5
    
    # 4. 새 예산 계산
    new_budget = default_budget + rollover_amount
    
    # 이월외는 예산이 많더라도 최대 2N원을 넘어가지 않게 해줘
    if default_budget > 0:
        max_cap = default_budget * 2
        if new_budget > max_cap:
            new_budget = max_cap
    elif default_budget == 0 and rollover_amount > 0:
        # 기본 예산이 0인 경우, 이월금이 있어도 예산은 0이 됨 (2N = 0)
        # 하지만 사용자가 의도적으로 0으로 설정했을 수 있으므로, 
        # 이월금만이라도 유지할지, 아니면 0으로 날릴지 결정해야 함.
        # 요구사항: "최대 2N원을 넘어가지 않게 해줘" -> N=0이면 0이어야 함.
        new_budget = 0
            
    # 5. DB 저장
    cursor.execute("""
        INSERT INTO asset_budgets (category_id, year, month, budget_amount, rollover_amount)
        VALUES (?, ?, ?, ?, ?)
    """, (category_id, year, month, new_budget, rollover_amount))
    
    new_id = cursor.lastrowid
    
    cursor.execute("""
        SELECT id, category_id, year, month, budget_amount, rollover_amount, created_at, updated_at
        FROM asset_budgets WHERE id = ?
    """, (new_id,))
    return dict(cursor.fetchone())

@router.get("/budgets", response_model=List[AssetBudget])
async def get_budgets(
    year: int,
    month: int,
    class_id: Optional[int] = Query(None, description="거래 분류 ID로 필터링")
):
    """특정 월의 모든 카테고리 예산 조회 (없으면 자동 생성)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 대상 카테고리 조회
        if class_id:
            cursor.execute("SELECT id FROM asset_categories WHERE class_id = ? AND is_active = TRUE", (class_id,))
        else:
            cursor.execute("SELECT id FROM asset_categories WHERE is_active = TRUE")
            
        categories = cursor.fetchall()
        
        budgets = []
        for cat in categories:
            budget = calculate_budget_for_month(cursor, cat['id'], year, month)
            budgets.append(budget)
            
        return budgets

@router.put("/budgets/{category_id}/{year}/{month}", response_model=AssetBudget)
async def update_budget(
    category_id: int,
    year: int,
    month: int,
    budget_update: AssetBudgetUpdate
):
    """특정 월의 예산 수정"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 예산 레코드가 있는지 확인 (없으면 생성)
        calculate_budget_for_month(cursor, category_id, year, month)
        
        if budget_update.budget_amount is not None:
            cursor.execute("""
                UPDATE asset_budgets
                SET budget_amount = ?, updated_at = CURRENT_TIMESTAMP
                WHERE category_id = ? AND year = ? AND month = ?
            """, (budget_update.budget_amount, category_id, year, month))
            
        cursor.execute("""
            SELECT id, category_id, year, month, budget_amount, rollover_amount, created_at, updated_at
            FROM asset_budgets
            WHERE category_id = ? AND year = ? AND month = ?
        """, (category_id, year, month))
        
        return dict(cursor.fetchone())

@router.put("/categories/{category_id}/default-budget", response_model=AssetCategory)
async def update_category_default_budget(
    category_id: int,
    default_budget: float = Query(..., description="기본 월 예산")
):
    """카테고리 기본 예산 수정"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE asset_categories
            SET default_budget = ?
            WHERE id = ?
        """, (default_budget, category_id))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Category not found")
            
        cursor.execute("""
            SELECT id, class_id, name, display_name, tier_id, description, 
                   is_active, sort_order, created_at, default_budget
            FROM asset_categories WHERE id = ?
        """, (category_id,))
        return dict(cursor.fetchone())
