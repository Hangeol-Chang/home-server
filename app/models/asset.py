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