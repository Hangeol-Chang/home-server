from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from datetime import date as date_type
from enum import Enum

# ===== Asset Classes (거래 분류) =====
class AssetClassBase(BaseModel):
    name: str = Field(..., description="분류명 (예: spend, earn, save)")
    display_name: str = Field(..., description="표시명")
    description: Optional[str] = None
    is_active: bool = True

class AssetClassCreate(AssetClassBase):
    pass

class AssetClass(AssetClassBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ===== Asset Categories (카테고리) =====
class AssetCategoryBase(BaseModel):
    class_id: int = Field(..., description="거래 분류 ID")
    name: str = Field(..., description="카테고리명")
    display_name: str = Field(..., description="표시명")
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class AssetCategoryCreate(AssetCategoryBase):
    pass

class AssetCategory(AssetCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ===== Asset Tiers (중요도/필수도) =====
class AssetTierBase(BaseModel):
    class_id: int = Field(..., description="거래 분류 ID")
    tier_level: int = Field(..., description="티어 레벨")
    name: str = Field(..., description="티어명")
    display_name: str = Field(..., description="표시명")
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class AssetTierCreate(AssetTierBase):
    pass

class AssetTier(AssetTierBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# ===== Assets (자산 거래) =====
class AssetTransactionBase(BaseModel):
    name: str = Field(..., description="거래명")
    cost: float = Field(..., gt=0, description="금액")
    class_id: int = Field(..., description="거래 분류 ID")
    category_id: int = Field(..., description="카테고리 ID")
    tier_id: int = Field(..., description="티어 ID")
    date: date_type = Field(default_factory=date_type.today, description="거래 날짜")
    description: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None, description="태그 목록")

class AssetTransactionCreate(AssetTransactionBase):
    pass

class AssetTransactionUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[float] = Field(None, gt=0)
    category_id: Optional[int] = None
    tier_id: Optional[int] = None
    date: Optional[date_type] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class AssetTransaction(AssetTransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ===== 조회용 응답 모델 (JOIN된 데이터) =====
class AssetTransactionDetail(BaseModel):
    id: int
    name: str
    cost: float
    date: date_type
    description: Optional[str]
    tags: Optional[List[str]]
    class_name: str
    class_display_name: str
    category_name: str
    category_display_name: str
    tier_level: int
    tier_name: str
    tier_display_name: str
    created_at: datetime
    updated_at: datetime

# ===== 통계 응답 모델 =====
class CategoryStatistics(BaseModel):
    category_id: int
    category_name: str
    category_display_name: str
    count: int
    total_cost: float

class TierStatistics(BaseModel):
    tier_id: int
    tier_level: int
    tier_name: str
    tier_display_name: str
    count: int
    total_cost: float

class PeriodSummary(BaseModel):
    class_name: str
    class_display_name: str
    total_count: int
    total_cost: float
    by_category: List[CategoryStatistics]
    by_tier: List[TierStatistics]

class MonthlyStatistics(BaseModel):
    year: int
    month: int
    spend_total: float
    earn_total: float
    save_total: float
    balance: float  # earn - spend - save

# ===== Period Comparison (기간별 비교) =====
class PeriodUnit(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"

class PeriodData(BaseModel):
    """단일 기간 데이터"""
    period_label: str = Field(..., description="기간 레이블 (예: 2025-11-04~11-10)")
    start_date: date_type
    end_date: date_type
    spend_total: float
    earn_total: float
    save_total: float
    balance: float
    transaction_count: int
    by_category: List[CategoryStatistics]
    top_transactions: List['AssetTransactionDetail'] = Field(default_factory=list, description="상위 거래 5건")

class PeriodComparison(BaseModel):
    """기간별 비교 통계"""
    unit: PeriodUnit = Field(..., description="비교 단위")
    periods: List[PeriodData] = Field(..., description="최대 4개 기간 데이터 (최신순)")
    
    # 평균/트렌드 정보
    avg_spend: float
    avg_earn: float
    avg_save: float
    spend_trend: float = Field(..., description="지출 증감률 (최근 기간 대비 이전 기간 평균)")
    earn_trend: float = Field(..., description="수익 증감률")

# ===== Tags (태그) =====
class AssetTagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="태그명")
    description: Optional[str] = None
    color: str = Field(default="#6366f1", description="태그 색상")
    is_active: bool = True

class AssetTagCreate(AssetTagBase):
    pass

class AssetTagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None

class AssetTag(AssetTagBase):
    id: int
    usage_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True