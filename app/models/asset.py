from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AssetType(str, Enum):
    HARDWARE = "hardware"
    SOFTWARE = "software"
    DIGITAL = "digital"
    DOCUMENT = "document"

class AssetStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"

class AssetBase(BaseModel):
    name: str
    description: Optional[str] = None
    asset_type: AssetType
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    location: Optional[str] = None
    status: AssetStatus = AssetStatus.ACTIVE

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    asset_type: Optional[AssetType] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[datetime] = None
    purchase_price: Optional[float] = None
    location: Optional[str] = None
    status: Optional[AssetStatus] = None

class Asset(AssetBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True